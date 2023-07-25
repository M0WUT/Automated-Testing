from logging import Logger

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.PowerMeter.PowerMeter import PowerMeter
from AutomatedTesting.Misc.UsefulFunctions import readable_freq


class Agilent_U2001A(PowerMeter):
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
            min_freq=10e6,
            max_freq=6e9,
            timeout=500,
            **kwargs,
        )

    def __enter__(self):
        self.initialise()

    def initialise(self):
        super().initialise()
        self._write("INIT:CONT ON")
        return self

    def internal_zero(self):
        self._write("CAL:ZERO:TYPE INT")
        self._zero()
        self.logger.info(f"{self.name} zeroed internally")

    def external_zero(self):
        self.logger.debug(f"{self.name}: Waiting for user intervention on zeroing")
        input(
            f"Please disconnect input from {self.name} and press "
            "any key to continue..."
        )
        self._write("CAL:ZERO:TYPE EXT")
        self._zero()
        self.logger.info(f"{self.name} zeroed externally")
        self.logger.debug(f"{self.name}: Waiting for user intervention on zeroing")
        input(
            f"Please reconnect input to {self.name} and press " "any key to continue..."
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
        assert result != 0, f"Calibration of {self.name} failed. Return code: {result}"
