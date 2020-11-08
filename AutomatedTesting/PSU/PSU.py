from AutomatedTesting.TopLevel.MultiChannelInstrument import \
    MultiChannelInstrument, InstrumentChannel
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
        address,
        id,
        name,
        channelCount,
        channels,
        hasOVP,
        hasOCP,
        **kwargs
    ):

        # Check that we have a continous list of channels from
        # ID = 1 -> channelCount

        self.hasOVP = hasOVP
        self.hasOCP = hasOCP

        super().__init__(
            address,
            id,
            name,
            channelCount,
            channels,
            **kwargs
        )

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)
        for x in self.channels:
            x.enable_ovp(False)
            x.enable_ocp(False)
            x.enable_output(False)
            x.set_voltage(x.minVoltage)
            x.set_current(x.minCurrent)
        logging.info(f"{self.name} initialised")

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


class PowerSupplyChannel(InstrumentChannel):
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

        super().__init__(channelNumber)

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
        super()._free()
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
                f"{self.instrument.name}, Channel {self.channelNumber} "
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
                f"{self.instrument.name}, Channel {self.channelNumber} "
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
                        f"{self.instrument.name}, "
                        f"Channel {self.channelNumber}"
                        f" is current limiting on turn on"
                    )
                    assert False
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.name} set to {voltage}V"
            )
        else:
            raise ValueError(
                f"Requested voltage of {voltage}V outside limits for "
                f"Power supply {self.instrument.name}, "
                f"Channel {self.channelNumber}"
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
        logging.debug(
            f"{self.instrument.name}, "
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
            logging.debug(
                f"{self.instrument.name}, Channel {self.name} "
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
        logging.debug(
            f"{self.instrument.name}, Channel {self.name} "
            f"current measured as {x}A"
        )
        return x

    def enable_ovp(self, enabled=True):
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
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.name}: OVP Enabled"
            )
        else:
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.name}: OVP Disabled"
            )

    def disable_ovp(self):
        self.enable_ovp(False)

    def enable_ocp(self, enabled=True):
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
            logging.debug(
                f"{self.instrument.name}, f"
                f"Channel {self.name}: OCP Enabled"
            )
        else:
            logging.debug(
                f"{self.instrument.name}, "
                f"Channel {self.name}: OCP Disabled"
            )

    def disable_ocp(self):
        self.enable_ocp(False)
