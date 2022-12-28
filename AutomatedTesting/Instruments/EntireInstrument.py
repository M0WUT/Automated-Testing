from logging import Logger

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from pyvisa import ResourceManager


class EntireInstrument(BaseInstrument):
    """
    Class for instruments that can't conceptually have multiple independent
    systems. E.g. Signals Generators and PSUs don't come under this class as
    they can support multiple channels and so should inherit from
    MultichannelInstrument (even if that specific instance only has one
    channel). This class is for things such as Network Analysers,
    Multimeters, Noise Sources etc that cannot be treated as multiple parts
    """

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
            **kwargs,
        )
        self.reserved = False  # Whether this instrument is in use
        self.name = self.instrumentName

        # Used to remember previous freq to avoid continually updating it
        self.centreFreq = 0

    def reserve(self, purpose: str):
        """
        Allows a test to assign an instrument a particular purpose
        This prevents the same instrument accidentially being assigned
        multiple roles
        """
        assert self.reserved is False, "Attempted to reserve a reserved device"
        self.name = purpose
        self.reserved = True
        self.logger.info(f"{self.instrumentName} reserved as {self.name}")

    def free(self):
        assert self.reserved
        self.logger.debug(f"{self.instrumentName} freed from role as {self.name}")
        self.name = self.instrumentName
        self.reserved = False
