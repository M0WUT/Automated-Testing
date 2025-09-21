# Standard impots
from logging import Logger

# Third party imports
from pyvisa import ResourceManager

# Local imports
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)
from AutomatedTesting.Misc.UsefulFunctions import get_key_from_dict_value


class SiglentSSA3032XPlus(SpectrumAnalyser):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: Logger,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logger=logger,
            min_freq=0,
            max_freq=int(3.2e9),
            min_num_sweep_points=751,
            max_num_sweep_points=751,
            min_sweep_time_s=450e-6,
            max_sweep_time_s=1500,
            min_span_hz=100,
            max_span_hz=int(3.2e9),
            min_attenuation_db=0,
            max_attenuation_db=51,
            has_preamp=True,
            supported_rbw=[
                1,
                3,
                10,
                30,
                100,
                300,
                1000,
                3000,
                10000,
                30000,
                100000,
                300000,
                1000000,
            ],
            supported_vbw=[
                1,
                3,
                10,
                30,
                100,
                300,
                1000,
                3000,
                10000,
                30000,
                100000,
                300000,
                1000000,
                3000000,
            ],
            max_num_traces=4,
            max_num_markers=8,
            supports_emi_measurements=True,
            supported_emi_rbw=[200, 9000, 120000, 1000000],
            **kwargs,
        )

        self._trace_str = {
            SpectrumAnalyser.TraceMode.CLEAR_WRITE: "WRIT",
            SpectrumAnalyser.TraceMode.MAX_HOLD: "MAXH",
            SpectrumAnalyser.TraceMode.MIN_HOLD: "MINH",
            SpectrumAnalyser.TraceMode.VIEW: "VIEW",
            SpectrumAnalyser.TraceMode.BLANK: "BLAN",
            SpectrumAnalyser.TraceMode.AVERAGE: "AVER",
        }

        self._filter_str = {
            SpectrumAnalyser.FilterType.NORMAL: "GAUSS",
            SpectrumAnalyser.FilterType.EMI: "EMI",
        }

        self._detector_str = {
            SpectrumAnalyser.DetectorType.POSITIVE_PEAK: "POS",
            SpectrumAnalyser.DetectorType.NEGATIVE_PEAK: "NEG",
            SpectrumAnalyser.DetectorType.AVERAGE: "AVER",
            SpectrumAnalyser.DetectorType.QUASI_PEAK: "QUAS",
        }

        self._y_axis_unit_str = {
            SpectrumAnalyser.YAxisUnits.DBM: "DBM",
            SpectrumAnalyser.YAxisUnits.DBMV: "DBMV",
            SpectrumAnalyser.YAxisUnits.DBUV: "DBUV",
            SpectrumAnalyser.YAxisUnits.VOLTS: "V",
            SpectrumAnalyser.YAxisUnits.WATTS: "W",
        }

    #####################################
    # Override BaseInstrument functions #
    #####################################
    def set_local_control(self):
        self._write("SYST:LOC")

    def initialise(self):
        super().initialise()
        self._write(":SWE:MODE SWE")

    #########################################
    # Functions from SpectrumAnalyser class #
    #########################################

    def _set_start_freq(self, freq_hz: float):
        self._write(f":FREQ:STAR {freq_hz}")

    def _get_start_freq(self) -> float:
        return float(self._query(":FREQ:STAR?"))

    def _set_stop_freq(self, freq_hz: float):
        self._write(f":FREQ:STOP {freq_hz}")

    def _get_stop_freq(self) -> float:
        return float(self._query(":FREQ:STOP?"))

    def _set_centre_freq(self, freq_hz: float):
        self._write(f":FREQ:CENT {freq_hz}")

    def _get_centre_freq(self) -> float:
        return float(self._query(":FREQ:CENT?"))

    def _set_span(self, span_hz: float):
        self._write(f":FREQ:SPAN {span_hz}")

    def _get_span(self) -> float:
        return float(self._query(":FREQ:SPAN?"))

    def _set_zero_span_enabled_state(self, enabled: bool) -> None:
        if enabled:
            self._write(":FREQ:SPAN:ZERO")
        else:
            self.set_span(self.min_span_hz)

    def _get_zero_span_enabled_state(self) -> bool:
        return self.get_span() == 0

    def _set_filter_type(self, filter_type: SpectrumAnalyser.FilterType) -> None:
        # Changing the filter type auto-adjusts the units for the y-axis
        # and sweep type. Don't want things happening magically
        old_units = self.get_y_axis_units()
        self._write(f":FILT:TYPE {self._filter_str[filter_type]}")
        self.set_y_axis_units(old_units)
        self._write(":SWE:MODE SWE")

    def _get_filter_type(self) -> SpectrumAnalyser.FilterType:
        response = self._query(":FILT:TYPE?")
        return get_key_from_dict_value(self._filter_str, response)

    def _set_rbw(self, rbw_hz: float) -> None:
        self._write(f":BWID {rbw_hz}")

    def _get_rbw(self) -> float:
        return float(self._query(":BWID?"))

    def _set_vbw(self, vbw_hz: float) -> None:
        self._write(f":BWID:VID {vbw_hz}")

    def _get_vbw(self) -> float:
        return float(self._query(":BWID:VID?"))

    def _set_sweep_mode(self, mode: SpectrumAnalyser.SweepMode) -> None:
        self._write(f":INIT:CONT {'1' if mode == self.SweepMode.CONTINUOUS else '0'}")

    def _get_sweep_mode(self) -> SpectrumAnalyser.SweepMode:
        return (
            SpectrumAnalyser.SweepMode.CONTINUOUS
            if self._query(":INIT:CONT?") == "1"
            else SpectrumAnalyser.SweepMode.SINGLE
        )

    def _set_num_sweep_points(self, num_points: int) -> None:
        pass  # Fixed at 751 points

    def _get_num_sweep_points(self) -> int:
        return 751

    def _set_input_attenuation(self, attenuation_db: float) -> None:
        self._write(f":POW:ATT {attenuation_db}")

    def _get_input_attenuation(self) -> float:
        return float(self._query(":POW:ATT?"))

    def _set_ref_level(self, ref_level) -> None:
        self._write(f":DISP:WIND:TRAC:Y:RLEV {ref_level}")

    def _get_ref_level(self) -> float:
        return float(self._query(":DISP:WIND:TRAC:Y:RLEV?"))

    def _trigger_sweep(self) -> None:
        self._write(":INIT:IMM")

    def _get_trace_data(self) -> list[float]:
        return [float(x) for x in self._query(":TRAC:DATA?").split(",")]

    def _set_marker_enabled_state(self, marker_num: int, enabled: bool) -> None:
        self._write(f":CALC:MARK{marker_num}:STAT {'ON' if enabled else 'OFF'}")

    def _get_marker_enabled_state(self, marker_num: int) -> bool:
        return self._query(f":CALC:MARK{marker_num}:STAT?") == "1"

    def _set_marker_freq(
        self,
        marker_num: int,
        freq_hz: float,
    ) -> None:
        self._write(f":CALC:MARK{marker_num}:X {freq_hz}")

    def _get_marker_freq(self, marker_num: int) -> float:
        return float(self._query(f":CALC:MARK{marker_num}:X?"))

    def _measure_marker_power(self, marker_num: int) -> float:
        return float(self._query(f":CALC:MARK{marker_num}:Y?"))

    def _set_trace_mode(self, trace_num: int, mode: SpectrumAnalyser.TraceMode) -> None:
        self._write(f":TRAC{trace_num}:MODE {self._trace_str[mode]}")

    def _get_trace_mode(self, trace_num: int) -> SpectrumAnalyser.TraceMode:
        response = self._query(f":TRAC{trace_num}:MODE?")
        return get_key_from_dict_value(self._trace_str, response)

    def _set_detector_type(
        self, trace_num: int, detector_type: SpectrumAnalyser.DetectorType
    ) -> None:
        self._write(f":DET:TRAC{trace_num} {self._detector_str[detector_type]}")

    def _get_detector_type(self, trace_num: int) -> SpectrumAnalyser.DetectorType:
        response = self._query(f":DET:TRAC{trace_num}?")
        return get_key_from_dict_value(self._detector_str, response)

    def _set_y_axis_units(self, units: SpectrumAnalyser.YAxisUnits) -> None:
        self._write(f":UNIT:POW {self._y_axis_unit_str[units]}")

    def _get_y_axis_units(self) -> SpectrumAnalyser.YAxisUnits:
        response = self._query(":UNIT:POW?")
        return get_key_from_dict_value(self._y_axis_unit_str, response)

    def _set_preamp_enabled_state(self, enabled: bool):
        self._write(f":POW:GAIN {'ON' if enabled else 'OFF'}")

    def _get_preamp_enabled_state(self) -> bool:
        return self._query(":POW:GAIN?") == "1"

    def _set_sweep_time(self, sweep_time_s: float) -> None:
        self._write(f":SWE:TIME {sweep_time_s}")

    def _get_sweep_time(self) -> float:
        return float(self._query(":SWE:TIME?"))

    def _set_sweep_time_auto_enabled_state(self, enabled: bool) -> None:
        self._write(f":SWE:TIME:AUTO {'ON' if enabled else 'OFF'}")

    def _get_sweep_time_auto_enabled_state(self) -> bool:
        return self._query(":SWE:TIME:AUTO?") == "1"
