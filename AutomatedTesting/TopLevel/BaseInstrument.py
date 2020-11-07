import pyvisa
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from multiprocessing import Lock
from time import sleep
import logging


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
        self.lock = Lock()

    def initialise(self, resourceManager, supervisor):
        """
        Args:
            resourceManager (pyvisa.highlevel.ResourceManager):
                PyVisa Resource Manager.
            supervisor (InstrumentSupervisor):
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

        x = self.read_id().strip()
        if(x != self.id):
            logging.error(
                f"Failed to initialise device {self.name}. "
                f"Expected ID: {self.id} "
                f"Received ID: {x}"
            )
            raise AssertionError

    def read_id(self):
        raise NotImplementedError  # pragma: no cover

    def _write(self, command, acquireLock=False):
        """
        Writes Data to Instrument - needs sleep otherwise data gets dropped
        in some cases

        Args:
            command (str): Command to send
            acquireLock:
                True: Executing a pure write command and need to acquire lock
                False: Write is part of a query (combined write/read)
                    and does not need to acquire lock

        Returns:
            None

        Raises:
            None
        """
        sleep(0.1)
        if(acquireLock):
            try:
                self.lock.acquire()
                self.dev.write(command)
            finally:
                self.lock.release()
        else:
            self.dev.write(command)

    def _read(self):
        """
        Reads a single respone (until \n or message end)
        Doesn't acquire lock as normally just a part
        of a query which handles locking

        Args:
            None

        Returns:
            str: Response from Instrument

        Raises:
            None
        """
        return self.dev.read()

    def _query(self, command):
        """
        Sends command and returns response

        Args:
            command (str): Command to send

        Returns:
            str: Response from Instrument

        Raises:
            None
        """
        try:
            self.lock.acquire()
            self._write(command)
            return self._read()
        finally:
            self.lock.release()

    def cleanup(self):
        """
        Returns instrument to a safe state and disconnects
        Use of seperate close_remote_session allows a command
        to be issued to the device after all inherited classes
        have been cleaned up

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.close_remote_session()

    def close_remote_session(self):
        """
        Final actions before connection is closed.
        Override if final commands after e.g. channel cleanup
        are needed i.e. to return the device to local control

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.dev.close()
