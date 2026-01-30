# Standard imports
import logging
import os
import signal
from threading import Event, Thread
from time import sleep
from typing import Optional, Sequence

# Third party imports
from pyvisa import ResourceManager

# Local imports
from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument


class InstrumentChannel:
    def __init__(
        self,
        channel_num: int,
        instrument: "MultichannelInstrument",
        logging_level: int,
    ):
        """
        Channel Number is 1-indexed because I'm human
        """
        self.instrument = instrument
        self.channel_num = channel_num
        self.logger: Optional[logging.Logger] = None
        self.logging_level = logging_level
        self.logger = logging.getLogger(
            f"{self.instrument.name} - Channel {self.channel_num}"
        )
        self.logger.setLevel(self.logging_level)

        self.reserved: bool = False
        self.purpose: Optional[str] = None
        self.monitor_process = Thread(
            target=self.check_channel_errors, args=[os.getpid()], daemon=True
        )
        self.terminate_monitor_process_flag = Event()

    def __enter__(self):
        assert self.reserved is False, "Requested channel is already reserved"
        self.reserved = True
        self.instrument.logger.info(
            f"{self.instrument.name} - Channel {self.channel_num} "
            f"reserved for {self.purpose}"
        )
        self.logger = logging.getLogger(self.purpose)
        self.logger.setLevel(self.logging_level)
        return self

    def __exit__(self, *args, **kwargs):
        self.shutdown()
        assert self.reserved, "Attempted to free an already free channel"
        if self.monitor_process.is_alive():
            self.terminate_monitor_process_flag.set()
            self.monitor_process.join(2)

        self.reserved = False
        self.logger.info("Released")
        self.logger = logging.getLogger(
            f"{self.instrument.name} - Channel {self.channel_num}"
        )
        self.logger.setLevel(self.logging_level)

    def check_channel_errors(self, pid: int):
        """
        Checks for channel specific errors, raises a signal to thread with Process
        ID pid in case of an error
        """
        self.logger.debug("Started error monitoring thread")
        while not self.terminate_monitor_process_flag.is_set():
            sleep(3)
            error_list = self.instrument.get_channel_errors(self.channel_num)
            if error_list:
                for error_code, error_message in error_list:
                    self.logger.error(
                        f"Error {error_code} ({error_message}). Shutting down..."
                    )
                # Inform main thread
                os.kill(pid, signal.SIGTERM)

    def shutdown(self) -> None:
        raise NotImplementedError  # pragma: no cover


class SourceChannel(InstrumentChannel):

    # def __exit__(self, *args, **kwargs):
    #     self.disable_output()
    #     super().__exit__(args, kwargs)

    def set_output_enabled_state(self, enabled: bool = True) -> None:
        if enabled:
            assert self.monitor_process.is_alive() is False and self.reserved
            self.instrument.enable_channel_output(self.channel_num)
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.monitor_process = Thread(
                target=self.check_channel_errors,
                args=[os.getpid()],
                daemon=True,
            )
            self.monitor_process.start()
            self.logger.info("Output Enabled")
        else:
            if self.monitor_process and self.monitor_process.is_alive():
                try:
                    self.terminate_monitor_process_flag.set()
                    self.monitor_process.join()
                except AttributeError:
                    pass
            self.instrument.disable_channel_output(self.channel_num)
            self.logger.info("Output Disabled")

        if self.instrument.verify:
            response = self.get_output_enabled_state()
            assert response == enabled

    def get_output_enabled_state(self) -> bool:
        return self.instrument.get_channel_output_enabled_state(self.channel_num)

    def enable_output(self) -> None:
        self.set_output_enabled_state(True)

    def disable_output(self) -> None:
        self.set_output_enabled_state(False)

    def shutdown(self) -> None:
        self.disable_output()


class MeasureChannel(InstrumentChannel):
    def __enter__(self):
        self.monitor_process = Thread(
            target=self.check_channel_errors, args=[os.getpid()], daemon=True
        )
        self.monitor_process.start()
        return self

    def shutdown(self) -> None:
        pass


class MultichannelInstrument(BaseInstrument):
    """
    Class for instruments that can be treated as having multiple independent
    function e.g. power supplies or signal generators. If an instrument can
    conceptually have multiple channels (even if a particular instance
    does not), then it should inherit from this class.
    """

    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logging_level: int,
        channels: Sequence[InstrumentChannel],
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logging_level=logging_level,
            **kwargs,
        )
        # Keep it as a list as, in rare cases,
        # this might not be continuous
        self.channels = channels

    def __enter__(self):
        super().__enter__()
        for x in self.channels:
            x.instrument = self
            if self.only_software_control and isinstance(x, SourceChannel):
                x.disable_output()
        return self

    def __exit__(self, *args, **kwargs):
        self.shutdown()

    def shutdown(self) -> None:
        if self.only_software_control:
            for x in self.channels:
                x.shutdown()
        super().shutdown()

    def validate_channel_num(self, channel_num: int) -> None:
        if channel_num not in [x.channel_num for x in self.channels]:
            raise ValueError(
                f"Invalid channel number {channel_num} requested for {self.name}"
            )

    def get_channel(self, channel_num: int) -> InstrumentChannel:
        self.validate_channel_num(channel_num)
        for channel in self.channels:
            if channel.channel_num == channel_num:
                return channel
        raise ValueError(f"Could not find channel {channel_num} in {self.name}")

    def reserve_channel(self, channel_num: int, purpose: str) -> InstrumentChannel:
        self.validate_channel_num(channel_num)
        for channel in self.channels:
            if channel.channel_num == channel_num:
                channel.purpose = purpose
                return channel
        raise ValueError(f"Could not find channel {channel_num} in {self.name}")

    def get_channel_errors(self, channel_num: int) -> list[tuple[int, str]]:
        return self._get_channel_errors(channel_num)

    def enable_channel_output(self, channel_num: int) -> None:
        self.set_channel_output_enabled_state(channel_num, True)

    def disable_channel_output(self, channel_num: int) -> None:
        self.set_channel_output_enabled_state(channel_num, False)

    #################################################
    # Functions that must be implemented per device #
    #################################################

    # Inherited from BaseInstrument
    def _set_remote_control(self) -> None:
        raise NotImplementedError

    def _set_local_control(self) -> None:
        raise NotImplementedError

    # Specific to this class
    def _get_channel_errors(self, channel_num: int) -> list[tuple[int, str]]:
        raise NotImplementedError

    def set_channel_output_enabled_state(self, channel_num: int, enabled: bool) -> None:
        raise NotImplementedError

    def get_channel_output_enabled_state(self, channel_num: int) -> bool:
        raise NotImplementedError
