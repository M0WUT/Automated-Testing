import logging

from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    DetectorMode,
    SpectrumAnalyser,
)
from AutomatedTesting.Instruments.TopLevel.BaseInstrument import BaseInstrument


class Rigol_DSA815TG(SpectrumAnalyser):
    def __init__(
        self,
        address,
        name="Rigol DSA815-TG",
    ):
        super().__init__(
            address,
            id="Rigol Technologies,DSA815,DSA8A163551099,00.01.09.00.07",
            name=name,
            minFreq=9e3,
            maxFreq=1.5e9,
            minSweepPoints=None,  # Fixed at 601
            maxSweepPoints=None,
            minSpan=0,
            maxSpan=1.5e9,
            hasPreamp=True,
        )

    def set_preamp_state(self, enabled: bool) -> None:
        if enabled:
            self._write(":POW:GAIN 1")
            logging.debug(f"{self.name} enabled RF preamp")
        else:
            self._write(":POW:GAIN 0")
            logging.debug(f"{self.name} disabled RF preamp")

        if self.verify:
            assert self.read_preamp_state() == enabled

    def read_preamp_state(self) -> bool:
        return self._query(":POW:GAIN?") == "1"

    def set_detector_mode(self, mode: DetectorMode) -> None:
        if mode == DetectorMode.RMS:
            self._write(":DET RMS")
        else:
            raise NotImplementedError

        if self.verify:
            assert self.read_detector_mode() == mode

    def read_detector_mode(self) -> DetectorMode:
        ret = self._query(":DET?")
        if ret == "RMS":
            return DetectorMode.RMS
        else:
            raise NotImplementedError

    def set_rbw(self, rbw: int) -> None:
        self._write(f":BAND {int(rbw)}")
        assert self.read_rbw() == rbw

    def read_rbw(self) -> float:
        return float(self._query(":BAND?"))

    def set_vbw_rbw_ratio(self, ratio: float) -> None:
        assert 0.000001 <= ratio <= 30000
        self._write(f":BAND:VID:RAT {ratio}")
        if self.verify:
            assert self.read_vbw_rbw_ratio() == ratio

    def read_vbw_rbw_ratio(self) -> float:
        return float(self._query(":BAND:VID:RAT?"))

    def get_trace_data(self) -> list[float]:
        self.trigger_measurement()
        data = self._query(":TRAC? TRACE1")
        # First field is length so discard it
        data = data.split(",")
        assert len(data) == 601
        data[0] = data[0].split(" ")[1]
        return [float(x) for x in data]
