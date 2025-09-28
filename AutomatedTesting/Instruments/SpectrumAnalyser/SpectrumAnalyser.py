# Standard imports
from enum import Enum, auto
from logging import Logger
from typing import Optional, Union
from math import ceil, floor
from dataclasses import dataclass
from datetime import datetime
import re
from pathlib import Path

# Third party imports
from numpy import linspace
from pyvisa import ResourceManager

# Local imports
from AutomatedTesting.Instruments.EntireInstrument import EntireInstrument
from AutomatedTesting.Instruments.Transducer.Transducer import Transducer
from AutomatedTesting.Misc.Units import AmplitudeUnits, FieldStrengthUnits


class SpectrumAnalyser(EntireInstrument):
    class SweepMode(Enum):
        SINGLE = auto()
        CONTINUOUS = auto()

    class FilterType(Enum):
        NORMAL = auto()
        EMI = auto()

    class DetectorType(Enum):
        POSITIVE_PEAK = "Peak"
        NEGATIVE_PEAK = "Negative Peak"
        AVERAGE = "Average"
        QUASI_PEAK = "Quasi-Peak"

    class TraceMode(Enum):
        CLEAR_WRITE = auto()
        MAX_HOLD = auto()
        MIN_HOLD = auto()
        VIEW = auto()
        BLANK = auto()
        AVERAGE = auto()

    @dataclass
    class SpectrumAnalyserMeasurement:
        datapoints: dict["SpectrumAnalyser.DetectorType", list[tuple[float, float]]]
        units: Union[AmplitudeUnits, FieldStrengthUnits]

        def __add__(
            self, other: "SpectrumAnalyser.SpectrumAnalyserMeasurement"
        ) -> "SpectrumAnalyser.SpectrumAnalyserMeasurement":
            """
            Allows combination of the results of multiple sweeps
            e.g. EMC emissions measured with different settings
            """
            assert self.units == other.units, (
                "Measurements to be combined have different "
                f"units: {self.units} and {other.units}"
            )
            result = SpectrumAnalyser.SpectrumAnalyserMeasurement(
                datapoints={}, units=self.units
            )

            self_detectors = [x for x in self.datapoints]
            other_detectors = [x for x in other.datapoints]

            for detector_type in set(self_detectors + other_detectors):
                try:
                    self_freqs = [x[0] for x in self.datapoints[detector_type]]
                except KeyError:
                    self_freqs = []

                try:
                    other_freqs = [x[0] for x in other.datapoints[detector_type]]
                except KeyError:
                    other_freqs = []

                common_freqs = set(self_freqs) & set(other_freqs)
                assert (
                    not common_freqs
                ), f"Multiple measurements found at frequency: {common_freqs}"

                # It's cleaner to make sure both datapoints dicts have something for
                # each detector type rather than handle KeyErrors in the combination

                if detector_type not in self_detectors:
                    self.datapoints[detector_type] = []

                if detector_type not in other_detectors:
                    other.datapoints[detector_type] = []

                result.datapoints[detector_type] = sorted(
                    self.datapoints[detector_type] + other.datapoints[detector_type],
                    key=lambda x: x[0],
                )

            return result

        def save_to_file(
            self,
            results_dir: Optional[Path] = None,
            filename_prefix: Optional[str] = None,
        ) -> list[Path]:

            written_paths = []

            current_time_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            if results_dir is None:
                results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            for detector, measurements in self.datapoints.items():
                filename_str = (
                    f"{current_time_str}_{re.sub(' ', '-', detector.value)}.csv"
                )
                if filename_prefix:
                    filename_str = f"{re.sub(' ', '-', filename_prefix)}_{filename_str}"

                file_path = results_dir / filename_str

                written_paths.append(file_path)

                with open(file_path, "w") as file:
                    file.write(f"Frequency (Hz), Amplitude ({self.units})\n")
                    for x in measurements:
                        file.write(f"{x[0]},{x[1]}\n")
            return written_paths

    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: Logger,
        min_freq: int,
        max_freq: int,
        min_num_sweep_points: int,
        max_num_sweep_points: int,
        min_sweep_time_s: float,
        max_sweep_time_s: float,
        min_span_hz: int,  # Note this is ignoring zero span
        max_span_hz: int,
        min_attenuation_db: float,
        max_attenuation_db: float,
        has_preamp: bool,
        supported_rbw: list[int],
        supported_vbw: list[int],
        max_num_traces: int,
        max_num_markers: int,
        supports_emi_measurements: bool = True,
        supported_emi_rbw: Optional[list[int]] = None,
        **kwargs,
    ):
        """
        Pure virtual class for Spectrum Analyser
        This should never be implemented directly
        """
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logger=logger,
            **kwargs,
        )
        if (
            (max_freq < min_freq)
            or (max_num_sweep_points < min_num_sweep_points)
            or (max_span_hz < min_span_hz)
        ):
            raise ValueError
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.min_num_sweep_points = min_num_sweep_points
        self.max_num_sweep_points = max_num_sweep_points
        self.min_span_hz = min_span_hz
        self.max_span_hz = max_span_hz
        self.min_sweep_time_s = min_sweep_time_s
        self.max_sweep_time_s = max_sweep_time_s
        self.min_attenuation_db = min_attenuation_db
        self.max_attenuation_db = max_attenuation_db
        self.has_preamp = has_preamp
        self.supported_rbw = supported_rbw
        self.supported_vbw = supported_vbw
        self.min_num_sweep_points = min_num_sweep_points
        self.max_num_sweep_points = max_num_sweep_points
        self.max_num_traces = max_num_traces
        self.max_num_markers = max_num_markers
        self.supports_emi_measurements = supports_emi_measurements
        if self.supports_emi_measurements:
            assert supported_emi_rbw is not None
        self.supported_emi_rbw = supported_emi_rbw

    # Functions that must be specified by the individual class
    # All input validation should happen in the SpectrumAnalyser base class
    # so these functions should purely implement the transaction
    def _set_start_freq(self, freq_hz: float):
        raise NotImplementedError  # pragma: no cover

    def _get_start_freq(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_stop_freq(self, freq_hz: float):
        raise NotImplementedError  # pragma: no cover

    def _get_stop_freq(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_centre_freq(self, freq_hz: float):
        raise NotImplementedError  # pragma: no cover

    def _get_centre_freq(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_span(self, span_hz: float):
        raise NotImplementedError  # pragma: no cover

    def _get_span(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_zero_span_enabled_state(self, enabled: bool) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_zero_span_enabled_state(self) -> bool:
        raise NotImplementedError  # pragma: no cover

    def _set_filter_type(self, filter_type: FilterType) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_filter_type(self) -> FilterType:
        raise NotImplementedError  # pragma: no cover

    def _set_rbw(self, rbw_hz: float) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_rbw(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_vbw(self, vbw_hz: float) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_vbw(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_sweep_mode(self, mode: SweepMode) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_sweep_mode(self) -> SweepMode:
        raise NotImplementedError  # pragma: no cover

    def _set_num_sweep_points(self, num_points: int) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_num_sweep_points(self) -> int:
        raise NotImplementedError  # pragma: no cover

    def _set_input_attenuation(self, attenuation_db: float) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_input_attenuation(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_ref_level(self, ref_level) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_ref_level(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _trigger_sweep(self) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_trace_data(self, trace_num: int) -> list[float]:
        raise NotImplementedError  # pragma: no cover

    def _set_marker_enabled_state(self, marker_num: int, enabled_bool) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_marker_enabled_state(self, marker_num: int) -> bool:
        raise NotImplementedError  # pragma: no cover

    def _set_marker_freq(
        self,
        marker_num: int,
        freq_hz: float,
    ) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_marker_freq(self, marker_num: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def _measure_marker_power(self, marker_num: int) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_trace_mode(self, trace_num: int, mode: TraceMode) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_trace_mode(self, trace_num: int) -> TraceMode:
        raise NotImplementedError  # pragma: no cover

    def _set_detector_type(self, trace_num: int, detector_type: DetectorType) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_detector_type(self, trace_num: int) -> DetectorType:
        raise NotImplementedError  # pragma: no cover

    def _set_y_axis_units(self, units: AmplitudeUnits) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_y_axis_units(self) -> AmplitudeUnits:
        raise NotImplementedError  # pragma: no cover

    def _set_preamp_enabled_state(self, enabled: bool):
        raise NotImplementedError  # pragma: no cover

    def _get_preamp_enabled_state(self) -> bool:
        raise NotImplementedError  # pragma: no cover

    def _set_sweep_time(self, sweep_time_s: float) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_sweep_time(self) -> float:
        raise NotImplementedError  # pragma: no cover

    def _set_sweep_time_auto_enabled_state(self, enabled: bool) -> None:
        raise NotImplementedError  # pragma: no cover

    def _get_sweep_time_auto_enabled_state(self) -> bool:
        raise NotImplementedError  # pragma: no cover

    ################################################################
    # Wrappers for functions that are for all devices
    # Any input validation should happen here so it is used across
    # all SpectrumAnalyser inherited classes
    ################################################################

    def __enter__(self):
        super().__enter__()
        self.set_sweep_mode(self.SweepMode.SINGLE)
        for x in range(1, self.max_num_traces + 1):
            self.disable_trace(x)
        for x in range(1, self.max_num_markers + 1):
            self.set_marker_enabled_state(x, False)
        return self

    def __exit__(self, *args, **kwargs):
        if self.has_preamp:
            self.disable_preamp()
        self.set_input_attenuation(20)
        self.enable_auto_sweep_time()
        self.set_sweep_mode(self.SweepMode.CONTINUOUS)
        self.corrections = None
        self.transducer = None

        super().__exit__(*args, **kwargs)

    def set_start_freq(self, freq: float):
        """
        Sets start frequency

        Args:
            freq (float): Start Frequency in Hz

        Returns:
            None

        Raises:
            ValueError: If <freq> is outside min_freq -> max_freq
            AssertionError: If readback value doesn't match requested
        """
        if not (self.min_freq <= freq <= self.max_freq):
            raise ValueError
        self._set_start_freq(freq)
        if self.verify:
            response = self.get_start_freq()
            assert response == freq

    def get_start_freq(self) -> float:
        """
        Reads start frequency

        Args:
            None

        Returns:
            float: Start Frequency in Hz

        Raises:
            None
        """
        return self._get_start_freq()

    def set_stop_freq(self, freq_hz: float):
        """
        Sets stop frequency

        Args:
            freq (float): Stop Frequency in Hz

        Returns:
            None

        Raises:
            ValueError: If <freq> is outside min_freq -> max_freq
            AssertionError: If readback value doesn't match requested
        """
        if not (self.min_freq <= freq_hz <= self.max_freq):
            raise ValueError
        self._set_stop_freq(freq_hz)
        if self.verify:
            assert self.get_stop_freq() == freq_hz

    def get_stop_freq(self) -> float:
        """
        Reads stop frequency

        Args:
            None

        Returns:
            float: Stop Frequency in Hz

        Raises:
            None
        """
        return self._get_stop_freq()

    def set_centre_freq(self, freq_hz: float):
        """
        Sets centre frequency

        Args:
            freq (float): Centre Frequency in Hz

        Returns:
            None

        Raises:
            ValueError: If <freq> is outside min_freq -> max_freq
            AssertionError: If readback value doesn't match requested
        """
        if not (self.min_freq <= freq_hz <= self.max_freq):
            raise ValueError
        self._set_centre_freq(freq_hz)
        if self.verify:
            assert self.get_centre_freq() == freq_hz

    def get_centre_freq(self) -> float:
        """
        Reads centre frequency

        Args:
            None

        Returns:
            float: centre Frequency in Hz

        Raises:
            None
        """
        return self._get_centre_freq()

    def set_span(self, span_hz: float):
        """
        Sets span

        Args:
            freq (float): Span in Hz

        Returns:
            None

        Raises:
            ValueError: If <span> is outside min_span_hz -> max_span_hz
            AssertionError: If readback value doesn't match requested
        """
        if not (self.min_span_hz <= span_hz <= self.max_span_hz):
            raise ValueError
        self._set_span(span_hz)
        if self.verify:
            assert self.get_span() == span_hz

    def get_span(self) -> float:
        """
        Reads span

        Args:
            None

        Returns:
            float: Span in Hz

        Raises:
            None
        """
        return self._get_span()

    def set_zero_span_enabled_state(self, enabled: bool) -> None:
        """
        Controls whether the spectrum analyser is in zero span mode

        Args:
            enabled (bool): Set True to enable zero span mode

        Returns:
            None

        Raises:
            AssertionError: If readback span isn't zero
        """
        self._set_zero_span_enabled_state(enabled)
        readback = self.get_zero_span_enabled_state()
        if self.verify:
            assert readback == enabled

    def get_zero_span_enabled_state(self) -> bool:
        """
        Returns true if spectrum analyser is in a zero span state

        Args:
            None

        Returns:
            bool: True is in zero span

        Raises:
            AssertionError: If readback span isn't zero
        """
        return self._get_zero_span_enabled_state()

    def enable_zero_span(self) -> None:
        self.set_zero_span_enabled_state(True)

    def disable_zero_span(self) -> None:
        self.set_zero_span_enabled_state(False)

    def set_rbw(self, rbw_hz: float, filter_type: FilterType = FilterType.NORMAL):
        """
        Sets Resolution Bandwidth (RBW)

        Args:
            rbw (float): RBW in Hz
            filter_type (FilterType): type of filter the detector is using

        Returns:
            None

        Raises:
            ValueError: If requested RBW isn't in supported list
            AssertionError: If readback value doesn't match requested
        """
        if filter_type == self.FilterType.EMI:
            if not self.supports_emi_measurements:
                raise ValueError
            # Not necessary (as validated on initialisation)
            # but stops Pylance complaining
            assert self.supported_emi_rbw
            if rbw_hz not in self.supported_emi_rbw:
                raise ValueError
        else:
            if rbw_hz not in self.supported_rbw:
                raise ValueError

        self._set_filter_type(filter_type)
        self._set_rbw(rbw_hz)
        if self.verify:
            assert self.get_filter_type() == filter_type
            assert self.get_rbw() == rbw_hz

    def get_filter_type(self) -> FilterType:
        """
        Reads currently used filter type

        Args:
            None

        Returns:
            FilterType: type of filter in use

        Raises:
            None
        """
        return self._get_filter_type()

    def get_rbw(self) -> float:
        """
        Reads Resolution Bandwidth (RBW)

        Args:
            None

        Returns:
            float: RBW in Hz

        Raises:
            None
        """
        return self._get_rbw()

    def set_vbw(self, vbw_hz: float):
        """
        Sets Video Bandwidth (VBW)

        Args:
            vbw (float): VBW in Hz

        Returns:
            None

        Raises:
            ValueError: If requested RBW isn't in supported list
            AssertionError: If readback value doesn't match requested
        """
        if vbw_hz not in self.supported_vbw:
            raise ValueError
        self._set_vbw(vbw_hz)
        if self.verify:
            assert self.get_vbw() == vbw_hz

    def get_vbw(self) -> float:
        """
        Reads Video Bandwidth (VBW)

        Args:
            None

        Returns:
            float: VBW in Hz

        Raises:
            None
        """
        return self._get_vbw()

    def set_sweep_mode(self, mode: SweepMode = SweepMode.CONTINUOUS):
        """
        Sets analyser into continuous or single sweep mode

        Args:
            mode(SweepMode): Mode to set the analyser to

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested
        """
        self._set_sweep_mode(mode)
        if self.verify:
            assert self.get_sweep_mode() == mode

    def get_sweep_mode(self) -> SweepMode:
        """
        Returns Sweep mode of the analyser

        Args:
            None

        Returns:
            SweepMode: Mode the analyser is in

        Raises:
            None
        """
        return self._get_sweep_mode()

    def set_num_sweep_points(self, num_points: int):
        """
        Sets number of sweep points
        Args:
            num_points (int): number of points in the sweep

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested
        """
        if not self.min_num_sweep_points <= num_points <= self.max_num_sweep_points:
            raise ValueError
        self._set_num_sweep_points(num_points)
        if self.verify:
            assert self.get_num_sweep_points() == num_points

    def get_num_sweep_points(self) -> int:
        """
        Reads number of sweep points

        Args:
            None

        Returns:
            int: number of sweep points

        Raises:
            None
        """
        return self._get_num_sweep_points()

    def set_input_attenuation(self, attenuation_db: float):
        """
        Sets input attenuation

        Args:
            attenuation (float): attenuation in dB i.e. all values should be positive

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested value
        """
        if not self.min_attenuation_db <= attenuation_db <= self.max_attenuation_db:
            raise ValueError
        self._set_input_attenuation(attenuation_db)
        if self.verify:
            assert self.get_input_attenuation() == attenuation_db

    def get_input_attenuation(self) -> float:
        """
        Reads input attenuation

        Args:
            None

        Returns:
            float: input attenuation in dB

        Raises:
            None
        """
        return self._get_input_attenuation()

    def set_ref_level(self, ref_level: float):
        """
        Sets Reference Level

        Args:
            level (float): reference level in y-axis units (normally dBm)

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested value
        """
        self._set_ref_level(ref_level)
        if self.verify:
            assert self.get_ref_level() == ref_level

    def get_ref_level(self) -> float:
        """
        Reads Reference Level

        Args:
            None

        Returns:
            float: Reference Level in y-axis units (normally dBm)

        Raises:
            None
        """
        return self._get_ref_level()

    def trigger_sweep(self, num_sweeps: int = 1, timeout_s: int = 60) -> None:
        """
        Triggers a sweep and blocks until completion

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        for _ in range(num_sweeps):
            self._trigger_sweep()
            self.wait_until_op_complete(timeout_s)

    def get_trace_freqs(self) -> list[float]:
        """
        Returns a list of the swept frequency points
        N.B. This assumes that the spacing is linear
        """
        freqs = linspace(
            self.get_start_freq(), self.get_stop_freq(), self.get_num_sweep_points()
        )
        return [float(x) for x in freqs]

    def get_trace_data(self, trace_num: int = 1) -> SpectrumAnalyserMeasurement:
        """
        Returns trace data for a given trace number

        Args:
            trace_num (int): Number of which trace to get data from

        Returns:
            list[tuple[float, float]:
                List of (frequency in Hz, power in y-axis units) tuples

        Raises:
            None
        """
        self.validate_trace_num(trace_num)

        if self.get_zero_span_enabled_state():
            raise RuntimeError("Cannot get frequency data in zero span mode")

        freqs = self.get_trace_freqs()
        data = self._get_trace_data(trace_num)
        detector_type = self.get_detector_type(trace_num)
        y_axis_units = self.get_y_axis_units()

        datapoints = [x for x in zip(freqs, data)]
        if self.corrections:
            datapoints = [(f, self.corrections.correct(f, d)) for f, d in datapoints]
        if self.transducer:
            assert y_axis_units == self.transducer.output_units
            datapoints = [
                (f, self.transducer.conversion_func_output_to_input(f, d))
                for f, d in datapoints
            ]
            y_axis_units = self.transducer.input_units
        return SpectrumAnalyser.SpectrumAnalyserMeasurement(
            {detector_type: datapoints}, y_axis_units
        )

    def validate_marker_num(self, marker_num: int) -> None:
        """
        Checks whether the marker number requested is valid

        Args:
            marker_num (int): marker number to test

        Returns:
            None

        Raises:
            ValueError: If marker number is invalid
        """
        if not 1 <= marker_num <= self.max_num_markers:
            raise ValueError

    def set_marker_enabled_state(self, marker_num: int = 1, enabled: bool = False):
        """
        En/disables a marker

        Args:
            marker_num (int): which marker to en/disable
            enabled (bool): Enable marker if True, Disable if False

        Returns:
            None

        Raises:
            AssertionError: If readback state doesn't match requested
        """
        self.validate_marker_num(marker_num)
        self._set_marker_enabled_state(marker_num, enabled)
        if self.verify:
            assert self.get_marker_enabled_state(marker_num) == enabled

    def get_marker_enabled_state(self, marker_num: int = 1) -> bool:
        """
        Returns state of a particular marker

        Args:
            marker_num (int): which marker to get the state of

        Returns:
            bool: True if the marker is enabled

        Raises:
            ValueError: If <marker_num> is invalid
        """
        self.validate_marker_num(marker_num)
        return self._get_marker_enabled_state(marker_num)

    def set_marker_freq(
        self,
        marker_num: int,
        freq_hz: float,
    ):
        """
        Sets marker to a particular frequency

        Args:
            freq (float): Frequency to set the marker to in Hz
            marker_num (int): which marker to move

        Returns:
            None

        Raises:
            AssertionError: If readback frequency doesn't match requested
        """
        self.validate_marker_num(marker_num)
        self._set_marker_freq(marker_num, freq_hz)
        if self.verify:
            assert self.get_marker_freq(marker_num) == freq_hz

    def get_marker_freq(self, marker_num: int = 1) -> float:
        """
        Reads frequency a particular marker is set to

        Args:
            marker_num (int): which marker to query

        Returns:
            float: marker frequency in Hz

        Raises:
            None
        """
        self.validate_marker_num(marker_num)
        return self._get_marker_freq(marker_num)

    def measure_marker_power(self, marker_num: int = 1) -> float:
        """
        Reads power for a a particular marker

        Args:
            marker_num (int): which marker to query

        Returns:
            float: marker power in dBm

        Raises:
            None
        """
        self.validate_marker_num(marker_num)
        return self._measure_marker_power(marker_num)

    def enable_marker(self, marker_num: int = 1):
        self.set_marker_enabled_state(marker_num, True)

    def disable_marker(self, marker_num: int = 1):
        self.set_marker_enabled_state(marker_num, False)

    def measure_power(self, freq: float, marker_num: int = 1) -> float:
        """
        Measure power at a certain frequency by placing a
        marker and reporting the value

        Args:
            freq (float): frequency in Hz

        Returns:
            float: power in dBm

        Raises:
            ValueError: If <freq> is not within the trace data
        """
        if marker_num > self.max_num_markers:
            raise ValueError
        if not self.get_marker_enabled_state(marker_num):
            self.enable_marker(marker_num)
        self.set_marker_freq(marker_num, freq)
        return self.measure_marker_power(marker_num)

    def validate_trace_num(self, trace_num: int) -> None:
        """
        Checks whether the trace number requested is valid

        Args:
            trace_num (int): trace number to test

        Returns:
            None

        Raises:
            ValueError: If trace number is invalid
        """
        if not 1 <= trace_num <= self.max_num_traces:
            raise ValueError

    def set_trace_mode(self, trace_num: int, mode: TraceMode):
        """
        Sets the mode of a trace

        Args:
            trace_num (int): Number of trace to set state of
            enabled (bool): True will enable the trace

        Returns:
            None

        Raises:
            AssertionError: if readback is not correct
        """
        self.validate_trace_num(trace_num)
        self._set_trace_mode(trace_num, mode)
        if self.verify:
            assert self.get_trace_mode(trace_num) == mode

    def get_trace_mode(self, trace_num: int) -> TraceMode:
        """
        Returns the mode of a trace

        Args:
            trace_num (int): Number of trace to get state of

        Returns:
            TraceMode: mode of requested trace

        Raises:
            None
        """
        self.validate_trace_num(trace_num)
        return self._get_trace_mode(trace_num)

    def disable_trace(self, trace_num: int):
        """
        Removes a trace from the display.

        Args:
            trace_num (int): which trace to get the state of

        Returns:
            None

        Raises:
            None
        """
        self.set_trace_mode(trace_num, SpectrumAnalyser.TraceMode.BLANK)

    def set_detector_type(self, trace_num: int, detector_type: DetectorType) -> None:
        """
        Sets the detector type used for a certain trace

        Args:
            trace_num (int): which trace to set the detector of
            detector_type (DetectorType): which detector type to use

        Returns:
            None

        Raises:
            None
        """
        self.validate_trace_num(trace_num)
        self._set_detector_type(trace_num, detector_type)
        if self.verify:
            assert self.get_detector_type(trace_num) == detector_type

    def get_detector_type(self, trace_num: int) -> DetectorType:
        """
        Returns the detector type used for a certain trace

        Args:
            trace_num (int): which trace to get the detector of

        Returns:
            DetectorType: which detector is in use

        Raises:
            None
        """
        self.validate_trace_num(trace_num)
        return self._get_detector_type(trace_num)

    def perform_multi_part_sweep(
        self,
        start_freq: float,
        stop_freq: float,
        step_size: float,
        ensure_stop_freq_is_covered: bool = True,
        detector_types: Optional[list[DetectorType]] = None,
        seconds_per_mhz: Optional[float] = None,
        num_sweeps: int = 1,
        units: AmplitudeUnits | FieldStrengthUnits = AmplitudeUnits.DBM,
    ) -> SpectrumAnalyserMeasurement:
        """
        Some sweeps may require > 1 sweep to capture at sufficient resolution
        e.g. for EMC measurements where there might be a small RBW,
        step size must be RBW/2 (for full capture), and a large span

        This performs as many sweeps as needed at the spectrum analyser's maximum number
        of points and concatenates the results

        It will always start at <start-freq>, behaviour of the last point is
        controlled by <ensure_stop_freq_is_covered>.
            If True (max sure frequency range exceeds that point):
                it will stop at the smallest value of N for which
                <start-freq> + N * <step-size> >= stop_freq
            If False (e.g. if stop freq is max_freq of spectrum analyser
                    and must not be exceeded):
                it will stop at the largest value of N for which
                <start-freq> + N * <step-size> <= stop_freq

        """
        if self.transducer:
            assert units == self.transducer.input_units
        self.set_y_axis_units(
            self.transducer.output_units if self.transducer else units
        )

        results = SpectrumAnalyser.SpectrumAnalyserMeasurement(
            datapoints={}, units=units
        )

        if detector_types is None:
            detector_types = [SpectrumAnalyser.DetectorType.POSITIVE_PEAK]

        for trace_num, detector_type in enumerate(detector_types):
            self.set_detector_type(trace_num + 1, detector_type)
            self.set_trace_mode(trace_num + 1, SpectrumAnalyser.TraceMode.MAX_HOLD)

        # Plus 1 for fencepost problem
        num_points_required = 1 + (stop_freq - start_freq) / step_size
        if ensure_stop_freq_is_covered:
            num_points_required = ceil(num_points_required)
        else:
            num_points_required = floor(num_points_required)

        # Can't handle if the request is smaller than min sweep points.
        # What extra frequencies do you than pad, on what side of the requested range?
        assert num_points_required >= self.min_num_sweep_points

        freqs_to_measure = [
            start_freq + x * step_size for x in range(num_points_required)
        ]

        current_start_freq_index = 0
        stop_freq_index = num_points_required - 1
        num_remaining_points = num_points_required

        while num_remaining_points:
            if num_remaining_points >= self.min_num_sweep_points:
                num_points_to_measure = min(
                    num_remaining_points, self.max_num_sweep_points
                )
                self.set_start_freq(freqs_to_measure[current_start_freq_index])
                self.set_stop_freq(
                    freqs_to_measure[
                        current_start_freq_index + num_points_to_measure - 1
                    ]
                )
                self.set_num_sweep_points(num_points_to_measure)
                if seconds_per_mhz:
                    self.set_sweep_time(
                        num_points_to_measure * step_size * seconds_per_mhz / 1e6
                    )
                else:
                    self.enable_auto_sweep_time()
                self.trigger_sweep(num_sweeps)

                # Add datapoints to results
                for trace_index, detector_type in enumerate(detector_types):
                    results += self.get_trace_data(trace_index + 1)

                # Update counters
                current_start_freq_index += num_points_to_measure
                num_remaining_points -= num_points_to_measure
            else:
                # We need fewer points than can be handled in a single sweep :(
                num_points_to_measure = self.min_num_sweep_points
                self.set_start_freq(
                    freqs_to_measure[stop_freq_index - num_points_to_measure + 1]
                )
                self.set_stop_freq(freqs_to_measure[stop_freq_index])
                self.set_num_sweep_points(num_points_to_measure)
                if seconds_per_mhz:
                    self.set_sweep_time(
                        num_points_to_measure * step_size * seconds_per_mhz / 1e6
                    )
                else:
                    self.enable_auto_sweep_time()
                self.trigger_sweep(num_sweeps)
                # Add valid datapoints to results - there will be unnecessary points
                # at the start
                for trace_index, detector_type in enumerate(detector_types):
                    results.datapoints[detector_type] += [
                        x
                        for x in self.get_trace_data(trace_index + 1).datapoints[
                            detector_type
                        ]
                        if x[0] >= freqs_to_measure[current_start_freq_index]
                    ]

                current_start_freq_index = stop_freq_index
                num_remaining_points = 0

        # Sanity check we'be ended up with the right frequenceies
        for datapoints in results.datapoints.values():
            assert freqs_to_measure == [x[0] for x in datapoints]

        return results

    def set_y_axis_units(self, units: AmplitudeUnits) -> None:
        """
        Sets the units in use for the y-axis

        Args:
            units (AmplitudeUnits): which units to use

        Returns:
            None

        Raises:
            AssertionError: if readback is not correct
        """
        self._set_y_axis_units(units)
        if self.verify:
            assert self.get_y_axis_units() == units

    def get_y_axis_units(self) -> AmplitudeUnits:
        """
        Returns the units in use for the y-axis

        Args:
            None

        Returns:
            AmplitudeUnits: which units are in use

        Raises:
            None
        """
        return self._get_y_axis_units()

    def set_preamp_enabled_state(self, enabled: bool):
        """
        Sets whether the pre-amp is enabled

        Args:
            None

        Returns:
            YAxisUnits: which units are in use

        Raises:
            RuntimeError: If spectrum analyser doesn't have a preamp
            AssertionError: if readback is not correct
        """
        if self.has_preamp is False:
            raise RuntimeError(
                "Attempted to set pre-amp state on analyser without preamp"
            )
        self._set_preamp_enabled_state(enabled)
        if self.verify:
            assert self.get_preamp_enabled_state() == enabled

    def get_preamp_enabled_state(self) -> bool:
        """
        Returns true if the pre-amp is enabled

        Args:
            None

        Returns:
            bool: True if pre-amp is enabled

        Raises:
            RuntimeError: If spectrum analyser doesn't have a preamp
        """
        if self.has_preamp is False:
            raise RuntimeError(
                "Attempted to set pre-amp state on analyser without preamp"
            )
        return self._get_preamp_enabled_state()

    def enable_preamp(self):
        self.set_preamp_enabled_state(True)

    def disable_preamp(self):
        self.set_preamp_enabled_state(False)

    def set_sweep_time(self, sweep_time_s: float) -> None:
        """
        Sets sweep time

        Args:
            sweep_time_s (float): sweep time in seconds

        Returns:
            None

        Raises:
            ValueError: if sweep_time_s is outside_supported_range
            AssertionError: if readback value is incorrect
        """

        # Auto sweep time will almost certainly be fastest so also need to ensure
        # requested time exceeds that
        self.enable_auto_sweep_time()
        auto_sweep_time = self.get_sweep_time()

        if not self.min_sweep_time_s <= sweep_time_s <= self.max_sweep_time_s:
            raise ValueError

        if not sweep_time_s >= auto_sweep_time:
            raise ValueError(
                f"Requested sweep time of {sweep_time_s}s is less "
                f"than auto time of {auto_sweep_time}s"
            )

        self._set_sweep_time(sweep_time_s)
        if self.verify:
            assert self.get_sweep_time() == sweep_time_s

    def get_sweep_time(self) -> float:
        """
        Returns sweep time

        Args:
            None

        Returns:
            float: sweep time in seconds

        Raises:
            None
        """
        return self._get_sweep_time()

    def set_sweep_time_auto_enabled_state(self, enabled: bool) -> None:
        """
        Sets whether auto sweep time is used or not

        Args:
            enabled (bool): True to enable auto-sweep time

        Returns:
            None

        Raises:
            AssertionError: if readback value is incorrect
        """
        self._set_sweep_time_auto_enabled_state(enabled)
        if self.verify:
            assert self.get_sweep_time_auto_enabled_state() == enabled

    def get_sweep_time_auto_enabled_state(self) -> bool:
        """
        Returns whether auto sweep time is used or not

        Args:
            None

        Returns:
            bool: True if auto-sweep time is enabled

        Raises:
            None
        """
        return self._get_sweep_time_auto_enabled_state()

    def enable_auto_sweep_time(self):
        """
        Sets sweep time to auto

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        # Don't have disable function - that will happen when
        # sweep time is set manually
        self.set_sweep_time_auto_enabled_state(True)

    def apply_transducer(self, transducer: Transducer) -> None:
        super().apply_transducer(transducer)
        self.set_y_axis_units(transducer.output_units)
