import logging
from time import sleep

from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser
from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq


class Agilent_E4407B(SpectrumAnalyser):
    def __init__(
        self,
        address,
        name="Agilent E4407B",
        enableDisplay=False,
        enableAutoAlign=True,
        enableLowPhaseNoise=False,
    ):
        super().__init__(
            address,
            id="Hewlett-Packard, E4407B, SG44210622, A.14.01",
            name=name,
            minFreq=9e3,
            maxFreq=26.5e9,
            timeout=20000,
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

        self._write(":INIT:CONT ON")
        super().cleanup()

    def trigger_measurement(self):
        self.lock.acquire()
        try:
            self._write(":INIT:IMM", acquireLock=False)
            while self._query("*OPC?", acquireLock=False) == "1":
                logging.critical("SLEEPING")
                sleep(1)
        finally:
            self.lock.release()

    def set_centre_freq(self, freq):
        """
        Sets centre frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        assert 0 < freq < 26.5e9
        self._write(f"FREQ:CENT {readable_freq(freq)}")
        logging.debug(f"{self.name} set centre frequency to {readable_freq(freq)}")

    def set_start_freq(self, freq):
        """
        Sets start frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        assert 0 < freq < 26.5e9
        self._write(f"FREQ:STAR {readable_freq(freq)}")
        logging.debug(f"{self.name} set start frequency to {readable_freq(freq)}")

    def set_stop_freq(self, freq):
        """
        Sets stop frequency

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        assert 0 < freq < 26.5e9
        self._write(f"FREQ:STOP {readable_freq(freq)}")
        logging.debug(f"{self.name} set stop frequency to {readable_freq(freq)}")

    def set_span(self, freq):
        """
        Sets x axis span

        Args:
           freq (float): Frequency in Hz

        Returns:
            None

        Raises:
            None
        """
        assert 100 < freq < 26.5e9 or freq == 0
        self._write(f"FREQ:SPAN {readable_freq(freq)}")
        logging.debug(f"{self.name} set span to {readable_freq(freq)}")

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
        if isinstance(rbw, int):
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
        if isinstance(vbw, int):
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

    def set_sweep_points(self, numPoints):
        """
        Sets Number of Points in sweep

        Args:
           vbw (float): VBW in Hz, or "auto"

        Returns:
            None

        Raises:
            None
        """
        assert 101 <= numPoints <= 8192
        self._write(f":SWE:POIN {numPoints}")
        logging.debug(f"{self.name} set number of points to {numPoints}")

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
            logging.debug(f"{self.name} set sweep time to {sweepTime}ms")

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

    def get_trace_data(self):
        traceData = []
        self.trigger_measurement()

        # First number is how many digits are in length field
        data = self._query_raw(":TRAC? TRACE1")
        lengthOfLength = int(chr(data[1]))
        length = 0
        lengthBytes = data[2 : (2 + lengthOfLength)]
        for x in lengthBytes:
            length = length * 10 + int(chr(x))

        length = int(length / 4)  # 32 bit values so 4 bytes per value
        index = 2 + lengthOfLength  # First index worth reading

        for x in range(length):
            dataPoint = data[index : index + 4]
            traceData.append(
                int.from_bytes(dataPoint, byteorder="big", signed=True) / 1000
            )
            index += 4
        return traceData

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
