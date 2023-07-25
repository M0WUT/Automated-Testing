from logging import Logger

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument


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
            **kwargs,
        )
        self.reserved = False  # Whether this instrument is in use
        self.name = self.name

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
        self.logger.info(f"{self.name} reserved as {self.name}")

    def free(self):
        assert self.reserved
        self.logger.debug(f"{self.name} freed from role as {self.name}")
        self.name = self.instrument_name
        self.reserved = False
