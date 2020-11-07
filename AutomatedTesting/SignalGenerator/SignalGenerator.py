from AutomatedTesting.TopLevel.MultiChannelInstrument import \
    MultiChannelInstrument
from AutomatedTesting.TopLevel.ProcessWIthCleanStop import ProcessWithCleanStop
from time import sleep
import logging


class SignalGeneratorChannel():
    """
    Object containing properties of Signal Generator Output channel

    Args:
        sigGen (SignalGenerator): Power Supply to which that channel belongs
        channelNumber (int): Channel Number on Signal Generator
        maxPower (float): Maximum Output Power (in dBm)
        minPower (float): Minimum Output Power (in dBm)
        maxFreq (float): Maximum Carrier Frequency (in Hz)
        minFreq (float): Minimum Carrier Frequency (in Hz)

    Attributes:
        sigGen (SignalGenerator): Signal Generator to which
            this channel belongs
        reserved (bool): True if something has reserved control of this channel
        name (str): Name of the purpose that has this channel reserved
            None if self.reserved = False
        errorThread (Thread): When output is enabled, checks to ensure
            that no errors have occured

    Returns:
        None

    Raises:
        TypeError: If psu is not a SignalGenerator or None
        ValueError: If Max Power < Min Power, Max Freq < Min Freq
            or channelNumber > max channels for that Signal Generator
    """
    def __init__(
        self,
        channelNumber,
        maxPower,
        minPower,
        maxFreq,
        minFreq
    ):

        self.psu = None
        self.reserved = False
        self.name = str(channelNumber)
        self.errorThread = None
        self.error = False

        self.channelNumber = channelNumber

        # Absolute max / min are limits fixed by instrument
        # max / min include extra limits imposed externally
        if(maxPower < minPower):
            raise ValueError
        self.absoluteMaxPower = maxPower
        self.absoluteMinPower = minPower
        self.maxPower = self.absoluteMaxPower
        self.minPower = self.absoluteMinPower

        if(maxFreq < minFreq):
            raise ValueError
        self.absoluteMaxFreq = maxFreq
        self.absoluteMinFreq = minFreq
        self.maxFreq = self.absoluteMaxFreq
        self.minFreq = self.absoluteMinFreq

        self.ovpEnabled = False
        self.ocpEnabled = False
        self.outputEnabled = False

    def _free(self):
        """
        Removes the reservation on this power supply channel

        Args:
            None

        Returns:
            None

        Raises:
            AssertionError: If this channel is not already reserved
        """
        assert self.reserved is True, \
            f"Attempted to free unused channel {self.channelNumber} " \
            f"on {self.psu.name}"
        self.name = str(self.channelNumber)
        self.reserved = False
        self.maxPower = self.absoluteMaxPower
        self.minPower = self.absoluteMinPower
        self.maxFreq = self.absoluteMaxFreq
        self.minFreq = self.absoluteMinFreq

    def set_power_limits(self, minPower, maxPower):
        """
        Allows tighter limits to be set on power than imposed by
        the instrument.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: If requested limits are outside
                instrument limits
        """
        if(
            (maxPower > self.absoluteMaxPower) or
            (minPower < self.absoluteMinPower)
        ):
            logging.error(
                f"Signal Generator: {self.sigGen.name}, "
                f"Channel {self.channelNumber} "
                f"requested power limits ({minPower}dBm - {maxPower}dBm) "
                f" are outside channel limits "
                f"({self.absoluteMinPower}dBm - {self.absoluteMaxPower}dBm)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.maxPower = maxPower
        self.minPower = minPower

    def set_freq_limits(self, minFreq, maxFreq):
        """
        Allows tighter limits to be set on frequency than imposed by
        the instrument.

        Args:
            None

        Returns:
            None

        Raises:
            ValueError: If requested limits are outside
                instrument limits
        """
        if(
            (maxFreq > self.absoluteMaxFreq) or
            (minFreq < self.absoluteMinFreq)
        ):
            logging.error(
                f"Signal Generator: {self.sigGen.name}, "
                f"Channel {self.channelNumber} "
                f"requested frequency limits ({minFreq}Hz - {maxFreq}Hz) "
                f" are outside channel limits "
                f"({self.absoluteMinFreq}Hz - {self.absoluteMaxFreq}Hz)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.maxFreq = maxFreq
        self.minFreq = minFreq

    def enable_output(self, enabled):
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
                    f"Signal Generator: {self.sigGen.name}, "
                    f"Channel {self.name} "
                    f"attempted to enable while already enabled"
                )
                raise ValueError

            self.errorThread.terminate()
            self.errorThread = None

        self.sigGen.enable_channel_output(self.channelNumber, enabled)
        self.outputEnabled = enabled

        if(enabled):
            logging.info(
                f"Signal Generator: {self.sigGen.name}, "
                f"Channel {self.name}: Output Enabled"
            )
            self.errorThread = ProcessWithCleanStop(
                target=self.check_for_errors
            )
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.errorThread.start()
        else:
            logging.info(
                f"Signal Generator: {self.sigGen.name}, "
                f"Channel {self.name}: Output Disabled"
            )

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
            if self.psu.check_channel_errors(self.channelNumber):
                self.error = True
                self.psu.supervisor.handle_instrument_error()

    def cleanup(self):
        if self.errorThread is not None:
            self.errorThread.terminate()
            self.errorThread = None
        self.enable_output(False)
        if(self.reserved):
            self._free()

        logging.info(
            f"Signal Generator: {self.sigGen.name}, "
            f"Channel {self.name} shutdown"
        )


class SignalGenerator(MultiChannelInstrument):
    """
    Pure virtual class for Signal Generators
    This should never be implemented directly

    Args:
        name (str): Identifying string for signal generator
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location
        channelCount (int): Number of seperate output channels
        channels (List[SignalGeneratorChannel]): List of Signal Generator's
            output channels
        **kwargs: Passed to PyVisa Address field

    Returns:
        None

    Raises:
        TypeError: If resourceManager is not a valid PyVisa
            Resource Manager
        ValueError: If Resource Manager fails to open device
        AssertionError: If channel has ID greater than Signal Generator channel
            count
    """
    def __init__(
        self,
        id,
        name,
        channelCount,
        channels,
        address,
        **kwargs
    ):
        self.id = id
        self.name = name
        # Check that we have a continous list of channels from
        # ID = 1 -> channelCount
        assert len(channels) == channelCount
        expectedChannels = list(range(1, channelCount + 1))
        foundChannels = [x.channelNumber for x in channels]
        assert expectedChannels == foundChannels

        self.channels = channels
        for x in self.channels:
            x.sigGen = self
            x.reserved = False

        self.channelCount = channelCount
        self.supervisor = None

        super().__init__(
            address,
            **kwargs
        )

    def enable_channel_output(self, channelNumber, enabled):
        raise NotImplementedError  # pragma: no cover

    def check_channel_errors(self, channelNumber):
        raise NotImplementedError  # pragma: no cover
