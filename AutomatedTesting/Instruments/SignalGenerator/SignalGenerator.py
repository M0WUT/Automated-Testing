import logging
from enum import Enum, auto
from typing import List, Tuple

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.MultichannelInstrument import (
    InstrumentChannel, MultichannelInstrument)
from AutomatedTesting.Misc.UsefulFunctions import readable_freq


class SignalGeneratorModulation(Enum):
    NONE = auto()
    AM = auto()
    FM = auto()
    PM = auto()


class SignalGeneratorChannel(InstrumentChannel):
    def __init__(
        self,
        channel_number: int,
        instrument: BaseInstrument,
        logger: logging.Logger,
        max_power: float,  # in dBm
        min_power: float,
        max_freq: float,  # in Hz
        min_freq: float,
    ):
        super().__init__(channel_number, instrument, logger)

        # Save channel limits for power - Two limits as we
        # can set soft limits later
        if min_power > max_power:
            raise ValueError
        self.absolute_max_power = self.max_power = max_power
        self.absolute_min_power = self.min_power = min_power

        # Save channel limits for frequency
        if min_freq > max_freq:
            raise ValueError
        self.absolute_max_freq = self.max_freq = max_freq
        self.absolute_min_freq = self.min_freq = min_freq

    def set_soft_power_limits(self, min_power, max_power):
        """
        Allows tighter limits to be set on power than imposed by
        the instrument.

        Args:
            min_power (float): Minimum allowed power in dBm
            max_power (float): Maximum allowed power in dBm
        Returns:
            None
        Raises:
            ValueError: If requested limits are outside
                instrument limits
        """
        if (max_power > self.absolute_max_power) or (
            min_power < self.absolute_min_power
        ):
            self.logger.error(
                f"{self.name}, "
                f"requested power limits ({min_power}dBm - {max_power}dBm) "
                f" are outside channel limits "
                f"({self.absolute_min_power}dBm - {self.absolute_max_power}dBm)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.max_power = max_power
        self.min_power = min_power

    def set_freq_limits(self, min_freq: float, max_freq: float):
        """
        Allows tighter limits to be set on frequency than imposed by
        the instrument.

        Args:
            min_freq: Minimum allowed frequency in Hz
            max_freq: Maximum allowed frequency in Hz
        Returns:
            None
        Raises:
            ValueError: If requested limits are outside
                instrument limits
        """
        if (max_freq > self.absolute_max_freq) or (min_freq < self.absolute_min_freq):
            self.logger.error(
                f"{self.name}"
                f"requested frequency limits ({readable_freq(min_freq)} - "
                f"{readable_freq(max_freq)}) "
                f" are outside channel limits "
                f"({readable_freq(self.absolute_min_freq)} - "
                f"{readable_freq(self.absolute_max_freq)})"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.max_freq = max_freq
        self.min_freq = min_freq

    def set_power(self, power):
        """
        Sets channel output power

        Args:
            power (float): desired output power in dBm
        Returns:
            None
        Raises:
            ValueError: If requested power is outside channel
                max/min power
            AssertionError: If verified power != requested power
        """
        assert self.get_load_impedance() == 50
        if (power < self.min_power) or (power > self.max_power):
            raise ValueError(f"Unable to set {self.name} to {power}dBm")
        self.instrument.set_channel_power(self.channel_number, power)
        if self.instrument.verify:
            readbackPower = self.get_power()
            assert readbackPower == power
        self.logger.debug(f"{self.name} set to {power} dBm")

    def get_power(self) -> float:
        """
        Reads channel output power setpoint

        Args:
            None
        Returns:
            float: channel output power setpoint in dBm
        Raises:
            None
        """
        assert self.get_load_impedance() == 50
        return self.instrument.get_channel_power(self.channel_number)

    def set_freq(self, freq):
        """
        Sets channel output frequency

        Args:
            freq (float): desired output frequency in Hz
        Returns:
            None
        Raises:
            ValueError: If requested frequency is outside channel
                max/min frequency
            AssertionError: If verified frequency != requested frequency
        """
        if self.min_freq <= freq <= self.max_freq:
            self.instrument.set_channel_freq(self.channel_number, freq)
            if self.instrument.verify:
                readbackFreq = self.get_freq()
                assert readbackFreq == freq
            self.logger.debug(f"{self.name} set to {readable_freq(freq)}")

    def get_freq(self) -> float:
        """
        Reads channel output frequency

        Args:
            None
        Returns:
            float: channel output frequency in Hz
        Raises:
            None
        """
        return self.instrument.get_channel_freq(self.channel_number)

    def set_modulation(self, modulation: SignalGeneratorModulation):
        """
        Sets channel modulation type

        Args:
            modulation (SignalGeneratorModulation): modulation type
        Returns:
            None
        Raises:
            AssertionError: If verified modulation != requested modulation
        """
        self.instrument.set_channel_modulation(self.channel_number, modulation)
        if self.instrument.verify:
            assert self.get_modulation() == modulation
        self.logger.debug(f"{self.name} set modulation type to {modulation}")

    def get_modulation(self) -> SignalGeneratorModulation:
        """
        Returns channel's modulation type

        Args:
            None
        Returns:
            modulation (SignalGeneratorModulation): modulation type
        Raises:
            None
        """
        return self.instrument.get_channel_modulation(self.channel_number)

    def set_load_impedance(self, impedance: float):
        """
        Sets channel load impedance

        Args:
            impedance (float): load impedance in Ohms.
                Set to float('inf') for Hi-Z
        Returns:
            None
        Raises:
            AssertionError: If verified impedance != requested impedance
        """
        self.instrument.set_channel_load_impedance(self.channel_number, impedance)
        if self.instrument.verify:
            assert self.get_load_impedance() == impedance

    def get_load_impedance(self) -> float:
        """
        Returns channel load impedance in Ohms

        Args:
            None
        Returns:
            float: Load impedance in Ohms
        Raises:
            None
        """
        return self.instrument.get_channel_load_impedance(self.channel_number)

    def set_vpp(self, voltage: float):
        """
        Sets channel output amplitude in Vpp

        Args:
            voltage(float): peak-to-peak voltage in V
        Returns:
            None
        Raises:
            AssertionError: If verified voltage != requested voltage
        """
        assert self.get_load_impedance() == float("inf")
        self.instrument.set_channel_vpp(self.channel_number, voltage)
        if self.instrument.verify:
            assert self.get_vpp() == voltage

    def get_vpp(self) -> float:
        """
        Returns channel output amplitude in Vpp

        Args:
            None
        Returns:
            Output peak-to-peak voltage in V
        Raises:
            None
        """
        assert self.get_load_impedance() == float("inf")
        return self.instrument.get_channel_vpp(self.channel_number)


class SignalGenerator(MultichannelInstrument):
    """
    Pure virtual class for Signal Generators
    This should never be implemented directly
    The functions listed below should all be overwritten by the child
    class with the possible exception of enter and get_instrument_errors
    """

    def reserve_channel(
        self, channel_number: int, purpose: str
    ) -> SignalGeneratorChannel:
        return super().reserve_channel(channel_number, purpose)

    def __enter__(self):
        self.initialise()

    def initialise(self):
        super().initialise()
        if self.only_software_control:
            for x in self.channels:
                x.set_load_impedance(50)
                x.set_modulation(SignalGeneratorModulation.NONE)
                x.set_freq(x.min_freq)
                x.set_power(x.min_power)
        return self

    def get_instrument_errors(self) -> List[Tuple[int, str]]:
        return super().get_instrument_errors()

    def get_channel_errors(self, channel_number: int) -> list[Tuple[int, str]]:
        raise NotImplementedError  # pragma: no cover

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        raise NotImplementedError  # pragma: no cover

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        raise NotImplementedError  # pragma: no cover

    def set_channel_power(self, channel_number: int, power: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_power(self, channel_number: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def set_channel_frequency(self, channel_number: int, freq: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_freq(self, channel_number: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def set_channel_modulation(
        self, channel_number: int, modulation: SignalGeneratorModulation
    ):
        raise NotImplementedError  # pragma: no cover

    def get_channel_modulation(self, channel_number: int) -> SignalGeneratorModulation:
        raise NotImplementedError  # pragma: no cover

    def set_channel_load_impedance(self, channel_number: int, impedance: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_load_impedance(self, channel_number: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def set_channel_vpp(self, channel_number: int, voltage: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_vpp(self, channel_number) -> float:
        raise NotImplementedError  # pragma: no cover
