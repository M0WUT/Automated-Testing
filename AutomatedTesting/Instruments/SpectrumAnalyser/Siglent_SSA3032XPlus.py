from logging import Logger
from typing import List, Tuple

from numpy import linspace
from pyvisa import ResourceManager

from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import \
    SpectrumAnalyser


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
            max_freq=3.2e9,
            min_sweep_points=751,
            max_sweep_points=751,
            min_span=100,
            max_span=3.2e9,
            min_attenuation=0,
            max_attenuation=51,
            has_preamp=True,
            **kwargs,
        )
        self.supported_rbw = [
            1,
            3,
            10,
            30,
            100,
            300,
            1000,
            3000,
            10e3,
            30e3,
            100e3,
            300e3,
            1e6,
        ]
        self.supported_vbw = [
            1,
            3,
            10,
            30,
            100,
            300,
            1000,
            3000,
            10e3,
            30e3,
            100e3,
            300e3,
            1e6,
        ]

    def get_instrument_errors(self) -> List[Tuple[int, str]]:
        return []

    def set_start_freq(self, freq: float):
        if not (self.min_freq <= freq <= self.max_freq):
            raise ValueError
        self._write(f":FREQ:STAR {freq}")
        if self.verify:
            assert self.get_start_freq() == freq

    def get_start_freq(self) -> float:
        return float(self._query(":FREQ:STAR?"))

    def set_stop_freq(self, freq: float):
        if not (self.min_freq <= freq <= self.max_freq):
            raise ValueError
        self._write(f":FREQ:STOP {freq}")
        if self.verify:
            assert self.get_stop_freq() == freq

    def get_stop_freq(self) -> float:
        return float(self._query(":FREQ:STOP?"))

    def set_centre_freq(self, freq: float):
        if not (self.min_freq <= freq <= self.max_freq):
            raise ValueError
        self._write(f":FREQ:CENT {freq}")
        if self.verify:
            assert self.get_centre_freq() == freq

    def get_centre_freq(self) -> float:
        return float(self._query(":FREQ:CENT?"))

    def set_span(self, span: float):
        if not (self.min_span <= span <= self.max_span):
            if span == 0:
                self.logger.warning(
                    "Attempted to set zero span without using zero span function"
                )
            raise ValueError
        self._write(f":FREQ:SPAN {span}")
        if self.verify:
            assert self.get_span() == span

    def set_zero_span(self):
        self._write(":FREQ:SPAN:ZERO")
        if self.verify:
            assert self.get_span() == 0

    def get_span(self) -> float:
        return float(self._query(":FREQ:SPAN?"))

    def set_rbw(self, rbw: float):
        if rbw not in self.supported_rbw:
            raise ValueError
        self._write(f":BWID {rbw}")
        if self.verify:
            assert self.get_rbw() == rbw

    def get_rbw(self) -> float:
        return float(self._query(":BWID?"))

    def set_vbw(self, vbw: float):
        if vbw not in self.supported_vbw:
            raise ValueError
        self._write(f":BWID:VID {vbw}")
        if self.verify:
            assert self.get_vbw() == vbw

    def get_vbw(self) -> float:
        return float(self._query(":BWID:VID?"))

    def set_vbw_rbw_ratio(self, ratio: float):
        self._write(f":BWID:VID:RAT {ratio}")
        if self.verify:
            assert self.get_vbw_rbw_ratio() == ratio

    def get_vbw_rbw_ratio(self) -> float:
        return float(self._query(":BWID:VID:RAT?"))

    def set_sweep_mode(
        self,
        mode: SpectrumAnalyser.SweepMode = SpectrumAnalyser.SweepMode.CONTINUOUS,
    ):
        self._write(
            f":INIT:CONT {'1' if mode == self.SweepMode.CONTINUOUS else '0'}"
        )
        if self.verify:
            assert self.get_sweep_mode() == mode

    def get_sweep_mode(self) -> SpectrumAnalyser.SweepMode:
        return (
            SpectrumAnalyser.SweepMode.CONTINUOUS
            if self._query(":INIT:CONT?") == "1"
            else SpectrumAnalyser.SweepMode.SINGLE
        )

    def set_sweep_points(self, num_points: int):
        # Fixed 751 point operation
        if num_points != 751:
            raise ValueError

    def get_sweep_points(self) -> int:
        # Fixed 751 point and querying this causes it to hang
        return 751

    def set_input_attenuation(self, attenuation: float):
        if not (self.min_attenuation <= attenuation <= self.max_attenuation):
            raise ValueError
        self._write(f":POW:ATT {attenuation}")
        if self.verify:
            assert self.get_input_attenuation() == attenuation

    def get_input_attenuation(self) -> float:
        return float(self._query(":POW:ATT?"))

    def set_ref_level(self, level: float):
        self._write(f":DISP:WIND:TRAC:Y:RLEV {level}")
        if self.verify:
            assert self.get_ref_level() == level

    def get_ref_level(self) -> float:
        return float(self._query(":DISP:WIND:TRAC:Y:RLEV?"))

    def get_trace_data(self) -> list[tuple[float, float]]:
        data = self._query(":TRAC:DATA?")
        powers = [float(x) for x in data.split(",")]
        freqs = linspace(
            self.get_start_freq(), self.get_stop_freq(), self.get_sweep_points()
        )
        return list(zip(freqs, powers))

    def set_marker_state(self, marker_number: int = 1, enabled: bool = False):
        if marker_number > self.max_markers:
            raise ValueError
        self._write(
            f":CALC:MARK{marker_number}:STAT {'ON' if enabled else 'OFF'}"
        )
        if self.verify:
            assert self.get_marker_state(marker_number) == enabled

    def get_marker_state(self, marker_number: int = 1) -> bool:
        if marker_number > self.max_markers:
            raise ValueError
        return self._query(f":CALC:MARK{marker_number}:STAT?") == "1"

    def set_marker_frequency(self, freq: float, marker_number: int = 1):
        if marker_number > self.max_markers:
            raise ValueError
        self._write(f":CALC:MARK{marker_number}:X {freq}")
        if self.verify:
            assert self.get_marker_frequency(marker_number) == freq

    def get_marker_frequency(self, marker_number: int = 1) -> float:
        if marker_number > self.max_markers:
            raise ValueError
        return float(self._query(f":CALC:MARK{marker_number}:X?"))

    def measure_marker_power(self, marker_number: int = 1) -> float:
        if marker_number > self.max_markers:
            raise ValueError
        return float(self._query(f":CALC:MARK{marker_number}:Y?"))

    def trigger_sweep(self):
        self._write(":INIT:IMM")
        self.wait_until_op_complete()
