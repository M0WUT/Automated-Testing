import logging
from time import sleep
from typing import Union

from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    DetectorMode,
    SpectrumAnalyser,
)
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq


class Agilent_E4407B(SpectrumAnalyser):
    def __init__(
        self,
        address,
        name="Agilent E4407B",
        enableDisplay=False,
        enableAutoAlign=True,
        enableLowPhaseNoise=True,
    ):
        super().__init__(
            address,
            id="Hewlett-Packard, E4407B, SG44210622, A.14.01",
            name=name,
            minFreq=9e3,
            maxFreq=26.5e9,
            minSweepPoints=101,
            maxSweepPoints=8192,
            minSpan=100,
            maxSpan=26.5e9,
            hasPreamp=False,
            timeout=None,
        )
        self.enableDisplay = enableDisplay
        self.enableAutoAlign = enableAutoAlign
        self.enableLowPhaseNoise = enableLowPhaseNoise

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)
        if not self.enableDisplay:
            self._write(":DISP:ENAB OFF")

        if not self.enableAutoAlign:
            self._write(":CAL:AUTO OFF")

        if not self.enableLowPhaseNoise:
            self._write(":FREQ:SYNT 2")

        self._write(":INIT:CONT OFF")

    def cleanup(self):
        if not self.enableDisplay:
            self._write(":DISP:ENAB ON")

        if not self.enableAutoAlign:
            self._write(":CAL:AUTO ON")

        if not self.enableLowPhaseNoise:
            self._write(":FREQ:SYNT 3")

        super().cleanup()

    def read_detector_mode(self) -> DetectorMode:
        ret = self._query(":DET?")
        if ret == "AVER":
            return DetectorMode.RMS
        else:
            raise NotImplementedError(ret)

    def set_rbw(self, rbw):
        if isinstance(rbw, (int, float)):
            assert 1 <= rbw < 5e6
            self._write(f"BAND {readable_freq(rbw)}")
            if self.verify:
                assert self.read_rbw() == rbw
            logging.debug(f"{self.name} set RBW to {readable_freq(rbw)}")
        else:
            if rbw.lower() == "auto":
                self._write("BAND:AUTO ON")
                logging.debug(f"{self.name} set RBW to auto")
            else:
                logging.error(f'Unable to set RBW of {self.name} to "{rbw}"')
                raise ValueError

    def read_rbw(self) -> float:
        return float(self._query("BAND?"))

    def set_vbw(self, vbw):
        if isinstance(vbw, (int, float)):
            assert 1 <= vbw < 5e6
            self._write(f"BAND:VID {readable_freq(vbw)}")
            if self.verify:
                assert self.read_vbw() == vbw
            logging.debug(f"{self.name} set VBW to {readable_freq(vbw)}")
        else:
            if vbw.lower() == "auto":
                self._write("BAND:VID:AUTO ON")
                logging.debug(f"{self.name} set VBW to auto")
            else:
                logging.error(
                    f"Unable to set VBW of {self.name} to " f'"{readable_freq(vbw)}"'
                )
                raise ValueError

    def read_vbw(self) -> float:
        return float(self._query("BAND:VID?"))

    def set_vbw_rbw_ratio(self, ratio: float) -> None:
        if not 0.00001 <= ratio <= 3e6:
            raise ValueError

        self._write(f":BAND:VID:RAT {ratio}")

        if self.verify:
            assert self.read_vbw_rbw_ratio() == ratio

        logging.debug(f"{self.name} set VBW:RBW ratio to {ratio}")

    def read_vbw_rbw_ratio(self) -> float:
        return float(self._query("BAND:VID:RAT?"))

    def measure_power_marker(self, freq):
        self._write(":CALC:MARK:STAT ON")
        self._write(":CALC:MARK:MODE POS")
        self._write(f":CALC:MARK:X {int(freq)}")
        return float(self._query(":CALC:MARK:Y?"))

    def measure_power_zero_span(self, freq):
        self.set_span(0)
        self.set_sweep_points(101)
        self.set_sweep_time(10)

        self.set_centre_freq(freq)
        self.trigger_measurement()
        self._write(":CALC:MARK:MAX")
        return float(self._query(":CALC:MARK:Y?").strip())

    def enable_averaging(self, numAverages: int = 10):
        if numAverages:
            self._write(":AVER:STAT ON")
            self._write(f":AVER:COUN {int(numAverages)}")
            logging.debug(f"{self.name} set number of averages to {numAverages}")
        else:
            self._write(":AVER:STAT OFF")
            logging.debug(f"{self.name} disabled averaging")

    def disable_averaging(self):
        self.enable_averaging(0)

    def read_instrument_errors(self):
        """
        Checks whole instrument for errors

        Args:
            None

        Returns:
            list(Tuple): Pairs of (status code, error message)

        Raises:
            None
        """
        return []
