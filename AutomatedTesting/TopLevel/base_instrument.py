class BaseInstrument():
    def __init__(self, resourceManager, address, **kwargs):
        """
        Pure virtual class for all Test Equipment
        This should never be implemented directly

        Args:
            resourceManager (pyvisa.highlevel.ResourceManager):
                PyVisa Resource Manager.
            address (str):
                PyVisa String e.g. "GPIB0::14::INSTR"
                with device location
            **kwargs:
                additional parameters for PyVisa


        Returns:
            None

        Raises:
            ValueError: If Resource Manager fails to open device
            AssertionError: Device's ID string does not match the expected
                value
        """

        self.resourceManager = resourceManager
        self.address = address
        self.dev = None
        self.dev = self.resourceManager.open_resource(self.address, **kwargs)

        assert self.read_id() == self.id

    def read_id(self):
        raise NotImplementedError

    def __del__(self):
        if self.dev is not None:
            self.dev.close()
