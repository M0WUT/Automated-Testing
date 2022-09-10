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

    def __init__(self):
        super().__init__()
        self.reserved = False  # Whether this instrument is in use
        # When reserved, this will contain the purpose of the instrument
        self.displayName = None

        self.reserved = False  # Whether this instrument is in use
        # When reserved, this will contain the purpose of the instrument
        self.displayName = None

    def reserve(self, purpose: str):
        """
        Allows a test to assign an instrument a particular purpose
        This prevents the same instrument accidentially being assigned
        multiple roles
        """
        assert self.reserved is False, "Attempted to reserve a reserved device"
        self.displayName = purpose
        self.reserved = True
        self.logger.info(
            f"{self.instrumentName} reserved as {self.displayName}"
        )

    def free(self):
        assert self.reserved
        self.logger.debug(
            f"{self.instrumentName} freed from role as {self.displayName}"
        )
        self.displayName = None
        self.reserved = False
