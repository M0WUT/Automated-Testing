from logging import Logger

from AutomatedTesting.Instruments.PowerMeter.PowerMeter import PowerMeter
from AutomatedTesting.UsefulFunctions import readable_freq
from pyvisa import ResourceManager


class Agilent_U2001A(PowerMeter):
    def __init__(
        self,
        resourceManager: ResourceManager,
        visaAddress: str,
        instrumentName: str,
        expectedIdnResponse: str,
        verify: bool,
        logger: Logger,
        **kwargs,
    ):
        super().__init__(
            resourceManager=resourceManager,
            visaAddress=visaAddress,
            instrumentName=instrumentName,
            expectedIdnResponse=expectedIdnResponse,
            verify=verify,
            logger=logger,
            minFreq=10e6,
            maxFreq=6e9,
            timeout=500,
            **kwargs,
        )

    def __enter__(self):
        super().__enter__()
        self._write("INIT:CONT ON")
        return self

    def internal_zero(self):
        self._write("CAL:ZERO:TYPE INT")
        self._zero()
        self.logger.info(f"{self.name} zeroed internally")

    def external_zero(self):
        self.logger.debug(
            f"{self.name}: Waiting for user intervention on zeroing"
        )
        input(
            f"Please disconnect input from {self.name} and press "
            "any key to continue..."
        )
        self._write("CAL:ZERO:TYPE EXT")
        self._zero()
        self.logger.info(f"{self.name} zeroed externally")
        self.logger.debug(
            f"{self.name}: Waiting for user intervention on zeroing"
        )
        input(
            f"Please reconnect input to {self.name} and press "
            "any key to continue..."
        )

    def set_freq(self, freq):
        assert self.reserved
        self._write(f"FREQ {readable_freq(freq)}")
        if self.verify:
            assert self.get_freq() == freq
        self.centreFreq = freq

    def get_freq(self) -> float:
        return float(self._query("FREQ?"))

    def measure_power(self, freq: float) -> float:
        assert self.reserved
        if freq != self.centreFreq:
            self.set_freq(freq)
        timeout = self.dev.timeout
        self.dev.timeout = 0
        x = float(self._query("MEAS? DEF, 3, (@1)"))
        self.dev.timeout = timeout
        return x

    def _zero(self):
        """
        Internal helper function as internal and external zeroing
        uses the same comamand
        """
        self.logger.info(f"Calibrating {self.name}. This takes a while...")
        x = self.dev.timeout
        self.dev.timeout = 0
        result = self._query("CAL?")
        self.dev.timeout = x
        assert (
            result != 0
        ), f"Calibration of {self.name} failed. Return code: {result}"
