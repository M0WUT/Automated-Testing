from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser
import logging
from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq


class Agilent_E4407B(SpectrumAnalyser):
    def __init__(
        self, address, name="Agilent E4407B",
        enableDisplay=False, enableAutoAlign=True,
        enableLowPhaseNoise=False
    ):
        super().__init__(
            address,
            id="Hewlett-Packard, E4407B, SG44210622, A.14.01",
            name=name,
            minFreq=9e3,
            maxFreq=26.5e9,
            timeout=10000
        )
        self.enableDisplay = enableDisplay
        self.enableAutoAlign = enableAutoAlign
        self.enableLowPhaseNoise = enableLowPhaseNoise

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)
        if self.enableDisplay is False:
            self._write(":DISP:ENAB OFF")

        if self.enableAutoAlign is False:
            self._write(":CAL:AUTO OFF")

        if self.enableLowPhaseNoise is False:
            self._write(":FREQ:SYNT 2")

        self._write(":INIT:CONT OFF")

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
        errorList = []
        errors = self._query(":SYST:ERR?").strip()
        if(errors != '+0,"No error"'):
            errorStrings = errors.split('",')

            for x in errorStrings:
                errorCode, errorMessage = x.split(',"')
                # Last item in list isn't comma terminated so need
                # to manually remove trailing speech marks
                if(errorMessage[-1:] == '"'):
                    errorMessage = errorMessage[:-1]
                errorList.append((int(errorCode), errorMessage))
        return errorList

    def cleanup(self):
        if self.enableDisplay is False:
            self._write(":DISP:ENAB ON")

        if self.enableAutoAlign is False:
            self._write(":CAL:AUTO ON")

        if self.enableLowPhaseNoise is False:
            self._write(":FREQ:SYNT 3")

        self._write(":INIT:CONT ON")

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
        logging.debug(
            f"{self.name} set centre frequency to {readable_freq(freq)}"
        )

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
        logging.debug(
            f"{self.name} set start frequency to {readable_freq(freq)}"
        )

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
        logging.debug(
            f"{self.name} set stop frequency to {readable_freq(freq)}"
        )

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
        logging.debug(
            f"{self.name} set span to {readable_freq(freq)}"
        )

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
            logging.debug(
               f"{self.name} set RBW to {readable_freq(rbw)}"
            )
        else:
            if rbw.lower() == "auto":
                self._write("BAND:AUTO ON")
                logging.debug(
                   f"{self.name} set RBW to auto"
                )
            else:
                logging.error(
                    f"Unable to set RBW of {self.name} to \"{rbw}\""
                )
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
            logging.debug(
               f"{self.name} set VBW to {readable_freq(vbw)}"
            )
        else:
            if vbw.lower() == "auto":
                self._write("BAND:VID:AUTO ON")
                logging.debug(
                    f"{self.name} set VBW to auto"
                )
            else:
                logging.error(
                    f"Unable to set VBW of {self.name} to "
                    f"\"{readable_freq(vbw)}\""
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
        logging.debug(
            f"{self.name} set number of points to {numPoints}"
        )

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
        self._write(f":SWE:TIME {sweepTime}ms")
        logging.debug(
            f"{self.name} set sweep time to {sweepTime}ms"
        )

    def measure_power(self, freq):
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
        self.set_rbw(1000)
        self.set_sweep_time(4)
        self.set_sweep_points(101)

        self.set_centre_freq(freq)
        self._write(":INIT:IMM;*WAI;:CALC:MARK1:MAX")
        return self._correct_power(
            float(self._query(":CALC:MARK1:Y?")),
            freq
        )

    def get_trace_data(self):
        traceData = []
        self._write(":INIT:IMM;*WAI;")

        # First number is how many digits are in length field
        data = self._query_raw(
            ":TRAC? TRACE1"
        )
        lengthOfLength = int(chr(data[1]))
        length = 0
        lengthhBytes = data[2:(2+lengthOfLength)]
        for x in lengthhBytes:
            length = length * 10 + int(chr(x))

        length = int(length / 4)  # 32 bit values so 4 bytes per value
        index = 2 + lengthOfLength  # First index worth reading

        for x in range(length):
            dataPoint = data[index:index + 4]
            traceData.append(
                int.from_bytes(
                    dataPoint, byteorder="big", signed=True
                    ) / 1000
                )
            index += 4
        return traceData
