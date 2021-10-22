from AutomatedTesting.TopLevel.BaseInstrument import BaseInstrument
from AutomatedTesting.TopLevel.PowerCorrections import PowerCorrections
import logging


class PowerMeter(BaseInstrument):
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
        Pure virtual class for RF Power Meters
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

    def reset(self):
        super().reset()
        self.external_zero()

    def initialise(self, resourceManager, supervisor):
        """
        Setups device and checks it can be communicated with
        Puts device in a reset state

        Args:
            resourceManager (PyVisa Resource Manager)
            supervisor (InstrumentSupervisor)

        Returns:
            None

        Raises:
            None
        """
        super().initialise(resourceManager, supervisor)
        logging.info(f"{self.name} initialised")

    def internal_zero(self):
        """
        Zeros power meter. Does not require external intervation
        i.e. removal of RF signal / disconnection of meter

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def external_zero(self):
        """
        Zeros power meter. Does require external intervation
        i.e. removal of RF signal / disconnection of meter

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_freq(self, freq):
        """
        Informs power meter of frequency in to allow to
        compensate

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def measure_power(self, freq):
        """
        Measures RF Power

        Args:
            freq (float): Frequency of measured signal
                (Used for power correction)

        Returns:
            float: Measured power in dBm

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def apply_corrections(self, corrections):
        assert isinstance(corrections, PowerCorrections)
        self.corrections = corrections

    def _correct_power(self, power, freq=None):
        if self.corrections is not None:
            assert freq is not None
            x = self.corrections.correctedPower(freq, power)
        else:
            x = power

        logging.debug(
            f"{self.name} measured power of {round(x, 1)}dBm"
        )
        return x
