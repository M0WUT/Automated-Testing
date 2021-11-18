from AutomatedTesting.TopLevel.BaseInstrument import BaseInstrument
from AutomatedTesting.TopLevel.ProcessWIthCleanStop import ProcessWithCleanStop
import logging
from time import sleep


class InstrumentChannel():
    def __init__(self, channelNumber):
        self.instrument = None
        self.reserved = False
        self.name = None
        self.errorThread = None
        self.error = False
        self.channelNumber = channelNumber

    def _free(self):
        assert self.reserved is True, \
            f"Attempted to free unused channel {self.channelNumber} " \
            f"on {self.instrument.name}"
        self.name = None
        self.reserved = False

    def get_name(self) -> str:
        if self.name:
            return str(self.channelNumber) + " (" + self.name + ")"
        else:
            return str(self.channelNumber)

    def check_for_errors(self, event):
        """
        Checks that channel with output enabled has no errors attached to it
        This is blocking so should only be called within a separate thread

        Args:
            event (multiprocessing.Event): Thread will terminate cleanly
                when this is set

        Returns:
            None

        Raises:
            None
        """
        while not event.is_set() and self.error is False:
            if self.instrument.check_channel_errors(self.channelNumber):
                self.error = True
                self.instrument.supervisor.handle_instrument_error()
        logging.debug(
            f"{self.instrument.name}, Channel {self.get_name()} "
            f"monitoring thread stopped"
        )

    def enable_output(self, enabled=True):
        """
        Enables / Disables channel output

        Args:
            enabled (bool): 0/False = Disable output, 1/True = Enable output

        Returns:
            None

        Raises:
            None
        """

        # If we're turning off the output, disable the monitoring thread
        # Otherwise there's a race condition in shutdown where the output
        # is disabled before the monitor thread finished and it thinks the
        # protection has tripped
        if(self.errorThread is not None):
            if(enabled):
                logging.error(
                    f"{self.instrument.name}, "
                    f"Channel {self.get_name()} "
                    f"attempted to enable while already enabled"
                )
                raise ValueError

            self.errorThread.terminate()
            self.errorThread = None

        self.instrument.enable_channel_output(self.channelNumber, enabled)
        self.outputEnabled = enabled

        if(enabled):
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.get_name()}: Output Enabled"
            )
            self.errorThread = ProcessWithCleanStop(
                target=self.check_for_errors
            )
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.errorThread.start()
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.get_name()}: Monitoring Thread started"
            )
        else:
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.get_name()}: Output Disabled"
            )

    def disable_output(self):
        self.enable_output(False)

    def cleanup(self):
        """
        Disables channel output, removes reservation on channel and
        shutdowns the monitoring thread so channel is ready for
        shutdown

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        if self.errorThread is not None:
            self.errorThread.terminate()
            self.errorThread = None
        self.enable_output(False)
        if(self.reserved):
            self._free()

        logging.debug(
            f"{self.instrument.name}, "
            f"Channel {self.get_name()} shutdown"
        )


class MultiChannelInstrument(BaseInstrument):
    def __init__(
            self,
            address,
            id,
            name,
            channelCount,
            channels,
            *args,
            **kwargs
    ):
        assert len(channels) == channelCount
        expectedChannels = list(range(1, channelCount + 1))
        foundChannels = [x.channelNumber for x in channels]
        assert expectedChannels == foundChannels

        self.channels = channels
        for x in self.channels:
            x.instrument = self
            x.reserved = False

            self.channelCount = channelCount
            super().__init__(address, id, name, *args, **kwargs)

    def validate_channel_number(self, channelNumber):
        """
        Throws Error if channelNumber is invalid for that device

        Args:
            channelNumber (int): proposed Channel Number

        Returns:
            None

        Raises:
            ValueError: If Channel Number is not valid
        """
        if(
            int(channelNumber) != channelNumber or
            channelNumber < 0 or
            channelNumber > self.channelCount
        ):
            raise ValueError(
                f"Invalid channel number {channelNumber} for "
                f"{self.name}"
            )

    def reserve_channel(self, channelNumber: int, name: str) -> InstrumentChannel:
        """
        Marks Instrument Channel as reserved and assigns a name to it

        Args:
            channelNumber (int): proposed Channel Number to reserve
            name (str): name to identify channel purpose

        Returns:
            InstrumentChannel: the reserved channel

        Raises:
            AssertionError: If requested channel is already reserved
        """
        self.validate_channel_number(channelNumber)
        assert self.channels[channelNumber - 1].reserved is False, \
            f"Channel {channelNumber} on Instrument {self.name} already " \
            f"reserved for \"{self.channels[channelNumber - 1].name}\""

        self.channels[channelNumber - 1].reserved = True
        self.channels[channelNumber - 1].name = f"{name}"
        logging.info(
            f"{self.name}, Channel {channelNumber} "
            f"reserved for \"{name}\""
        )
        return self.channels[channelNumber - 1]

    def cleanup(self):
        """
        Returns instrument to a safe state

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        for x in self.channels:
            x.cleanup()
        super().cleanup()

