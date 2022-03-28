import logging

from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)
from AutomatedTesting.Instruments.TopLevel.BaseInstrument import BaseInstrument


class Rigol_DSA815TG(SpectrumAnalyser):
    def __init__(
        self,
        address,
        name="Rigol DSA815-TG",
    ):
        super().__init__(
            address,
            id="Rigol Technologies,DSA815,DSA8A163551099,00.01.09.00.07",
            name=name,
            minFreq=9e3,
            maxFreq=1.5e9,
            minSweepPoints=None,  # Fixed at 601
            maxSweepPoints=None,
            minSpan=0,
            maxSpan=1.5e9,
            hasPreamp=True,
        )

    def set_preamp_state(self, enabled: bool) -> None:
        if enabled:
            self._write(":POW:GAIN 1")
            logging.debug(f"{self.name} enabled RF preamp")
        else:
            self._write(":POW:GAIN 0")
            logging.debug(f"{self.name} disabled RF preamp")

        if self.verify:
            assert self.read_preamp_state() == enabled

    def read_preamp_state(self) -> bool:
        return self._query(":POW:GAIN?") == "1"
