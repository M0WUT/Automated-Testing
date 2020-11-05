import pyvisa
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor


class BaseInstrument():
    def __init__(self, address, **kwargs):
        """
        Parent class for all Test Equipment
        This should never be implemented directly

        Args:
            address (str):
                PyVisa String e.g. "GPIB0::14::INSTR"
                with device location
            **kwargs:
                additional parameters for PyVisa

        Raises:
            None

        Returns:
            None
        """

        self.resourceManager = None
        self.address = address
        self.kwargs = kwargs
        self.dev = None

    def initialise(self, resourceManager, supervisor):
        """
        Args:
            resourceManager (pyvisa.highlevel.ResourceManager):
                PyVisa Resource Manager.
            supervisor (AutomatedTesting.TestClass.test_supervisor.TestSupervisor):
                Test Supervisor

        Returns:
            None

        Raises:
            ValueError: Resource Manager / Supervisor is not valid
            AssertionError: Fails to query correct device ID
        """
        if (isinstance(resourceManager, pyvisa.highlevel.ResourceManager)):
            self.dev = resourceManager.open_resource(
                self.address,
                **self.kwargs
            )
        else:
            raise ValueError

        if(isinstance(supervisor, InstrumentSupervisor)):
            self.supervisor = supervisor
        else:
            raise ValueError

        assert self.read_id() == self.id

    def read_id(self):
        raise NotImplementedError  # pragma: no cover

    def cleanup(self):
        self.dev.close()
