from base_instrument import BaseInstrument


class PowerSupply(BaseInstrument):
    """
    Pure virtual class for Power Supplies
    This should never be implemented directly

    Args:
        resourceManager (pyvisa.ResourceManager):
            PyVisa Resource Manager.
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
        resourceManager,
        channelCount,
        channels,
        hasOVP,
        hasOCP,
        address,
        **kwargs
    ):
        # Check that we have a continous list of channels from
        # ID = 1 -> channelCount
        assert len(channels) == channelCount
        expectedChannels = list(range(1, channelCount + 1))
        foundChannels = [x.channelNumber for x in channels]
        assert expectedChannels == foundChannels

        self.channels = channels
        for x in self.channels:
            x.psu = self

        self.hasOVP = hasOVP
        self.hasOCP = hasOCP

        super().__init__(
            resourceManager,
            address,
            **kwargs
        )

    def set_channel_voltage(self, channelNumber, voltage):
        raise NotImplementedError

    def read_channel_voltage(self, channelNumber):
        raise NotImplementedError

    def set_channel_current(self, channelNumber, current):
        raise NotImplementedError

    def read_channel_current(self, channelNumber):
        raise NotImplementedError

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
            raise ValueError


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

        self.psu = None

        self.channelNumber = channelNumber

        if(maxVoltage < minVoltage):
            raise ValueError
        self.maxVoltage = maxVoltage
        self.minVoltage = minVoltage

        if(maxCurrent < minCurrent):
            raise ValueError
        self.maxCurrent = maxCurrent
        self.minCurrent = minCurrent

        self.ovpEnabled = False
        self.ocpEnabled = False
        self.outputEnabled = False

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
            self.psu.set_channel_voltage(self.channelNumber, voltage)
            assert(self.read_voltage() == voltage)
        else:
            raise ValueError

    def read_voltage(self):
        """
        Reads channel output voltage

        Args:
            None

        Returns:
            voltage (float): channel output voltage in Volts

        Raises:
            None
        """
        return self.psu.read_channel_voltage(self.channelNumber)

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
            self.psu.set_channel_current(self.channelNumber, current)
            x = self.read_current()
            assert(x == current)
        else:
            raise ValueError

    def read_current(self):
        """
        Reads channel output current

        Args:
            None

        Returns:
            current (float): channel output current in Amps

        Raises:
            None
        """
        return self.psu.read_channel_current(self.channelNumber)
