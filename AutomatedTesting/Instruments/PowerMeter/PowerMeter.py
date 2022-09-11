from logging import Logger

from AutomatedTesting.Instruments.EntireInstrument import EntireInstrument
from pyvisa import ResourceManager


class PowerMeter(EntireInstrument):
    """
    Pure virtual class for Signal Generators
    This should never be implemented directly
    The functions listed below should all be overwritten by the child
    class with the possible exception of enter and get_instrument_errors
    """

    def __init__(
        self,
        resourceManager: ResourceManager,
        visaAddress: str,
        instrumentName: str,
        expectedIdnResponse: str,
        verify: bool,
        logger: Logger,
        minFreq: float,
        maxFreq: float,
        **kwargs,
    ):
        super().__init__(
            resourceManager=resourceManager,
            visaAddress=visaAddress,
            instrumentName=instrumentName,
            expectedIdnResponse=expectedIdnResponse,
            verify=verify,
            logger=logger,
            **kwargs,
        )
        self.minFreq = minFreq
        self.maxFreq = maxFreq

    def __enter__(self):
        self.internal_zero()
        return self

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

    def set_freq(self, freq: float):
        """
        Informs power meter of frequency in to allow to
        compensate

        Args:
            freq (float): frequency in Hz
        Returns:
            None
        Raises:
            ValueError: if freq is outside range for this instrument
        """
        raise NotImplementedError  # pragma: no cover

    def get_freq(self) -> float:
        """
        Returns the frequency the instrument is set to in Hz

        Args:
            None
        Returns:
            float: frequency in Hz
        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def measure_power(self, freq: float) -> float:
        """
        Measures RF Power

        Args:
            freq (float): Frequency of measured signal
                (Used for power correction)
        Returns:
            float: Measured power in dBm
        Raises:
            ValueError: if freq is outside range for this instrument
        """
        raise NotImplementedError  # pragma: no cover
