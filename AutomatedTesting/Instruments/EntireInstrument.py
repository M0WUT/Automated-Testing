# Standard imports
from logging import Logger
import logging
from typing import Optional

# Third party imports
from pyvisa import ResourceManager

# Local imports
from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.Transducer.Transducer import Transducer
from AutomatedTesting.Misc.Corrections import Corrections


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
        logging_level: int,
        corrections: Optional[Corrections] = None,
        transducer: Optional[Transducer] = None,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            logging_level=logging_level,
            **kwargs,
        )
        self.reserved = False  # Whether this instrument is in use
        self.corrections = corrections
        self.transducer = transducer

    def reserve(self, purpose: str):
        """
        Allows a test to assign an instrument a particular purpose
        This prevents the same instrument accidentially being assigned
        multiple roles
        """
        assert self.reserved is False, "Attempted to reserve a reserved device"
        self.reserved = True
        self.logger.info(f"{self.name} reserved for {purpose}")
        self.logger = logging.getLogger(purpose)

    def free(self):
        assert self.reserved
        self.logger.info("Released")
        self.logger = logging.getLogger(self.name)
        self.reserved = False

    def apply_corrections(self, corrections: Corrections) -> None:
        self.corrections = corrections

    def apply_transducer(self, transducer: Transducer) -> None:
        self.transducer = transducer

    #################################################
    # Functions that must be implemented per device #
    #################################################

    # Inherited from BaseInstrument
    def _set_remote_control(self) -> None:
        raise NotImplementedError

    def _set_local_control(self) -> None:
        raise NotImplementedError
