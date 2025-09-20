import logging
from typing import Tuple

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator,
    SignalGeneratorChannel,
    SignalGeneratorModulation,
)


class SiglentSDG2122X(SignalGenerator):
    """
    Class for Siglent SDG2122X
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
            max_power=30,
            min_power=-50,
            max_freq=120e6,
            min_freq=1e-6,
        )

        channel2 = SignalGeneratorChannel(
            channel_number=2,
            instrument=self,
            logger=logger,
            max_power=30,
            min_power=-50,
            max_freq=120e6,
            min_freq=1e-6,
        )

        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            channel_count=2,
            channels=[channel1, channel2],
            logger=logger,
            **kwargs,
        )

    def get_instrument_errors(self):
        return []  # Doesn't appear to be implemented in the device

    def get_channel_errors(self, channel_number: int) -> list[Tuple[int, str]]:
        return []  # Doesn't appear to be implemented in the device

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        self._write(f"C{channel_number}:OUTP {'ON' if enabled else 'OFF'}")

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        response = self._query(f"C{channel_number}:OUTP?")
        state = response.split("OUTP ")[1].split(",")[0]
        return state == "ON"

    def set_channel_power(self, channel_number: int, power: float):
        self._write(f"C{channel_number}:BSWV AMPDBM,{power}")

    def get_channel_power(self, channel_number: int) -> float:
        channel_status = self._query(f"C{channel_number}:BSWV?")
        try:
            return float(channel_status.split("AMPDBM,")[1].split("d")[0])
        except IndexError:
            # Asked for power in dBm into Hi-Z load
            self.logger.warning("Requested power reading when set to Hi-Z load")
            return -174

    def set_channel_freq(self, channel_number: int, freq: float):
        self._write(f"C{channel_number}:BSWV FRQ,{freq}")

    def get_channel_freq(self, channel_number: int) -> float:
        channel_status = self._query(f"C{channel_number}:BSWV?")
        freq = float(channel_status.split("FRQ,")[1].split("HZ")[0])
        return freq

    def set_channel_modulation(
        self, channel_number: int, modulation: SignalGeneratorModulation
    ):
        if modulation == SignalGeneratorModulation.NONE:
            self._write(f"C{channel_number}:BSWV WVTP SINE")
        else:
            raise NotImplementedError

    def get_channel_modulation(self, channel_number: int) -> SignalGeneratorModulation:
        channel_status = self._query(f"C{channel_number}:BSWV?")
        modulation = channel_status.split(",")[1]
        if modulation == "SINE":
            return SignalGeneratorModulation.NONE
        else:
            raise NotImplementedError

    def set_channel_load_impedance(self, channel_number: int, impedance: float):
        if impedance == float("inf"):
            self._write(f"C{channel_number}:OUTP LOAD,HZ")
        else:
            assert isinstance(impedance, int)
            self._write(f"C{channel_number}:OUTP LOAD,{impedance}")

    def get_channel_load_impedance(self, channel_number: int) -> float:
        response = self._query(f"C{channel_number}:OUTP?")
        impedance = response.split(",")[2]
        if impedance == "HZ":
            return float("inf")
        else:
            return float(impedance)

    def set_channel_vpp(self, channel_number: int, voltage: float):
        self._write(f"C{channel_number}:BSWV AMP,{voltage}")

    def get_channel_vpp(self, channel_number: int) -> float:
        channel_status = self._query(f"C{channel_number}:BSWV?")
        vpp = float(channel_status.split("AMP,")[1].split("V,AMP")[0])
        return vpp
