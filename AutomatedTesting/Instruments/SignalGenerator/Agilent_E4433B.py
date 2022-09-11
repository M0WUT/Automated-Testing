import logging
from typing import List, Tuple

from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator,
    SignalGeneratorChannel,
    SignalGeneratorModulation,
)
from pyvisa import ResourceManager


class Agilent_E4433B(SignalGenerator):
    """
    Class for Agilent E4433B
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
            maxPower=13,
            minPower=-135,
            maxFreq=4e9,
            minFreq=250e3,
        )

        super().__init__(
            resourceManager=resourceManager,
            visaAddress=visaAddress,
            instrumentName=instrumentName,
            expectedIdnResponse=expectedIdnResponse,
            verify=verify,
            channelCount=1,
            channels=[channel1],
            logger=logger,
            **kwargs,
        )

    def __enter__(self):
        super().__enter__()
        selfTestResults = self._query("*TST?")
        assert selfTestResults == "+0"
        return self

    def get_channel_errors(self, channelNumber: int) -> list[Tuple[int, str]]:
        return []  # Doesn't have channel specific errors

    def set_channel_output_state(self, channelNumber: int, enabled: bool):
        # Single channel instrument so ignore channelNumber
        self._write(f"OUTP:STAT {'1' if enabled else '0'}")

    def get_channel_output_state(self, channelNumber: int) -> bool:
        # Single channel instrument so ignore channelNumber
        response = self._query("OUTP:STAT?")
        return response == "1"

    def set_channel_power(self, channelNumber: int, power: float):
        # Single channel instrument so ignore channelNumber
        self._write(f"POW {power}")

    def get_channel_power(self, channelNumber: int) -> float:
        # Single channel instrument so ignore channelNumber
        response = self._query("POW?")
        return float(response)

    def set_channel_freq(self, channelNumber: int, freq: float):
        # Single channel instrument so ignore channelNumber
        self._write(f"FREQ {freq}")

    def get_channel_freq(self, channelNumber: int) -> float:
        # Single channel instrument so ignore channelNumber
        response = self._query("FREQ?")
        return float(response)

    def set_channel_modulation(
        self, channelNumber: int, modulation: SignalGeneratorModulation
    ):
        # Single channel instrument so ignore channelNumber
        if modulation == SignalGeneratorModulation.NONE:
            self._write("OUTP:MOD:STAT 0")
        else:
            raise NotImplementedError

    def get_channel_modulation(
        self, channelNumber: int
    ) -> SignalGeneratorModulation:
        # Single channel instrument so ignore channelNumber
        response = self._query("OUTP:MOD:STAT?")
        if response == "0":
            return SignalGeneratorModulation.NONE
        else:
            raise NotImplementedError

    def set_channel_load_impedance(self, channelNumber: int, impedance: float):
        if impedance != 50:
            raise ValueError(
                f"{self.instrumentName} only supports 50R load impedance"
            )

    def get_channel_load_impedance(self, channelNumber: int) -> float:
        return 50
