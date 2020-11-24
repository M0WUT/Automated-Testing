from AutomatedTesting.TopLevel.BaseInstrument import BaseInstrument
import logging


class SpectrumAnalyser(BaseInstrument):
    def __init__(
        self,
        address,
        id,
        name,
        minFreq,
        maxFreq,
        **kwargs
    ):
        """
        Pure virtual class for Spectrum Analyser
        This should never be implemented directly

        Args:
            address (str):
                PyVisa String e.g. "GPIB0::14::INSTR"
                with device location
            id (str): Expected string when ID is queried
            name (str): Identifying string for power supply
            minFreq (float): minimum operational frequency in Hz
            maxFreq (float): maximum operational frequency in Hz
            **kwargs: Passed to PyVisa Address field

        Returns:
            None

        Raises:
            None
        """
        super().__init__(address, id, name, **kwargs)
        self.corrections = None