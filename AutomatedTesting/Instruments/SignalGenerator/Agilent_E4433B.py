import logging
from typing import List, Tuple

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator,
    SignalGeneratorChannel,
    SignalGeneratorModulation,
)


class Agilent_E4433B(SignalGenerator):
    """
    Class for Agilent E4433B
    """

    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: logging.Logger,
        **kwargs,
    ):
        channel1 = SignalGeneratorChannel(
            channel_number=1,
            instrument=self,
            logger=logger,
            max_power=13,
            min_power=-135,
            max_freq=4e9,
            min_freq=250e3,
        )

        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            channel_count=1,
            channels=[channel1],
            logger=logger,
            **kwargs,
        )

    def __enter__(self):
        self.initialise()

    def initialise(self):
        super().initialise()
        test_result = self._query("*TST?")
        assert test_result == "+0", test_result
        return self

    def get_channel_errors(self, channel_number: int) -> list[Tuple[int, str]]:
        return []  # Doesn't have channel specific errors

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        # Single channel instrument so ignore channel_number
        self._write(f"OUTP:STAT {'1' if enabled else '0'}")

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        # Single channel instrument so ignore channel_number
        response = self._query("OUTP:STAT?")
        return response == "1"

    def set_channel_power(self, channel_number: int, power: float):
        # Single channel instrument so ignore channel_number
        self._write(f"POW {power}")

    def get_channel_power(self, channel_number: int) -> float:
        # Single channel instrument so ignore channel_number
        response = self._query("POW?")
        return float(response)

    def set_channel_freq(self, channel_number: int, freq: float):
        # Single channel instrument so ignore channel_number
        self._write(f"FREQ {freq}")

    def get_channel_freq(self, channel_number: int) -> float:
        # Single channel instrument so ignore channel_number
        response = self._query("FREQ?")
        return float(response)

    def set_channel_modulation(
        self, channel_number: int, modulation: SignalGeneratorModulation
    ):
        # Single channel instrument so ignore channel_number
        if modulation == SignalGeneratorModulation.NONE:
            self._write("OUTP:MOD:STAT 0")
        else:
            raise NotImplementedError

    def get_channel_modulation(self, channel_number: int) -> SignalGeneratorModulation:
        # Single channel instrument so ignore channel_number
        response = self._query("OUTP:MOD:STAT?")
        if response == "0":
            return SignalGeneratorModulation.NONE
        else:
            raise NotImplementedError

    def set_channel_load_impedance(self, channel_number: int, impedance: float):
        if impedance != 50:
            raise ValueError(f"{self.name} only supports 50R load impedance")

    def get_channel_load_impedance(self, channel_number: int) -> float:
        return 50
