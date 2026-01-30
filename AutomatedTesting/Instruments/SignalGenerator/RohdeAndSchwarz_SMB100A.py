# Standard imports
import logging

# Third party imports
from pyvisa import ResourceManager

# Local imports
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator,
    SignalGeneratorChannel,
    SignalGeneratorModulation,
)


class RohdeAndSchwarzSMB100A(SignalGenerator):
    """
    Class for Rohde & Schwarz SMB100A
    """

    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logging_level: int,
        **kwargs,
    ):
        self.name = name
        channel1 = SignalGeneratorChannel(
            channel_num=1,
            instrument=self,
            logging_level=logging_level,
            max_power=30,
            min_power=-120,  # Instrument can go down to -135dBm but not always
            max_freq=12.75e9,
            min_freq=100e3,
        )

        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            channels=[channel1],
            logging_level=logging_level,
            **kwargs,
        )

    def __enter__(self):
        self.initialise()

    def initialise(self):
        super().initialise()

    def get_channel_errors(self, channel_num: int) -> list[tuple[int, str]]:
        return []  # Doesn't have channel specific errors

    def set_channel_output_enabled_state(self, channel_num: int, enabled: bool):
        # Single channel instrument so ignore channel_num
        self._write(f"OUTP {'1' if enabled else '0'}")

    def get_channel_output_enabled_state(self, channel_num: int) -> bool:
        # Single channel instrument so ignore channel_num
        response = self._query("OUTP?")
        return response == "1"

    def set_channel_power(self, channel_num: int, power: float):
        # Single channel instrument so ignore channel_num
        self._write(f":POW {power}")

    def get_channel_power(self, channel_num: int) -> float:
        # Single channel instrument so ignore channel_num
        response = self._query(":POW?")
        return float(response)

    def set_channel_freq(self, channel_num: int, freq: float):
        # Single channel instrument so ignore channel_num
        self._write(f"FREQ {freq}")

    def get_channel_freq(self, channel_num: int) -> float:
        # Single channel instrument so ignore channel_num
        response = self._query("FREQ?")
        return float(response)

    def set_channel_modulation(
        self, channel_num: int, modulation: SignalGeneratorModulation
    ):
        # Single channel instrument so ignore channel_num
        if modulation == SignalGeneratorModulation.NONE:
            self._write("MOD:STAT 0")
        else:
            raise NotImplementedError

    def get_channel_modulation(self, channel_num: int) -> SignalGeneratorModulation:
        # Single channel instrument so ignore channel_num
        response = self._query("MOD:STAT?")
        if response == "0":
            return SignalGeneratorModulation.NONE
        else:
            raise NotImplementedError

    def set_channel_load_impedance(self, channel_num: int, impedance: float):
        if impedance != 50:
            raise ValueError(f"{self.name} only supports 50R load impedance")

    def get_channel_load_impedance(self, channel_num: int) -> float:
        return 50
