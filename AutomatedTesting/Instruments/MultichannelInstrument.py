import logging
import os
import signal
from multiprocessing import Process
from time import sleep

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument


class InstrumentChannel:
    def __init__(
        self,
        channel_number: int,
        # Can't type hint as creates a circular reference
        instrument,  # : MultichannelInstrument,
        logger: logging.Logger,
    ):
        """
        Channel Number is 1-indexed because I'm human
        """
        # Channel objects get created before the instrument
        # they're assigned to so have to set as None and override later
        self.instrument = instrument
        self.name = None
        self.channel_number = channel_number
        self.logger = logger

        self.reserved = False

        self.name = None
        self.monitor_process = Process(
            target=self.check_channel_errors, args=[os.getpid()], daemon=True
        )

    def _reserve(self, purpose: str):
        assert (
            self.reserved is False
        ), f"Requested channel is already reserved for {self.name}"
        old_name = self.name
        self.name = purpose
        self.reserved = True
        self.logger.debug(f"{old_name} assigned to {self.name}")
        return self

    def free(self):
        assert self.reserved, "Attempeted to free an already free channel"
        if self.monitor_process.is_alive():
            self.monitor_process.terminate()
            self.monitor_process.join(2)
        old_name = self.name
        self.name = f"{self.instrument.name} - Channel {self.channel_number}"
        self.reserved = False
        self.logger.debug(f"{self.name} released from role as {old_name}")

    def check_channel_errors(self, pid: int):
        """
        Checks for channel specific errors, raises a signal to thread with Process
        ID pid in case of an error
        """
        self.logger.debug(f"Started error monitoring thread for {self.name}")
        while True:
            sleep(3)
            error_list = self.instrument.get_channel_errors(self.channel_number)
            if error_list:
                for error_code, error_message in error_list:
                    self.logger.error(
                        f"{self.name} reporting error "
                        f"{error_code} ({error_message}). Shutting down..."
                    )

                # Inform main thread
                os.kill(pid, signal.SIGTERM)

    def set_output_enabled_state(self, enabled: bool = True):
        if enabled:
            assert self.monitor_process.is_alive() is False and self.reserved
            self.instrument.enable_channel_output(self.channel_number)
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.monitor_process = Process(
                target=self.check_channel_errors, args=[os.getpid()], daemon=True
            )
            self.monitor_process.start()
            self.logger.debug(f"{self.name} - Output Enabled")
        else:
            if self.monitor_process and self.monitor_process.is_alive():
                try:
                    self.monitor_process.terminate()
                    self.monitor_process.join()
                except AttributeError:
                    pass
            self.instrument.disable_channel_output(self.channel_number)
            self.logger.debug(f"{self.name} - Output Disabled")

        if self.instrument.verify:
            response = self.get_output_enabled_state()
            assert response == enabled

    def get_output_enabled_state(self) -> bool:
        return self.instrument.get_channel_output_enabled_state(self.channel_number)

    def enable_output(self):
        self.set_output_enabled_state(True)

    def disable_output(self):
        self.set_output_enabled_state(False)

    def cleanup(self):
        self.disable_output()


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
        channels: list[InstrumentChannel],
        logger: logging.Logger,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logger=logger,
            **kwargs,
        )
        self.channel_count = len(channels)
        expected_channels = list(range(1, self.channel_count + 1))
        found_channels = [x.channel_number for x in channels]
        assert expected_channels == found_channels
        self.channels = channels

    def __enter__(self):
        self.initialise()

    def initialise(self):
        super().initialise()
        for x in self.channels:
            x.instrument = self
            x.name = f"{self.name} - Channel {x.channel_number}"
            if self.only_software_control:
                x.disable_output()
        return self

    def __exit__(self, *args, **kwargs):
        self.cleanup()

    def cleanup(self):
        if self.only_software_control:
            for x in self.channels:
                x.cleanup()
        super().cleanup()

    def validate_channel_number(self, channel_number: int):
        if not 1 <= channel_number <= self.channel_count:
            raise ValueError(
                f"Invalid channel number {channel_number} requested for {self.name}"
            )

    def reserve_channel(self, channel_number: int, purpose: str) -> InstrumentChannel:
        self.validate_channel_number(channel_number)
        self.channels[channel_number - 1]._reserve(purpose)
        return self.channels[channel_number - 1]
