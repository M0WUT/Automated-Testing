import logging

from AutomatedTesting.Instruments.MultichannelInstrument import (
    InstrumentChannel,
    MultichannelInstrument,
)


class PowerSupply(MultichannelInstrument):
    """
    Pure virtual class for Power Supplies
    This should never be implemented directly

    Args:
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location
        id (str): Expected string when ID is queried
        name (str): Identifying string for power supply
        channelCount (int): Number of seperate output channels
        channels (List[PowerSupplyChannel]): List of PSU's output channels
        **kwargs: Passed to PyVisa Address field

    Returns:
        None

    Raises:
        None
    """

    def initialise(self):
        super().initialise()
        if self.only_software_control:
            for x in self.channels:
                x.set_voltage(x.min_voltage)
                x.set_current_limit(x.min_current)

    def set_channel_voltage(self, channel_number, voltage):
        raise NotImplementedError  # pragma: no cover

    def get_channel_voltage(self, channel_number):
        raise NotImplementedError  # pragma: no cover

    def measure_channel_voltage(self, channel_number):
        raise NotImplementedError  # pragma: no cover

    def set_channel_current_limit(self, channel_number, current):
        raise NotImplementedError  # pragma: no cover

    def get_channel_current_limit(self, channel_number):
        raise NotImplementedError  # pragma: no cover

    def measure_channel_current(self, channel_number):
        raise NotImplementedError  # pragma: no cover

    def check_channel_errors(self, channel_number):
        raise NotImplementedError  # pragma: no cover

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        raise NotImplementedError

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        raise NotImplementedError


class PowerSupplyChannel(InstrumentChannel):
    """
    Object containing properties of PSU Output channel

    Args:
        psu (PowerSupply): Power Supply to which that channel belongs
        channel_number (int): Channel Number on PSU
        max_voltage (float): Maximum Output Voltage (in Volts)
        min_voltage (float): Minimum Output Voltage (in Volts)
        max_current (float): Maximum Output Current (in Amps)
        min_current (float): Minimum Output Voltage (in Amps)

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
            or channel_number > max channels for that PSU
    """

    def __init__(
        self,
        channel_number: int,
        instrument: MultichannelInstrument,
        logger: logging.Logger,
        min_voltage: float,
        max_voltage: float,
        min_current: float,
        max_current: float,
    ):
        # Absolute max / min are limits fixed by instrument
        # max / min include extra limits imposed externally
        if max_voltage < min_voltage:
            raise ValueError
        self.absolute_max_voltage = max_voltage
        self.absolute_min_voltage = min_voltage
        self.max_voltage = self.absolute_max_voltage
        self.min_voltage = self.absolute_min_voltage

        if max_current < min_current:
            raise ValueError
        self.absolute_max_current = max_current
        self.absolute_min_current = min_current
        self.max_current = self.absolute_max_current
        self.min_current = self.absolute_min_current

        self.overvoltage_protectionEnabled = False
        self.ocpEnabled = False
        self.outputEnabled = False

        super().__init__(
            channel_number=channel_number, instrument=instrument, logger=logger
        )

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
        self.max_voltage = self.absolute_max_voltage
        self.min_voltage = self.absolute_min_voltage
        self.max_current = self.absolute_max_current
        self.min_current = self.absolute_min_current

    def set_soft_voltage_limits(self, min_voltage, max_voltage):
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
        if (max_voltage > self.absolute_max_voltage) or (
            min_voltage < self.absolute_min_voltage
        ):
            self.logger.error(
                f"{self.instrument.name}, Channel {self.channel_number} "
                f"requested voltage limits ({min_voltage}V - {max_voltage}V) "
                f" are outside channel limits "
                f"({self.absolute_min_voltage}V - {self.absolute_max_voltage}V)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.max_voltage = max_voltage
        self.min_voltage = min_voltage

    def set_soft_current_limits(self, min_current, max_current):
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
        if (max_current > self.absolute_max_current) or (
            min_current < self.absolute_min_current
        ):
            self.logger.error(
                f"{self.instrument.name}, Channel {self.channel_number} "
                f"requested current limits ({min_current}V - {max_current}V) "
                f" are outside channel limits "
                f"({self.absolute_min_current}V - {self.absolute_max_current}V)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.max_current = max_current
        self.min_current = min_current

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

        if not (self.min_voltage <= voltage <= self.max_voltage):
            raise ValueError(
                f"Requested voltage of {voltage}V outside limits for "
                f"Power supply {self.instrument.name}, "
                f"Channel {self.channel_number}"
            )

        self.instrument.set_channel_voltage(self.channel_number, voltage)

        if self.instrument.verify:
            assert self.get_voltage() == voltage

        self.logger.debug(
            f"{self.instrument.name}, " f"Channel {self.name} set to {voltage}V"
        )

    def get_voltage(self):
        """
        Reads channel output voltage setpoint

        Args:
            None

        Returns:
            voltage (float): channel output voltage setpoint in Volts

        Raises:
            None
        """
        return self.instrument.get_channel_voltage(self.channel_number)

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

        x = self.instrument.measure_channel_voltage(self.channel_number)
        self.logger.debug(
            f"{self.instrument.name}, " f"Channel {self.name} measured as {x}V"
        )
        return x

    def set_current_limit(self, current):
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

        if not (self.min_current <= current <= self.max_current):
            raise ValueError(
                f"Requested current of {current}A outside limits for "
                f"Power supply {self.instrument.name}, "
                f"channel {self.channel_number}"
            )
        self.instrument.set_channel_current_limit(self.channel_number, current)
        if self.instrument.verify:
            assert self.get_current_limit() == current

    def get_current_limit(self):
        """
        Reads channel output current setpoint

        Args:
            None

        Returns:
            current (float): channel output current setpoint in Amps

        Raises:
            None
        """
        return self.instrument.get_channel_current_limit(self.channel_number)

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
        x = self.instrument.measure_channel_current(self.channel_number)
        return x

    def get_output_enabled_state(self) -> bool:
        return self.instrument.get_channel_output_enabled_state(self.channel_number)
