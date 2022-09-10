import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from time import sleep
from typing import Optional

from AutomatedTesting.Instruments.TopLevel.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq
from pyvisa import VisaIOError


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
        self._write(":INIT:CONT 0")
        logging.info(f"{self.name} initialised")

    def cleanup(self):
        self.set_input_attenuator(10)
        if self.hasPreamp:
            self.disable_preamp()
        self.disable_averaging()
        self._write(":INIT:CONT 1")
        super().cleanup()

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
        if not self.minSweepPoints:
            logging.warning(
                f"{self.name} does not allow setting of number of sweep points. Ignoring command"
            )
        else:
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

    def set_ref_level(self, power: float) -> None:
        """
        Sets amplitude reference

        Args:
            power (float): Reference Level in dBm

        Returns:
            None

        Raises:
            None
        """
        self._write(f":DISP:WINDow:TRAC:Y:RLEV {power}")
        if self.verify:
            assert self.read_ref_level() == power

    def read_ref_level(self) -> float:
        """
        Returns amplitude reference

        Args:
            None

        Returns:
            float: Reference Level in dBm

        Raises:
            None
        """
        return float(self._query(":DISP:WINDow:TRAC:Y:RLEV?"))

    def set_ampl_scale(self, dBperDiv: float) -> None:
        """
        Sets y-axis scale

        Args:
            dBperDiv (float): dB per division

        Returns:
            None

        Raises:
            ValueError: If requested value is out of allowed range
            AssertionError: If readback value is incorrect
        """
        if not 0.1 <= dBperDiv <= 20:
            raise ValueError

        self._write(f":DISP:WINDow:TRAC:Y:PDIV {dBperDiv}")
        if self.verify:
            assert self.read_ampl_scale() == dBperDiv

    def read_ampl_scale(self) -> float:
        """
        Reads y-axis scale

        Args:
            None

        Returns:
            float: Y-axis scale in dB per division

        Raises:
            None
        """
        return float(self._query(":DISP:WINDow:TRAC:Y:PDIV?"))

    def set_input_attenuator(self, att: float) -> None:
        """
        Sets input attenuation

        Args:
            att (float): attenuation in dB

        Returns:
            None

        Raises:
            ValueError: If requested value is out of allowed range
            AssertionError: If readback value is incorrect
        """
        self._write(f":POW:ATT {att}")
        if self.verify:
            assert self.read_input_attenuator() == att

    def read_input_attenuator(self) -> float:
        """
        Reads input attenuation

        Args:
            None

        Returns:
            float: Input attenuation in dB

        Raises:
            None
        """
        return float(self._query(":POW:ATT?"))

    def trigger_measurement(self):
        """
        Triggers a measurement

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.lock.acquire()

        try:
            self._write(":INIT:IMM", acquireLock=False)
            running = True
            while running:
                try:
                    running = self._query("*OPC?", acquireLock=False) == "0"
                except VisaIOError:
                    pass
                sleep(1)
        finally:
            self.lock.release()

    def get_trace_data(self) -> list[float]:
        """
        Returns trace data

        Args:
            None

        Returns:
            list[float]: y axis value of each datapoint

        Raises:
            None
        """
        self.trigger_measurement()
        data = self._query(":TRAC? TRACE1")
        return [float(x) for x in data.split(",")]

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
        if mode == DetectorMode.RMS:
            self._write(":DET RMS")
        else:
            raise NotImplementedError

        if self.verify:
            assert self.read_detector_mode() == mode

    def read_detector_mode(self) -> DetectorMode:
        """
        Sets detector mode

        Args:
            None

        Returns:
            DetectorMode: Detector mode

        Raises:
            None
        """
        ret = self._query(":DET?")
        if ret == "RMS":
            return DetectorMode.RMS
        else:
            raise NotImplementedError(ret)

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

    def read_rbw(self) -> int:
        """
        Returns Resolution Bandwidth

        Args:
           None

        Returns:
            int: RBW in Hz

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

    def read_vbw(self) -> int:
        """
        Returns Video Bandwidth

        Args:
           None

        Returns:
            int: VBW in Hz

        Raises:
            None
        """
        raise NotImplementedError

    def set_vbw_rbw_ratio(self, ratio: float) -> None:
        """
        Sets VBW:RBW ratio

        Args:
           ratio (float): Desired VBW:RBW ratio

        Returns:
            None

        Raises:
            ValueError: If requested ratio is not supported
            AssertionError: If readback fails
        """
        raise NotImplementedError

    def read_vbw_rbw_ratio(self) -> float:
        """
        Returns VBW:RBW ratio

        Args:
           None

        Returns:
            float: VBW:RBW ratio

        Raises:
            None
        """
        raise NotImplementedError

    def measure_power_marker(self, freq: int) -> float:
        """
        Measures RF Power by putting a marker at frequency 'freq'

        Args:
            freq (float): Frequency of measured signal


        Returns:
            float: Measured power in dBm

        Raises:
            None
        """
        raise NotImplementedError

    def measure_power_zero_span(self, freq: int) -> float:
        """
        Measures RF Power by setting centre frequency to 'freq'
        and span to 0. Returns max value seen

        Args:
            freq (float): Frequency of measured signal

        Returns:
            float: Measured power in dBm

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
