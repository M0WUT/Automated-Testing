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
        instrument: BaseInstrument,
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
        self.monitorProcess = Process(
            target=self.check_channel_errors, args=[os.getpid()], daemon=True
        )

    def _reserve(self, purpose: str):
        assert (
            self.reserved is False
        ), f"Requested channel is already reserved for {self.name}"
        oldName = self.name
        self.name = purpose
        self.reserved = True
        self.logger.debug(f"{oldName} assigned to {self.name}")
        return self

    def free(self):
        assert self.reserved, "Attempeted to free an already free channel"
        if self.monitorProcess.is_alive():
            self.monitorProcess.terminate()
            self.monitorProcess.join(2)
        oldName = self.name
        self.name = f"{self.instrument.name} - Channel {self.channel_number}"
        self.reserved = False
        self.logger.debug(f"{self.name} released from role as {oldName}")

    def check_channel_errors(self, pid: int):
        """
        Checks for channel specific errors, raises a signal to thread with Process
        ID pid in case of an error
        """
        self.logger.debug(f"Started error monitoring thread for {self.name}")
        while True:
            sleep(3)
            errorList = self.instrument.get_channel_errors(self.channel_number)
            if errorList:
                for errorCode, errorMessage in errorList:
                    self.logger.error(
                        f"{self.name} reporting error "
                        f"{errorCode} ({errorMessage}). Shutting down..."
                    )

                # Inform main thread
                os.kill(pid, signal.SIGUSR1)

    def set_output_enabled_state(self, enabled: bool = True):
        if enabled:
            assert not self.monitorProcess.is_alive() and self.reserved
            self.instrument.enable_channel_output(self.channel_number)
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.monitorProcess.start()
            self.logger.debug(f"{self.name} - Output Enabled")
        else:
            if self.monitorProcess.is_alive():
                self.monitorProcess.terminate()
                self.monitorProcess.join(2)
            self.instrument.disable_channel_output(self.channel_number)
            self.logger.debug(f"{self.name} - Output Disabled")

        if self.instrument.verify:
            assert self.get_output_enabled_state() == enabled

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
        channel_count: int,
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

        assert len(channels) == channel_count
        expected_channels = list(range(1, channel_count + 1))
        found_channels = [x.channel_number for x in channels]
        assert expected_channels == found_channels

        self.channels = channels
        self.channel_count = channel_count

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
        for x in self.channels:
            x.cleanup()
        super().cleanup()

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        raise NotImplementedError

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        raise NotImplementedError

    def enable_channel_output(self, channel_number: int):
        self.set_channel_output_enabled_state(channel_number, True)

    def disable_channel_output(self, channel_number: int):
        self.set_channel_output_enabled_state(channel_number, False)

    def validate_channel_number(self, number: int):
        assert number in list(range(1, self.channel_count + 1))

    def reserve_channel(self, channel_number: int, purpose: str) -> InstrumentChannel:
        self.validate_channel_number(channel_number)
        self.channels[channel_number - 1]._reserve(purpose)
        return self.channels[channel_number - 1]
