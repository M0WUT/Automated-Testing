from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser
import logging
from time import sleep


class Agilent_E4407B(SpectrumAnalyser):
    def __init__(self, address, name="Agilent E4407B"):
        super().__init__(
            address,
            id="Hewlett-Packard, E4407B, SG44210622, A.14.01",
            name=name,
            minFreq=9e3,
            maxFreq=26.5e9,
            timeout=500
        )

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)

    def read_instrument_errors(self):
        return []
        