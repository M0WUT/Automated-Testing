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
        min_sweep_points: int,
        max_sweep_points: int,
        min_span: int,  # Note this is ignoring zero span
        max_span: int,
        min_attenuation: float,
        max_attenuation: float,
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
            or (max_sweep_points < min_sweep_points)
            or (max_span < min_span)
        ):
            raise ValueError
        self.min_freq = min_freq
        self.max_freq = max_freq
        self.min_sweep_points = min_sweep_points
        self.max_sweep_points = max_sweep_points
        self.min_span = min_span
        self.max_span = max_span
        self.min_attenuation = min_attenuation
        self.max_attenuation = max_attenuation
        self.has_preamp = has_preamp
        self.supported_rbw = supported_rbw
        self.supported_vbw = supported_vbw
        self.max_num_traces = max_num_traces
        self.max_num_markers = max_num_markers
        self.supports_emi_measurements = supports_emi_measurements
        if self.supports_emi_measurements:
            assert supported_emi_rbw is not None
        self.supported_emi_rbw = supported_emi_rbw

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

    def enable_marker(self, marker_number: int = 1):
        self.set_marker_enabled_state(marker_number, True)

    def disable_marker(self, marker_number: int = 1):
        self.set_marker_enabled_state(marker_number, False)

    def measure_power(self, freq: float, marker_number: int = 1) -> float:
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
        if marker_number > self.max_num_markers:
            raise ValueError
        if not self.get_marker_enabled_state(marker_number):
            self.enable_marker(marker_number)
        self.set_marker_frequency(freq, marker_number)
        return self.measure_marker_power(marker_number)

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

    def set_rbw(self, rbw: float, filter_type: FilterType = FilterType.NORMAL):
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
            if rbw not in self.supported_emi_rbw:
                raise ValueError
        else:
            if rbw not in self.supported_rbw:
                raise ValueError

        self._set_filter_type(filter_type)
        self._set_rbw(rbw)
        if self.verify:
            assert self.get_filter_type() == filter_type
            assert self.get_rbw() == rbw

    ########################################################
    # Methods that must be implemented for each instrument #
    ########################################################

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
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_stop_freq(self, freq: float):
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
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_centre_freq(self, freq: float):
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
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_span(self, span: float):
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
        raise NotImplementedError  # pragma: no cover

    def set_zero_span(self):
        """
        Puts spectrum analyser in zero span mode

        Args:
            None

        Returns:
            None

        Raises:
            AssertionError: If readback span isn't zero
        """
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def _set_rbw(self, rbw: float):
        """
        Low-level function that purely handles the transaction with the
        spectrum analyser. All validation and error checking is handled
        in the set_rbw function that calls this one, allowing automatic
        implementation for all spectrum analyser that inherit from this
        class

        Args:
            rbw (float): RBW in Hz

        Returns:
            None

        Raises:
            None

        """
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_vbw(self, vbw: float):
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
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_vbw_rbw_ratio(self, ratio: float):
        """
        Sets Video Bandwidth to Resolution Bandwidth ratio

        Args:
            ratio (float): desired VBW:RBW ratio

        Returns:
            None

        Raises:
            ValueError: If requested value isn't in supported list
            AssertionError: If readback value doesn't match requested
        """
        raise NotImplementedError  # pragma: no cover

    def get_vbw_rbw_ratio(self) -> float:
        """
        Reads Video Bandwidth to Resolution Bandwidth ratio

        Args:
            None

        Returns:
            float: ratio

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_sweep_points(self, num_points: int):
        """
        Sets number of sweep points
        Args:
            num_points (int): number of points in the sweep

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested
        """
        raise NotImplementedError  # pragma: no cover

    def get_sweep_points(self) -> int:
        """
        Reads number of sweep points

        Args:
            None

        Returns:
            int: number of sweep points

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_input_attenuation(self, attenuation: float):
        """
        Sets input attenuation

        Args:
            attenuation (float): attenuation in dB

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested value
        """
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def set_ref_level(self, level: float):
        """
        Sets Reference Level

        Args:
            level (float): reference level in dBm

        Returns:
            None

        Raises:
            AssertionError: If readback value doesn't match requested value
        """
        raise NotImplementedError  # pragma: no cover

    def get_ref_level(self) -> float:
        """
        Reads input attenuation

        Args:
            None

        Returns:
            float: Reference Level in dBm

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def get_trace_data(self) -> list[tuple[float, float]]:
        """
        Returns trace data

        Args:
            None

        Returns:
            List[Tuple[float, float]: List of (frequency in Hz, power in dBm) tuples

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_marker_enabled_state(self, marker_num: int = 1, enabled: bool = False):
        """
        En/disables a marker

        Args:
            marker_number (int): which marker to en/disable
            enabled (bool): Enable marker if True, Disable if False

        Returns:
            None

        Raises:
            ValueError: If <marker_number> is invalid
            AssertionError: If readback state doesn't match requested
        """
        raise NotImplementedError  # pragma: no cover

    def get_marker_enabled_state(self, marker_num: int = 1) -> bool:
        """
        Returns state of a particular marker

        Args:
            marker_number (int): which marker to get the state of

        Returns:
            bool: True if the marker is enabled

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def set_marker_frequency(self, freq: float, marker_number: int = 1):
        """
        Sets marker to a particular frequency

        Args:
            freq (float): Frequency to set the marker to
            marker_number (int): which marker to move

        Returns:
            None

        Raises:
            ValueError: If <marker_number> is invalid
            AssertionError: If readback frequency doesn't match requested
        """
        raise NotImplementedError  # pragma: no cover

    def get_marker_frequency(self, marker_number: int = 1) -> float:
        """
        Reads frequency a particular marker is set to

        Args:
            marker_number (int): which marker to query

        Returns:
            float: marker frequency in Hz

        Raises:
            ValueError: If <marker_number> is invalid
        """
        raise NotImplementedError  # pragma: no cover

    def measure_marker_power(self, marker_number: int = 1) -> float:
        """
        Reads power for a a particular marker

        Args:
            marker_number (int): which marker to query

        Returns:
            float: marker power in dBm

        Raises:
            ValueError: If <marker_number> is invalid
        """
        raise NotImplementedError  # pragma: no cover

    def trigger_sweep(self):
        """
        Triggers a sweep and blocks until completion

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

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
        raise NotImplementedError  # pragma: no cover

    def _set_filter_type(self, filter_type: FilterType):
        raise NotImplementedError  # pragma: no cover

    def get_filter_type(self) -> FilterType:
        raise NotImplementedError  # pragma: no cover
