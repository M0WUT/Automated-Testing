import logging
from time import sleep

from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    DetectorMode, SpectrumAnalyser)
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

        self.set_input_attenuator(10)

        self._write(":INIT:CONT ON")
        super().cleanup()

    def trigger_measurement(self):
        self.lock.acquire()
        try:
            self._write(":INIT:IMM", acquireLock=False)
            while self._query("*OPC?", acquireLock=False) == "1":
                sleep(1)
        finally:
            self.lock.release()

    def set_rbw(self, rbw):
        """
        Sets Resolution Bandwidth

        Args:
           rbw (int): RBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        if isinstance(rbw, (int, float)):
            assert 1 <= rbw < 5e6
            self._write(f"BAND {readable_freq(rbw)}")
            logging.debug(f"{self.name} set RBW to {readable_freq(rbw)}")
        else:
            if rbw.lower() == "auto":
                self._write("BAND:AUTO ON")
                logging.debug(f"{self.name} set RBW to auto")
            else:
                logging.error(f'Unable to set RBW of {self.name} to "{rbw}"')
                raise ValueError

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
        if isinstance(vbw, (int, float)):
            assert 1 <= vbw < 5e6
            self._write(f"BAND:VID {readable_freq(vbw)}")
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

    def measure_power_zero_span(self, freq):
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
        self.set_span(0)
        self.set_sweep_points(101)
        self.set_sweep_time(10)

        self.set_centre_freq(freq)
        self.trigger_measurement()
        self._write(":CALC:MARK:MAX")
        measuredPower = float(self._query(":CALC:MARK:Y?").strip())
        return measuredPower

    def measure_power_marker(self, freq):
        """
        Measures RF Power using a marker

        Args:
            freq (float): Frequency of measured signal

        Returns:
            float: Measured power in dBm

        Raises:
            None
        """
        self._write(":CALC:MARK:STAT ON")
        self._write(":CALC:MARK:MODE POS")
        self._write(f":CALC:MARK:X {int(freq)}")
        measuredPower = float(self._query(":CALC:MARK:Y?"))
        return measuredPower

    def set_ref_level(self, refLevel: int) -> None:
        """
        Sets reference level

        Args:
            refLevel: new reference level in dBm

        Returns:
            None
        """
        self._write(f":DISP:WIND:TRAC:Y:RLEV {refLevel}")

    def set_input_attenuator(self, attenuation: int) -> None:
        self._write(f"POW:ATT {attenuation}")

    def set_ampl_scale(self, dbPerDiv: float) -> None:
        """
        Sets y-axis scale in dB/div

        Args:
            dbPerDiv: Requested number of dB per division

        Returns:
            None
        """
        assert 0.1 <= dbPerDiv <= 20
        self._write(f"DISP:WIND:TRAC:Y:PDIV {round(dbPerDiv, 1)}")

    def get_trace_data(self) -> list[float]:
        self.trigger_measurement()
        data = self._query(":TRAC? TRACE1")
        return [float(x) for x in data.split(",")]

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

    def set_detector_mode(self, mode: DetectorMode):
        if mode == DetectorMode.RMS:
            self._write(":DET RMS")
        else:
            raise NotImplementedError
