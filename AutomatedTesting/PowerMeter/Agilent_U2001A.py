from AutomatedTesting.PowerMeter.PowerMeter import PowerMeter
import logging
from time import sleep

class Agilent_U2001A(PowerMeter):
    def __init__(self, address, name="Agilent U2001A"):
        super().__init__(
            address,
            id="Agilent Technologies,U2001A,MY53150007,A1.03.05",
            name=name,
            minFreq=10e6,
            maxFreq=6e9,
            timeout=500
        )

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)
        self._write("INIT:CONT ON")

    def internal_zero(self):
        """
        Zeros power meter. Does not require external intervation
        i.e. removal of RF signal / disconnection of meter

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self._write("CAL:ZERO:TYPE INT")
        self._zero()
        logging.info(f"{self.name} zeroed internally")

    def external_zero(self):
        """
        Zeros power meter. Does require external intervation
        i.e. removal of RF signal / disconnection of meter

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        logging.debug(
            f"{self.name}: Waiting for user intervention on zeroing"
        )
        input(
            f"Please disconnect input from {self.name} and press "
            "any key to continue..."
        )
        self._write("CAL:ZERO:TYPE EXT")
        self._zero()
        logging.info(f"{self.name} zeroed externally")
        logging.debug(
            f"{self.name}: Waiting for user intervention on zeroing"
        )
        input(
            f"Please reconnect input to {self.name} and press "
            "any key to continue..."
        )

    def _zero(self):
        """
        Performs the zeroing of the meter with whatever source
        (internal or external) is already set

        Args:
            None

        Returns:
            None

        Raises:
            AssertionError: if cal fails
        """
        logging.info(
            f"Calibrating {self.name}. This takes a while..."
        )
        x = self.dev.timeout
        self.dev.timeout = 0
        result = self._query("CAL?")
        self.dev.timeout = x
        if result != '0':
            logging.error(
                f"Calibration of {self.name} failed. Return code: {result}"
            )
            assert False

    def set_freq(self, freq):
        """
        Informs power meter of frequency to allow it to
        compensate

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        raise NotImplementedError  # pragma: no cover

    def measure_power(self, freq=None):
        """
        Measures RF Power

        Args:
            freq (float): Frequency in Hz to allow for reading correction

        Returns:
            float: Measured power in dBm

        Raises:
            None
        """

        timeout = self.dev.timeout
        self.dev.timeout = 0
        x = float(self._query("MEAS? DEF, 3, (@1)"))
        self.dev.timeout = timeout
        return self._correct_power(x, freq)

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
        errors = self._query("SYSTem:ERRor?").strip()
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
