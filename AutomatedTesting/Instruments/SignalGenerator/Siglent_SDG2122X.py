import logging
from typing import Tuple

from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator,
    SignalGeneratorChannel,
    SignalGeneratorModulation,
)
from pyvisa import ResourceManager


class Siglent_SDG2122X(SignalGenerator):
    """
    Class for Siglent SDG2122X
    """

    def __init__(
        self,
        resourceManager: ResourceManager,
        visaAddress: str,
        instrumentName: str,
        expectedIdnResponse: str,
        verify: bool,
        logger: logging.Logger,
        **kwargs,
    ):
        channel1 = SignalGeneratorChannel(
            channelNumber=1,
            instrument=self,
            logger=logger,
            maxPower=30,
            minPower=-50,
            maxFreq=120e6,
            minFreq=1e-6,
        )

        channel2 = SignalGeneratorChannel(
            channelNumber=2,
            instrument=self,
            logger=logger,
            maxPower=30,
            minPower=-50,
            maxFreq=120e6,
            minFreq=1e-6,
        )

        super().__init__(
            resourceManager=resourceManager,
            visaAddress=visaAddress,
            instrumentName=instrumentName,
            expectedIdnResponse=expectedIdnResponse,
            verify=verify,
            channelCount=2,
            channels=[channel1, channel2],
            logger=logger,
            **kwargs,
        )

    def get_instrument_errors(self):
        return []  # Doesn't appear to be implemented in the device

    def get_channel_errors(self, channelNumber: int) -> list[Tuple[int, str]]:
        return []  # Doesn't appear to be implemented in the device

    def set_channel_output_state(self, channelNumber: int, enabled: bool):
        self._write(f"C{channelNumber}:OUTP {'ON' if enabled else 'OFF'}")

    def get_channel_output_state(self, channelNumber: int) -> bool:
        response = self._query(f"C{channelNumber}:OUTP?")
        state = response.split("OUTP ")[1].split(",")[0]
        return state == "ON"

    def set_channel_power(self, channelNumber: int, power: float):
        self._write(f"C{channelNumber}:BSWV AMPDBM,{power}")

    def get_channel_power(self, channelNumber: int) -> float:
        channelStatus = self._query(f"C{channelNumber}:BSWV?")
        return float(channelStatus.split("AMPDBM,")[1].split("d")[0])

    def set_channel_freq(self, channelNumber: int, freq: float):
        self._write(f"C{channelNumber}:BSWV FRQ,{int(freq)}")

    def get_channel_freq(self, channelNumber: int) -> float:
        channelStatus = self._query(f"C{channelNumber}:BSWV?")
        freq = float(channelStatus.split("FRQ,")[1].split("HZ")[0])
        return freq

    def set_channel_modulation(
        self, channelNumber: int, modulation: SignalGeneratorModulation
    ):
        if modulation == SignalGeneratorModulation.NONE:
            self._write(f"C{channelNumber}:BSWV WVTP SINE")
        else:
            raise NotImplementedError

    def get_channel_modulation(
        self, channelNumber: int
    ) -> SignalGeneratorModulation:
        channelStatus = self._query(f"C{channelNumber}:BSWV?")
        modulation = channelStatus.split(",")[1]
        if modulation == "SINE":
            return SignalGeneratorModulation.NONE
        else:
            raise NotImplementedError

    def set_channel_load_impedance(self, channelNumber: int, impedance: float):
        if impedance == float("inf"):
            self._write(f"C{channelNumber}:OUTP LOAD,HZ")
        else:
            assert isinstance(impedance, int)
            self._write(f"C{channelNumber}:OUTP LOAD,{impedance}")

    def get_channel_load_impedance(self, channelNumber: int) -> float:
        response = self._query(f"C{channelNumber}:OUTP?")
        impedance = response.split(",")[2]
        if impedance == "HZ":
            return float("inf")
        else:
            return float(impedance)
