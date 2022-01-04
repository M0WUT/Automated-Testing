import logging
from multiprocessing import Lock
from time import sleep

import pyvisa
from AutomatedTesting.TopLevel.InstrumentSupervisor import (
    InstrumentConnectionError,
    InstrumentSupervisor,
)
from AutomatedTesting.TopLevel.ProcessWIthCleanStop import ProcessWithCleanStop


class BaseInstrument:
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
        logging.debug(f"Initialising {self.name}")
        assert isinstance(resourceManager, pyvisa.highlevel.ResourceManager)

        try:
            self.dev = resourceManager.open_resource(self.address, **self.kwargs)
        except (pyvisa.errors.VisaIOError, ValueError, Exception):
            raise InstrumentConnectionError

        assert isinstance(supervisor, InstrumentSupervisor)
        self.supervisor = supervisor

        x = self.read_id().strip()
        if x != self.id:
            logging.error(
                f"ID check failed on {self.name}. "
                f"Expected ID: {self.id} "
                f"Received ID: {x}"
            )
            raise AssertionError

        self.reset()

        errorList = self.read_instrument_errors()
        while errorList != []:
            for code, message in errorList:
                logging.warning(
                    f"{self.name} reporting error {code} ({message}). "
                    f"Waiting for error to clear"
                )
            sleep(1)
            errorList = self.read_instrument_errors()

        logging.debug(f"Starting monitoring thread for Instrument: {self.name}")
        self.errorThread = ProcessWithCleanStop(target=self.check_instrument_errors)
        self.errorThread.start()

    def read_id(self) -> str:
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
        self._write("*RST")  # Reset device
        self._write("*CLS")  # Clear errors

    def _write(self, command: str, acquireLock: bool = True):
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
        if acquireLock:
            self.lock.acquire()
            try:
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
        response = self.dev.read().strip()
        return response

    def _query(self, command, acquireLock: bool = True) -> str:
        """
        Sends command and returns response

        Args:
            command (str): Command to send
            acquireLock (bool): Where we need to lock the serial object

        Returns:
            str: Response from Instrument

        Raises:
            None
        """
        if acquireLock:
            self.lock.acquire()
            try:
                self._write(command, acquireLock=False)
                return self._read()
            finally:
                self.lock.release()
        else:
            self._write(command, acquireLock=False)
            return self._read()

    def _query_raw(self, command):
        """
        Sends command and returns raw response

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
            return self.dev.read_raw()
        finally:
            self.lock.release()

    def read_instrument_errors(self):
        """
        Checks whole instrument for errors

        Args:
            None

        Returns:
            list(Tuple): Pairs of (status code, error message)

        Raises:
            None
        """
        errorList = []
        errors = self._query("SYST:ERR?")
        if errors != '+0,"No error"':
            errorStrings = errors.split('",')

            for x in errorStrings:
                errorCode, errorMessage = x.split(',"')
                # Last item in list isn't comma terminated so need
                # to manually remove trailing speech marks
                errorMessage.rstrip('"')
                errorList.append((int(errorCode), errorMessage))
        return errorList

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
            sleep(3)
            errorList = self.read_instrument_errors()
            if errorList != []:
                self.error = True
                for code, message in errorList:
                    logging.error(
                        f"{self.name} reporting error {code} ({message})."
                        f"Shutting down..."
                    )
                self.supervisor.handle_instrument_error()
        logging.debug(f"{self.name} monitoring thread shutdown")

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
        if self.errorThread:
            self.errorThread.terminate()
            self.errorThread = None
        self.close_remote_session()
        logging.info(f"{self.name} Shutdown")

    def close_remote_session(self):
        """
        Final actions before connection is closed.
        Override if final commands after channel cleanup
        are needed i.e. to return the device to local control

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        self.dev.close()
