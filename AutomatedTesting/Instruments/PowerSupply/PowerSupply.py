# Standard imports
import logging

# Third party imports

# Local imports
from AutomatedTesting.Instruments.MultichannelInstrument import (
    InstrumentChannel,
    MultichannelInstrument,
    SourceChannel,
)
from AutomatedTesting.Misc.UsefulFunctions import prefixify


class PowerSupplyChannel(SourceChannel):
    """
    Object containing properties of PSU Output channel

    Args:
        psu (PowerSupply): Power Supply to which that channel belongs
        channel_num (int): Channel Number on PSU
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
            or channel_num > max channels for that PSU
    """

    instrument: "PowerSupply"

    def __init__(
        self,
        channel_num: int,
        instrument: "PowerSupply",
        logging_level: int,
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

        super().__init__(
            channel_num=channel_num, instrument=instrument, logging_level=logging_level
        )

    def __exit__(self, *args, **kwargs):
        """
        Removes the reservation on this power supply channel

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.max_voltage = self.absolute_max_voltage
        self.min_voltage = self.absolute_min_voltage
        self.max_current = self.absolute_max_current
        self.min_current = self.absolute_min_current
        super().__exit__(args, kwargs)

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
        if not (
            (self.absolute_min_voltage <= min_voltage <= self.absolute_max_voltage)
            and (self.absolute_min_voltage <= max_voltage <= self.absolute_max_voltage)
            and (max_voltage > min_voltage)
        ):
            self.logger.error(
                f"Requested voltage limits ({min_voltage}V - {max_voltage}V) "
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
        if not (
            (self.absolute_min_current <= min_current <= self.absolute_max_current)
            and (self.absolute_min_current <= max_current <= self.absolute_max_current)
            and (max_current > min_current)
        ):
            self.logger.error(
                f"Requested current limits ({min_current}V - {max_current}V) "
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
                f"Channel {self.channel_num}"
            )

        self.instrument.set_channel_voltage(self.channel_num, voltage)

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
        return self.instrument.get_channel_voltage(self.channel_num)

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

        x = self.instrument.measure_channel_voltage(self.channel_num)
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
                f"channel {self.channel_num}"
            )
        self.instrument.set_channel_current_limit(self.channel_num, current)

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
        return self.instrument.get_channel_current_limit(self.channel_num)

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
        x = self.instrument.measure_channel_current(self.channel_num)
        return x

    def get_output_enabled_state(self) -> bool:
        return self.instrument.get_channel_output_enabled_state(self.channel_num)


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

    channels: list[PowerSupplyChannel] = []

    def __enter__(self):
        super().__enter__()
        if self.only_software_control:
            for x in self.channels:
                # Channels are disabled in MultichannelInstrument init
                # x.disable_output()
                x.set_voltage(x.min_voltage)
                x.set_current_limit(x.min_current)
        return self

    def get_channel(self, channel_num: int) -> PowerSupplyChannel:
        return super().get_channel(channel_num)  # type:ignore

    def reserve_channel(self, channel_num: int, purpose: str) -> PowerSupplyChannel:
        return super().reserve_channel(channel_num, purpose)  # type: ignore

    def set_channel_voltage(self, channel_num: int, voltage: float) -> None:
        self.validate_channel_num(channel_num)
        self._set_channel_voltage(channel_num, voltage)
        if self.verify:
            assert self.get_channel_voltage(channel_num) == voltage
        self.get_channel(channel_num).logger.info(
            f"Set output voltage to {prefixify(voltage, 'V')}"
        )

    def get_channel_voltage(self, channel_num: int) -> float:
        self.validate_channel_num(channel_num)
        return self._get_channel_voltage(channel_num)

    def measure_channel_voltage(self, channel_num: int) -> float:
        self.validate_channel_num(channel_num)
        return self._measure_channel_voltage(channel_num)

    def set_channel_current_limit(self, channel_num: int, current: float) -> None:
        self.validate_channel_num(channel_num)
        self._set_channel_current_limit(channel_num, current)
        if self.verify:
            assert self.get_channel_current_limit(channel_num) == current
        self.get_channel(channel_num).logger.info(
            f"Set current limit to {prefixify(current, 'A')}"
        )

    def get_channel_current_limit(self, channel_num: int) -> float:
        self.validate_channel_num(channel_num)
        return self._get_channel_current_limit(channel_num)

    def measure_channel_current(self, channel_num: int) -> float:
        self.validate_channel_num(channel_num)
        return self._measure_channel_current(channel_num)

    def set_channel_output_enabled_state(self, channel_num: int, enabled: bool) -> None:
        self.validate_channel_num(channel_num)
        self._set_channel_output_enabled_state(channel_num, enabled)
        if self.verify:
            assert self.get_channel_output_enabled_state(channel_num) == enabled

    def get_channel_output_enabled_state(self, channel_num: int) -> bool:
        return self._get_channel_output_enabled_state(channel_num)

    ################################################################
    # Functions that must be implemented on a per-instrument basis #
    ################################################################
    # Inherited from BaseInstrument
    def _set_remote_control(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def _set_local_control(self) -> None:
        raise NotImplementedError  # pragma: no cover

    # Inherited from MultichannelInstrument
    def _get_channel_errors(self, channel_num: int) -> list[tuple[int, str]]:
        raise NotImplementedError  # pragma: no cover

    # Specific to this class
    def _set_channel_voltage(self, channel_num: int, voltage: float) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_channel_voltage(self, channel_num: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def _measure_channel_voltage(self, channel_num: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_channel_current_limit(self, channel_num: int, current: float) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_channel_current_limit(self, channel_num: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def _measure_channel_current(self, channel_num: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_channel_output_enabled_state(
        self, channel_num: int, enabled: bool
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_channel_output_enabled_state(self, channel_num: int) -> bool:
        raise NotImplementedError  # pragma: no cover
