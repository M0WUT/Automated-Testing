import logging

from AutomatedTesting.Instruments.TopLevel.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq
from numpy import poly1d, polyfit


class NoiseSource(BaseInstrument):
    def __init__(
        self, name: str, onVoltage: float, onCurrent: float, enr: dict[int, float]
    ):
        self.onVoltage = onVoltage
        self.onCurrent = onCurrent
        freqs = list(enr.keys())
        enrs = list(enr.values())
        enrCurve = polyfit(freqs, enrs, 10)
        self.evaluateEnr = poly1d(enrCurve)
        self.minFreq = min(freqs)
        self.maxFreq = max(freqs)
        self.name = name

    def evaluate_enr(self, freq: int) -> float:
        if not (self.minFreq <= freq <= self.maxFreq):
            logging.warning(
                f"Noise source ({self.name}) being used outside calibrated "
                f"frequency range of {readable_freq(self.minFreq)} - "
                f"{readable_freq(self.maxFreq)}"
            )
        return self.evaluateEnr(freq)

    def initialise(self, resourceManager, supervisor):
        # Override default function as this instrument cannot be
        # communicated with
        return None

    def check_instrument_errors(self, event):
        # Override default function as this instrument cannot be
        # communicated with
        pass

    def cleanup(self):
        # Override default function as this instrument cannot be
        # communicated with
        pass
