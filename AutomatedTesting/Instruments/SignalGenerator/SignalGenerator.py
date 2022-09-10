import logging
from enum import Enum, auto
from typing import Tuple

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.MultichannelInstrument import (
    InstrumentChannel,
    MultichannelInstrument,
)
from AutomatedTesting.UsefulFunctions import readable_freq


class SignalGeneratorModulation(Enum):
    NONE = auto()
    AM = auto()
    FM = auto()
    PM = auto()


class SignalGeneratorChannel(InstrumentChannel):
    def __init__(
        self,
        channelNumber: int,
        instrument: BaseInstrument,
        logger: logging.Logger,
        maxPower: float,  # in dBm
        minPower: float,
        maxFreq: float,  # in Hz
        minFreq: float,
    ):
        super().__init__(channelNumber, instrument, logger)

        # Save channel limits for power - Two limits as we
        # can set soft limits later
        if minPower > maxPower:
            raise ValueError
        self.absoluteMaxPower = self.maxPower = maxPower
        self.absoluteMinPower = self.minPower = minPower

        # Save channel limits for frequency
        if minFreq > maxFreq:
            raise ValueError
        self.absoluteMaxFreq = self.maxFreq = maxFreq
        self.absoluteMinFreq = self.minFreq = minFreq

    def set_soft_power_limits(self, minPower, maxPower):
        """
        Allows tighter limits to be set on power than imposed by
        the instrument.

        Args:
            minPower (float): Minimum allowed power in dBm
            maxPower (float): Maximum allowed power in dBm
        Returns:
            None
        Raises:
            ValueError: If requested limits are outside
                instrument limits
        """
        if (maxPower > self.absoluteMaxPower) or (
            minPower < self.absoluteMinPower
        ):
            self.logger.error(
                f"{self.name}, "
                f"requested power limits ({minPower}dBm - {maxPower}dBm) "
                f" are outside channel limits "
                f"({self.absoluteMinPower}dBm - {self.absoluteMaxPower}dBm)"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.maxPower = maxPower
        self.minPower = minPower

    def set_freq_limits(self, minFreq: float, maxFreq: float):
        """
        Allows tighter limits to be set on frequency than imposed by
        the instrument.

        Args:
            minFreq: Minimum allowed frequency in Hz
            maxFreq: Maximum allowed frequency in Hz
        Returns:
            None
        Raises:
            ValueError: If requested limits are outside
                instrument limits
        """
        if (maxFreq > self.absoluteMaxFreq) or (minFreq < self.absoluteMinFreq):
            self.logger.error(
                f"{self.name}"
                f"requested frequency limits ({readable_freq(minFreq)} - "
                f"{readable_freq(maxFreq)}) "
                f" are outside channel limits "
                f"({readable_freq(self.absoluteMinFreq)} - "
                f"{readable_freq(self.absoluteMaxFreq)})"
            )
            raise ValueError

        # We already know that requested limits are harsher / equal
        # to instrument limits so just use those
        self.maxFreq = maxFreq
        self.minFreq = minFreq

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
        if (power < self.minPower) or (power > self.maxPower):
            raise ValueError(f"Unable to set {self.name} to {power}dBm")
        self.instrument.set_channel_power(self.channelNumber, power)
        if self.instrument.verify:
            assert self.get_power() == power
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
        return self.instrument.get_channel_power(self.channelNumber)

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
        if self.minFreq <= freq <= self.maxFreq:
            self.instrument.set_channel_freq(self.channelNumber, freq)
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
        return self.instrument.get_channel_freq(self.channelNumber)

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
        self.instrument.set_channel_modulation(self.channelNumber, modulation)
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
        return self.instrument.get_channel_modulation(self.channelNumber)

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
        self.instrument.set_channel_load_impedance(
            self.channelNumber, impedance
        )
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
        return self.instrument.get_channel_load_impedance(self.channelNumber)


class SignalGenerator(MultichannelInstrument):
    """
    Pure virtual class for Signal Generators
    This should never be implemented directly
    """

    def __enter__(self):
        super().__enter__()
        for x in self.channels:
            x.set_load_impedance(50)
            x.set_modulation(SignalGeneratorModulation.NONE)
            x.set_freq(x.minFreq)
            x.set_power(x.minPower)
        return self

    def get_channel_errors(self, channelNumber: int) -> list[Tuple[int, str]]:
        raise NotImplementedError  # pragma: no cover

    def set_channel_power(self, channelNumber: int, power: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_power(self, channelNumber: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def set_channel_frequency(self, channelNumber: int, freq: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_freq(self, channelNumber: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def set_channel_modulation(
        self, channelNumber: int, modulation: SignalGeneratorModulation
    ):
        raise NotImplementedError  # pragma: no cover

    def get_channel_modulation(
        self, channelNumber: int
    ) -> SignalGeneratorModulation:
        raise NotImplementedError  # pragma: no cover

    def set_channel_load_impedance(self, channelNumber: int, impedance: float):
        raise NotImplementedError  # pragma: no cover

    def get_channel_load_impedance(self, channelNumber: int) -> float:
        raise NotImplementedError  # pragma: no cover
