import logging
import os
import signal
from multiprocessing import Process
from time import sleep

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from pyvisa import ResourceManager


class InstrumentChannel:
    def __init__(
        self,
        channelNumber: int,
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
        self.channelNumber = channelNumber
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
        oldName = self.name
        self.name = (
            f"{self.instrument.instrumentName} - Channel {self.channelNumber}"
        )
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
            errorList = self.instrument.get_channel_errors(self.channelNumber)
            if errorList:
                for errorCode, errorMessage in errorList:
                    self.logger.error(
                        f"{self.name} reporting error "
                        f"{errorCode} ({errorMessage}). Shutting down..."
                    )

                # Inform main thread
                os.kill(pid, signal.SIGUSR1)

    def set_output_state(self, enabled: bool = True):
        if enabled:
            assert not self.monitorProcess.is_alive() and self.reserved
            self.instrument.enable_channel_output(self.channelNumber)
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.monitorProcess.start()
            self.logger.debug(f"{self.name} - Output Enabled")
        else:
            if self.monitorProcess.is_alive():
                self.monitorProcess.terminate()
                self.monitorProcess.join(2)
            self.instrument.disable_channel_output(self.channelNumber)
            self.logger.debug(f"{self.name} - Output Disabled")

        if self.instrument.verify:
            assert self.get_output_state() == enabled

    def get_output_state(self) -> bool:
        return self.instrument.get_channel_output_state(self.channelNumber)

    def enable_output(self):
        self.set_output_state(True)

    def disable_output(self):
        self.set_output_state(False)

    def shutdown(self):
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
        resourceManager: ResourceManager,
        visaAddress: str,
        instrumentName: str,
        expectedIdnResponse: str,
        verify: bool,
        channelCount: int,
        channels: list[InstrumentChannel],
        logger: logging.Logger,
        **kwargs,
    ):
        super().__init__(
            resourceManager=resourceManager,
            visaAddress=visaAddress,
            instrumentName=instrumentName,
            expectedIdnResponse=expectedIdnResponse,
            verify=verify,
            logger=logger,
            **kwargs,
        )

        assert len(channels) == channelCount
        expectedChannels = list(range(1, channelCount + 1))
        foundChannels = [x.channelNumber for x in channels]
        assert expectedChannels == foundChannels

        self.channels = channels
        self.channelCount = channelCount

    def __enter__(self):
        super().__enter__()
        for x in self.channels:
            x.instrument = self
            x.name = f"{self.instrumentName} - Channel {x.channelNumber}"
            x.disable_output()
        return self

    def __exit__(self, *args, **kwargs):
        for x in self.channels:
            x.shutdown()
        super().__exit__()

    def set_channel_output_state(self, channelNumber: int, enabled: bool):
        raise NotImplementedError

    def enable_channel_output(self, channelNumber: int):
        self.set_channel_output_state(channelNumber, True)

    def disable_channel_output(self, channelNumber: int):
        self.set_channel_output_state(channelNumber, False)

    def validate_channel_number(self, number: int):
        assert number in list(range(1, self.channelCount + 1))

    def reserve_channel(
        self, channelNumber: int, purpose: str
    ) -> InstrumentChannel:
        self.validate_channel_number(channelNumber)
        self.channels[channelNumber - 1]._reserve(purpose)
        return self.channels[channelNumber - 1]
