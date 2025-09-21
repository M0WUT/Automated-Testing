from enum import Enum, auto
from logging import Logger
from typing import Optional

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.EntireInstrument import EntireInstrument


class SpectrumAnalyser(EntireInstrument):
    class SweepMode(Enum):
        SINGLE = auto()
        CONTINUOUS = auto()

    class FilterType(Enum):
        NORMAL = auto()
        EMI = auto()

    class DetectorType(Enum):
        POSITIVE_PEAK = auto()
        NEGATIVE_PEAK = auto()
        AVERAGE = auto()
        QUASI_PEAK = auto()

    class TraceMode(Enum):
        CLEAR_WRITE = auto()
        MAX_HOLD = auto()
        MIN_HOLD = auto()
        VIEW = auto()
        BLANK = auto()
        AVERAGE = auto()

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
        min_span: int,  # Note this is ignoring zero span
        max_span: int,
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
            or (max_span < min_span)
        ):
            raise ValueError
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.min_num_sweep_points = min_num_sweep_points
        self.max_num_sweep_points = max_num_sweep_points
        self.min_span = min_span
        self.max_span = max_span
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

    def _get_trace_data(self) -> list[tuple[float, float]]:
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

    def __exit__(self, *args, **kwargs):
        self.set_sweep_mode(self.SweepMode.CONTINUOUS)
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
            assert self.get_start_freq() == freq

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
            ValueError: If <span> is outside min_span -> max_span
            AssertionError: If readback value doesn't match requested
        """
        if not (self.min_span <= span_hz <= self.max_span):
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

    def trigger_sweep(self, timeout_s: Optional[float] = None) -> None:
        """
        Triggers a sweep and blocks until completion

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self._trigger_sweep()
        self.wait_until_op_complete(timeout_s)

    def get_trace_data(self) -> list[tuple[float, float]]:
        """
        Returns trace data

        Args:
            None

        Returns:
            list[tuple[float, float]:
                List of (frequency in Hz, power in y-axis units) tuples

        Raises:
            None
        """
        return self._get_trace_data()

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
            None
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
