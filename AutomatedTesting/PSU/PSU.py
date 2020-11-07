from AutomatedTesting.TopLevel.MultiChannelInstrument import \
    MultiChannelInstrument
from AutomatedTesting.TopLevel.ProcessWIthCleanStop import ProcessWithCleanStop
from time import sleep
import logging


class PowerSupply(MultiChannelInstrument):
    """
    Pure virtual class for Power Supplies
    This should never be implemented directly

    Args:
        name (str): Identifying string for power supply
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location
        channelCount (int): Number of seperate output channels
        channels (List[PowerSupplyChannel]): List of PSU's output channels
        hasOVP (bool): Whether PSU supports Over Voltage Protection
        hasOCP (bool): Whether PSU supports Over Current Protection
        **kwargs: Passed to PyVisa Address field

    Returns:
        None

    Raises:
        TypeError: If resourceManager is not a valid PyVisa
            Resource Manager
        ValueError: If Resource Manager fails to open device
        AssertionError: If channel has ID greater than PSU channel
            count
    """
    def __init__(
        self,
        id,
        name,
        channelCount,
        channels,
        hasOVP,
        hasOCP,
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
            x.instrument = self
            x.reserved = False

        self.channelCount = channelCount
        self.hasOVP = hasOVP
        self.hasOCP = hasOCP
        self.supervisor = None

        super().__init__(
            address,
            **kwargs
        )

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)
        for x in self.channels:
            x.enable_ovp(False)
            x.enable_ocp(False)
            x.enable_output(False)
        logging.info(f"PSU: {self.name} initialised")

    def set_channel_voltage(self, channelNumber, voltage):
        raise NotImplementedError  # pragma: no cover

    def read_channel_voltage_setpoint(self, channelNumber):
        raise NotImplementedError  # pragma: no cover

    def measure_channel_voltage(self, channelNumber):
        raise NotImplementedError  # pragma: no cover

    def set_channel_current(self, channelNumber, current):
        raise NotImplementedError  # pragma: no cover

    def read_channel_current_setpoint(self, channelNumber):
        raise NotImplementedError  # pragma: no cover

    def measure_channel_current(self, channelNumber):
        raise NotImplementedError  # pragma: no cover

    def enable_channel_output(self, channelNumber, enabled):
        raise NotImplementedError  # pragma: no cover

    def check_channel_errors(self, channelNumber):
        raise NotImplementedError  # pragma: no cover

    def read_id(self):
        raise NotImplementedError  # pragma: no cover


class PowerSupplyChannel():
    """
    Object containing properties of PSU Output channel

    Args:
        psu (PowerSupply): Power Supply to which that channel belongs
        channelNumber (int): Channel Number on PSU
        maxVoltage (float): Maximum Output Voltage (in Volts)
        minVoltage (float): Minimum Output Voltage (in Volts)
        maxCurrent (float): Maximum Output Current (in Amps)
        minCurrent (float): Minimum Output Voltage (in Amps)

    Attributes:
        psu (PowerSupply): Power Supply to which this channel belongs
        reserved (bool): True if something has reserved control of this channel
        name (str): Name of the purpose that has this channel reserved
            None if self.reserved = False
        errorThread (Thread): When output is enabled, checks to ensure
            that no errors have occured

    Returns:
        None

    Raises:
        TypeError: If psu is not a PowerSupply or None
        ValueError: If Max Voltage < Min Voltage, Max Current < Min Current
            or channelNumber > max channels for that PSU
    """
    def __init__(
        self,
        channelNumber,
        maxVoltage,
        minVoltage,
        maxCurrent,
        minCurrent
    ):

        self.instrument = None
        self.reserved = False
        self.name = str(channelNumber)
        self.errorThread = None
        self.error = False

        self.channelNumber = channelNumber

        # Absolute max / min are limits fixed by instrument
        # max / min include extra limits imposed externally
        if(maxVoltage < minVoltage):
            raise ValueError
        self.absoluteMaxVoltage = maxVoltage
        self.absoluteMinVoltage = minVoltage
        self.maxVoltage = self.absoluteMaxVoltage
        self.minVoltage = self.absoluteMinVoltage

        if(maxCurrent < minCurrent):
            raise ValueError
        self.absoluteMaxCurrent = maxCurrent
        self.absoluteMinCurrent = minCurrent
        self.maxCurrent = self.absoluteMaxCurrent
        self.minCurrent = self.absoluteMinCurrent

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
            f"on {self.instrument.name}"
        self.name = str(self.channelNumber)
        self.reserved = False
        self.maxVoltage = self.absoluteMaxVoltage
        self.minVoltage = self.absoluteMinVoltage
        self.maxCurrent = self.absoluteMaxCurrent
        self.minCurrent = self.absoluteMinCurrent

    def set_voltage_limits(self, minVoltage, maxVoltage):
        """
        Allows tighter limits to be set on voltage than imposed by
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
            (maxVoltage > self.absoluteMaxVoltage) or
            (minVoltage < self.absoluteMinVoltage)
        ):
            logging.error(
                f"PSU: {self.instrument.name}, Channel {self.channelNumber} "
                f"requested voltage limits ({minVoltage}V - {maxVoltage}V) "
                f" are outside channel limits "
                f"({self.absoluteMinVoltage}V - {self.absoluteMaxVoltage}V)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.maxVoltage = maxVoltage
        self.minVoltage = minVoltage

    def set_current_limits(self, minCurrent, maxCurrent):
        """
        Allows tighter limits to be set on current than imposed by
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
            (maxCurrent > self.absoluteMaxCurrent) or
            (minCurrent < self.absoluteMinCurrent)
        ):
            logging.error(
                f"PSU: {self.instrument.name}, Channel {self.channelNumber} "
                f"requested current limits ({minCurrent}V - {maxCurrent}V) "
                f" are outside channel limits "
                f"({self.absoluteMinCurrent}V - {self.absoluteMaxCurrent}V)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.maxCurrent = maxCurrent
        self.minCurrent = minCurrent

    def set_voltage(self, voltage):
        """
        Sets channel output voltage

        Args:
            voltage (float): desired output voltage in Volts

        Returns:
            None

        Raises:
            ValueError: If requested voltage is outside channel
                max/min voltage
            AssertionError: If readback voltage != requested voltage
        """
        if(self.minVoltage <= voltage <= self.maxVoltage):
            self.instrument.set_channel_voltage(self.channelNumber, voltage)
            assert(self.read_voltage_setpoint() == voltage)
            if(self.outputEnabled):
                sleep(0.1)
                if self.measure_voltage() != voltage:
                    logging.error(
                        f"PSU: {self.instrument.name}, "
                        f"Channel {self.channelNumber}"
                        f" is current limiting on turn on"
                    )
                    assert False
            logging.info(
                f"PSU: {self.instrument.name}, "
                f"Channel {self.name} set to {voltage}V"
            )
        else:
            raise ValueError(
                f"Requested voltage of {voltage}V outside limits for "
                f"Power supply {self.instrument.name}, "
                f"channel {self.channelNumber}"
            )

    def read_voltage_setpoint(self):
        """
        Reads channel output voltage setpoint

        Args:
            None

        Returns:
            voltage (float): channel output voltage setpoint in Volts

        Raises:
            None
        """
        return self.instrument.read_channel_voltage_setpoint(
            self.channelNumber
        )

    def measure_voltage(self):
        """
        Measures channel output voltage

        Args:
            None

        Returns:
            voltage (float): channel output voltage in Volts

        Raises:
            None
        """

        x = self.instrument.measure_channel_voltage(self.channelNumber)
        logging.info(
            f"PSU: {self.instrument.name}, "
            f"Channel {self.name} measured as to {x}V"
        )
        return x

    def set_current(self, current):
        """
        Sets channel output current

        Args:
            current (float): desired output current in Amps

        Returns:
            None

        Raises:
            ValueError: If requested current is outside channel
                max/min current
            AssertionError: If readback current != requested current
        """
        if(self.minCurrent <= current <= self.maxCurrent):
            self.instrument.set_channel_current(self.channelNumber, current)
            x = self.read_current_setpoint()
            assert(x == current)
            logging.info(
                f"PSU: {self.instrument.name}, Channel {self.name} "
                f"current limit set to {x}A"
            )
        else:
            raise ValueError(
                f"Requested current of {current}A outside limits for "
                f"Power supply {self.instrument.name}, "
                f"channel {self.channelNumber}"
            )

    def read_current_setpoint(self):
        """
        Reads channel output current setpoint

        Args:
            None

        Returns:
            current (float): channel output current setpoint in Amps

        Raises:
            None
        """
        return self.instrument.read_channel_current_setpoint(
            self.channelNumber
        )

    def measure_current(self):
        """
        Measures channel output current

        Args:
            None

        Returns:
            current (float): channel output current in Amps

        Raises:
            None
        """
        x = self.instrument.measure_channel_current(self.channelNumber)
        logging.info(
            f"PSU: {self.instrument.name}, Channel {self.name} "
            f"current measured as {x}A"
        )
        return x

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
                    f"PSU: {self.instrument.name}, Channel {self.name} "
                    f"attempted to enable while already enabled"
                )
                raise ValueError

            self.errorThread.terminate()
            self.errorThread = None

        self.instrument.enable_channel_output(self.channelNumber, enabled)
        self.outputEnabled = enabled

        if(enabled):
            logging.info(
                f"PSU: {self.instrument.name}, "
                f"Channel {self.name}: Output Enabled"
            )
            self.errorThread = ProcessWithCleanStop(
                target=self.check_for_errors
            )
            sleep(0.5)  # Allow a small amount of time for inrush current
            self.errorThread.start()
        else:
            logging.info(
                f"PSU: {self.instrument.name}, "
                f"Channel {self.name}: Output Disabled"
            )

    def enable_ovp(self, enabled):
        """
        Enables / Disables channel Overvoltage proection

        Args:
            enabled (bool): 0/False = Disable output, 1/True = Enable output

        Returns:
            None

        Raises:
            None
        """
        self.instrument.enable_channel_ovp(self.channelNumber, enabled)
        self.ovpEnabled = enabled

        if enabled:
            logging.info(
                f"PSU: {self.instrument.name}, "
                f"Channel {self.name}: OVP Enabled"
            )
        else:
            logging.info(
                f"PSU: {self.instrument.name}, "
                f"Channel {self.name}: OVP Disabled"
            )

    def enable_ocp(self, enabled):
        """
        Enables / Disables channel Overcurrent proection

        Args:
            enabled (bool): 0/False = Disable output, 1/True = Enable output

        Returns:
            None

        Raises:
            None
        """
        self.instrument.enable_channel_ocp(self.channelNumber, enabled)
        self.ocpEnabled = enabled

        if enabled:
            logging.info(
                f"PSU: {self.instrument.name}, f"
                f"Channel {self.name}: OCP Enabled"
            )
        else:
            logging.info(
                f"PSU: {self.instrument.name}, "
                f"Channel {self.name}: OCP Disabled"
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
            if self.instrument.check_channel_errors(self.channelNumber):
                self.error = True
                self.instrument.supervisor.handle_instrument_error()

    def cleanup(self):
        if self.errorThread is not None:
            self.errorThread.terminate()
            self.errorThread = None
        self.enable_output(False)
        if(self.reserved):
            self._free()

        logging.info(
            f"PSU: {self.instrument.name}, Channel {self.name} shutdown"
        )
