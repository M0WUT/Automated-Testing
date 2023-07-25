from logging import Logger

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.EntireInstrument import EntireInstrument


class PowerMeter(EntireInstrument):
    """
    Pure virtual class for Signal Generators
    This should never be implemented directly
    The functions listed below should all be overwritten by the child
    class with the possible exception of enter and get_instrument_errors
    """

    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: Logger,
        min_freq: float,
        max_freq: float,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logger=logger,
            **kwargs,
        )
        self.min_freq = min_freq
        self.max_freq = max_freq

    def __enter__(self):
        super().__enter__()
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
