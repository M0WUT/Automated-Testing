import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional

from AutomatedTesting.Instruments.TopLevel.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq


class DetectorMode(Enum):
    RMS = auto()
    VIDEO = auto()


class SpectrumAnalyser(BaseInstrument):
    def __init__(
        self,
        address: str,
        id: str,
        name: str,
        minFreq: int,
        maxFreq: int,
        minSweepPoints: Optional[int],
        maxSweepPoints: Optional[int],
        minSpan: int,
        maxSpan: int,
        hasPreamp: bool,
        **kwargs,
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
            **kwargs: ed to PyVisa Address field

        Returns:
            None

        Raises:
            None
        """
        self.minFreq = minFreq
        self.maxFreq = maxFreq
        self.minSweepPoints = minSweepPoints
        self.maxSweepPoints = maxSweepPoints
        self.minSpan = minSpan
        self.maxSpan = maxSpan
        self.hasPreamp = hasPreamp
        super().__init__(address, id, name, **kwargs)

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
            ValueError: If requested freq is outside instrument limits
        """
        if not (self.minFreq <= freq <= self.maxFreq):
            raise ValueError
        self._write(f"FREQ:CENT {readable_freq(freq)}")
        if self.verify:
            assert self.read_centre_freq() == freq
        logging.debug(f"{self.name} set centre frequency to {readable_freq(freq)}")

    def read_centre_freq(self) -> float:
        """
        Returns centre frequency

        Args:
           None

        Returns:
            float: centre freq in Hz

        Raises:
            None
        """
        return float(self._query("FREQ:CENT?"))

    def set_start_freq(self, freq):
        """
        Sets start frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            ValueError: If requested freq is outside instrument limits
        """
        if not (self.minFreq <= freq <= self.maxFreq):
            raise ValueError
        self._write(f"FREQ:STAR {readable_freq(freq)}")
        if self.verify:
            assert self.read_start_freq() == freq
        logging.debug(f"{self.name} set start frequency to {readable_freq(freq)}")

    def read_start_freq(self) -> int:
        """
        Returns start frequency

        Args:
           None

        Returns:
            float: Start frequency in Hz

        Raises:
            None
        """
        return float(self._query("FREQ:STAR?"))

    def set_stop_freq(self, freq):
        """
        Sets stop frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            ValueError: If requested freq is outside instrument limits
        """
        if not (self.minFreq <= freq <= self.maxFreq):
            raise ValueError
        self._write(f"FREQ:STOP {readable_freq(freq)}")
        if self.verify:
            assert self.read_stop_freq() == freq
        logging.debug(f"{self.name} set stop frequency to {readable_freq(freq)}")

    def read_stop_freq(self) -> float:
        """
        Returns stop frequency

        Args:
           None

        Returns:
            float: Stop frequency in Hz

        Raises:
            None
        """
        return float(self._query("FREQ:STOP?"))

    def set_span(self, span):
        """
        Sets x axis span

        Args:
           span (float): Span in Hz

        Returns:
            None

        Raises:
            ValueError: If frequested span is not allowed
        """
        if not (self.minSpan <= span <= self.maxSpan or span == 0):
            raise ValueError
        self._write(f"FREQ:SPAN {readable_freq(span)}")
        if self.verify:
            assert self.read_span() == span
        logging.debug(f"{self.name} set span to {readable_freq(span)}")

    def read_span(self) -> int:
        """
        Returns x-axis span

        Args:
           span (float): Span in Hz

        Returns:
            None

        Raises:
            None
        """
        return float(self._query("FREQ:SPAN?"))

    def set_sweep_points(self, numPoints):
        """
        Sets Number of Points in sweep

        Args:
           numPoints (int): Number of sweep points

        Returns:
            None

        Raises:
            None
        """
        assert self.minSweepPoints
        if not (self.minSweepPoints <= numPoints <= self.maxSweepPoints):
            raise ValueError
        self._write(f":SWE:POIN {numPoints}")
        if self.verify:
            assert self.read_sweep_points() == numPoints
        logging.debug(f"{self.name} set number of points to {numPoints}")

    def read_sweep_points(self) -> int:
        assert self.minSweepPoints
        return int(self._query(":SWE:POIN?"))

    def set_sweep_time(self, sweepTime):
        """
        Sets Sweep time in ms

        Args:
           sweepTime (float): sweep time in ms, or "auto"

        Returns:
            None

        Raises:
            None
        """
        if sweepTime == "auto":
            self._write(":SWE:TIME:AUTO ON")
        else:
            self._write(f":SWE:TIME {sweepTime}ms")
            if self.read_sweep_time() != sweepTime:
                raise ValueError
            logging.debug(f"{self.name} set sweep time to {sweepTime}ms")

    def read_sweep_time(self) -> float:
        """
        Returns sweep time in ms
        """
        return 1000.0 * float(self._query(":SWE:TIME?"))

    def enable_preamp(self) -> None:
        """
        Enables the RF preamp

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        assert self.hasPreamp
        self.set_preamp_state(True)
        if self.verify:
            assert self.read_preamp_state()

    def disable_preamp(self) -> None:
        """
        Disables the RF preamp

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        assert self.hasPreamp
        self.set_preamp_state(False)
        if self.verify:
            assert not self.read_preamp_state()

    ##########################################################
    ## Functions for which no generic implementation exists ##
    ##########################################################

    def set_rbw(self, rbw: int) -> None:
        """
        Sets Resolution Bandwidth

        Args:
           rbw (float): RBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def set_vbw(self, vbw: int) -> None:
        """
        Sets Video Bandwidth

        Args:
           vbw (float): VBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def measure_power(self, freq: int) -> float:
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
        raise NotImplementedError

    def set_ref_level(self, power: float) -> None:
        """
        Sets amplitude reference

        Args:
            power (float): Reference Level in dBm

        Returns:
            float: Measured power in dBm

        Raises:
            None
        """
        raise NotImplementedError

    def trigger_measurement(self) -> None:
        """
        Triggers a measurement

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def enable_averaging(self, numAverages: int = 10) -> None:
        """
        Sets the number of traces to average each measurement over

        Args:
            numAverages (int): Number of traces to average over

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def disable_averaging(self) -> None:
        """
        Disables averaging of traces

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def read_trace_data(self) -> list[float]:
        """
        Returns y-axis value for each points in y-axis units

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def set_detector_mode(self, mode: DetectorMode) -> None:
        """
        Sets detector mode

        Args:
            mode (DetectorMode): Detector Mode

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def set_preamp_state(self, enabled: bool) -> None:
        """
        Sets the state of the RF preamp

        Args:
            enabled (bool): True to enable the preamp

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError

    def read_preamp_state(self) -> bool:
        """
        Returns the state of the RF preamp

        Args:
            None

        Returns:
            bool: True if enabled

        Raises:
            None
        """
        raise NotImplementedError
