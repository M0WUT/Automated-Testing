import logging

from AutomatedTesting.Instruments.TopLevel.BaseInstrument import BaseInstrument


class SpectrumAnalyser(BaseInstrument):
    def __init__(self, address, id, name, minFreq, maxFreq, **kwargs):
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

    def initialise(self, *args, **kwargs):
        super().initialise(*args, **kwargs)
        logging.info(f"{self.name} initialised")

    def set_centre_freq(self, freq):
        """
        Sets centre frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_start_freq(self, freq):
        """
        Sets start frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_stop_freq(self, freq):
        """
        Sets stop frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_span(self, freq):
        """
        Sets x axis span

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_rbw(self, rbw):
        """
        Sets Resolution Bandwidth

        Args:
           rbw (float): RBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_vbw(self, vbw):
        """
        Sets Video Bandwidth

        Args:
           vbw (float): VBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_sweep_points(self, numPoints):
        """
        Sets Number of Points in sweep

        Args:
           vbw (float): VBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_sweep_time(self, sweepTime):
        """
        Sets Number of Points in sweep

        Args:
           sweepTime (float): sweep time in ms, or "auto"

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

    def set_ref_level(self, power):
        """
        Sets amplitude reference

        Args:
            power (float): Reference Level in dBm

        Returns:
            float: Measured power in dBm

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover
