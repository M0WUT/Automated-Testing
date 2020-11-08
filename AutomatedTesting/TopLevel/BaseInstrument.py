import pyvisa
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from AutomatedTesting.TopLevel.ProcessWIthCleanStop import ProcessWithCleanStop
from multiprocessing import Lock
from time import sleep
import logging
import sys


class BaseInstrument():
    def __init__(self, address, id, name, **kwargs):
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
        self.id = id
        self.name = name
        self.supervisor = None
        self.error = False
        self.errorThread = None

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
            try:
                self.dev = resourceManager.open_resource(
                    self.address,
                    **self.kwargs
                )
            except ValueError:
                logging.critical(f"Unable to open instrument: {self.name}")
                sys.exit(1)
        else:
            raise ValueError

        if(isinstance(supervisor, InstrumentSupervisor)):
            self.supervisor = supervisor
        else:
            raise ValueError

        self.reset()

        x = self.read_id().strip()
        if(x != self.id):
            logging.error(
                f"ID check failed on {self.name}. "
                f"Expected ID: {self.id} "
                f"Received ID: {x}"
            )
            raise AssertionError

        errorList = self.read_instrument_errors()
        while(errorList != []):
            for code, message in errorList:
                logging.warning(
                    f"{self.name} reporting error {code} ({message}). "
                    f"Waiting for error to clear"
                )
            sleep(1)
            errorList = self.read_instrument_errors()

        logging.debug(
            f"Starting monitoring thread for Instrument: {self.name}"
        )
        self.errorThread = ProcessWithCleanStop(
                target=self.check_instrument_errors
            )
        self.errorThread.start()

    def read_id(self):
        """
        Queries Device ID

        Args:
            None

        Returns:
            str: Device ID String

        Raises:
            None
        """
        return self._query("*IDN?")

    def reset(self):
        """
        Resets instrument and waits for error list to clear

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self._write("*RST")

    def _write(self, command, acquireLock=True):
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
            self._write(command, acquireLock=False)
            return self._read()
        finally:
            self.lock.release()

    def check_instrument_errors(self, event):
        """
        Function that lives in separate thread to monitor
        instrument for errors

        Args:
            event(Multiprocessing.Event): will be set
                when thread should terminate

        Returns:
            None

        Raises:
            None
        """
        while not event.is_set() and self.error is False:
            errorList = self.read_instrument_errors()
            if(errorList != []):
                self.error = True
                for code, message in errorList:
                    logging.warning(
                        f"{self.name} reporting error {code} ({message})."
                        f"Shutting down..."
                    )
                self.supervisor.handle_instrument_error()

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
        if self.errorThread is not None:
            self.errorThread.terminate()
            self.errorThread = None
            logging.debug(
                f"{self.name} monitoring thread shutdown"
            )
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
