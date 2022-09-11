import logging
import os
import signal
from multiprocessing import Lock, Process
from time import sleep
from typing import List, Tuple

from pyvisa import ResourceManager, VisaIOError


class InstrumentConnectionError(Exception):
    pass


class BaseInstrument:
    """
    Base class that all instruments should inherit from.
    Initialisation just sets up the data structure, instrument connection is
    performed once opened with a context manager ("with x as y:")

    When opened with a context manager, this will start communication with the
    instrument, confirm that the instrument responds correctly and begin
    checking the instrument for errors periodically

    Closing the connection is handled within the context manager's
    __exit__ function

    """

    def __init__(
        self,
        resourceManager: ResourceManager,
        visaAddress: str,
        instrumentName: str,
        expectedIdnResponse: str,
        verify: bool,
        logger: logging.Logger,
        **kwargs,
    ):
        self.resourceManager = resourceManager
        self.visaAddress = visaAddress
        self.instrumentName = instrumentName
        self.expectedIdnResponse = expectedIdnResponse
        self.verify = verify
        self.logger = logger
        self.kwargs = kwargs

        self.dev = None  # Connection to the device
        self.lock = Lock()  # lock for access to the device connection

    def __enter__(self):
        """
        Opens connection to the instrument, checks the IDN response is correct
        and begins monitoring for errors
        """
        self.open_connection()
        self.logger.info(f"Connected to {self.instrumentName}")

        # Reset the Device and start error monitoring thread
        self.reset()

        self.errorProcess = Process(
            target=self.check_instrument_errors, args=[os.getpid()], daemon=True
        )
        self.errorProcess.start()

        # Lock front panel control of the instrument
        self.set_remote_control()
        self.logger.info(f"{self.instrumentName} initialised")

    def __exit__(self, *args, **kwargs):
        self.set_local_control()
        if self.errorProcess:
            self.errorProcess.terminate()
        if self.dev:
            self.dev.close()
            self.dev = None
            self.logger.info(f"Connection to {self.instrumentName} closed")

    def open_connection(self):
        """
        Opens the connection to the device
        """
        try:
            self.dev = self.resourceManager.open_resource(
                self.visaAddress, **self.kwargs
            )
        except (VisaIOError, ValueError):
            raise InstrumentConnectionError(
                f'Connection to "{self.instrumentName}" at VISA address '
                f'"{self.visaAddress}" failed.\r\nAvailable VISA address:'
                f" {self.resourceManager.list_resources()}"
            )

        # Check device ID to ensure we're connecting the right thing
        idnString = self.query_id()
        assert idnString == self.expectedIdnResponse, (
            f"Unexpected IDN response from {self.instrumentName}. "
            f'Expected response: "{self.expectedIdnResponse}", '
            f'Received response: "{idnString}"'
        )

    def test_connection(self) -> bool:
        """
        Tests whether the instruments can be connected to.
        Return True if this is possible
        """
        try:
            self.open_connection()
            return True
        except InstrumentConnectionError:
            return False
        finally:
            if self.dev:
                # Just in case the instrument automatically goes to remote
                self.set_local_control()
                self.dev.close()

    def set_remote_control(self):
        """
        Used if the instrument has any specific commands for remote control
        e.g. locking the front panel or blanking the display
        """
        pass

    def set_local_control(self):
        """
        Returns the instrument back to local control
        """
        pass

    def check_instrument_errors(self, pid: int):
        """
        This function should be run in a separate thread.
        It queries the instrument then processes the results
        and decides whether to flag an issue to the main process
        """
        self.logger.debug(
            f"Started error monitoring thread for {self.instrumentName}"
        )
        while True:
            sleep(3)
            errorList = self.get_instrument_errors()
            if errorList:
                for errorCode, errorMessage in errorList:
                    self.logger.error(
                        f"{self.instrumentName} reporting error "
                        f"{errorCode} ({errorMessage}). Shutting down..."
                    )

                # Inform main thread
                os.kill(pid, signal.SIGUSR1)

    def get_instrument_errors(self) -> List[Tuple[int, str]]:
        """
        Function to extract error messages from the device.
        This can be overwritten by sub-classes if this uses different syntax
        """
        errorList = []
        errors = self._query("SYST:ERR?")

        for x in errors.split('",'):
            errorCode, errorMessage = x.strip('"').split(',"')
            # Last item in list isn't comma terminated so need
            # to manually remove trailing speech marks
            errorCode = int(errorCode)
            errorMessage.rstrip('"')
            if errorCode:
                errorList.append((errorCode, errorMessage))
        return errorList

    def query_id(self) -> str:
        """
        Queries the device's ID string and returns it
        """
        return self._query("*IDN?")

    def reset(self):
        """
        Resets the device and clears all errors
        """
        self._write("*RST")
        # Wait for reset to complete
        while self._query("*OPC?") == "0":
            pass
        self._write("*CLS")

    def _write(self, x: str, acquireLock: bool = True):
        """
        Blocks until device is available, then writes to the device

        acquireLock specifys whether this function should
        acquire the lock itself (e.g. when used with query,
        the lock will have already been acquired)
        """
        if acquireLock:
            self.lock.acquire()
            try:
                self.dev.write(x)
            finally:
                self.lock.release()
        else:
            self.dev.write(x)
        # self.logger.debug(x)  # @DEBUG

    def _read(self, acquireLock: bool = True) -> str:
        """
        Blocks until device is available, then reads a line
        from the device

        acquireLock specifys whether this function should
        acquire the lock itself (e.g. when used with query,
        the lock will have already been acquired)
        """
        if acquireLock:
            self.lock.acquire()
            try:
                result = self.dev.read.strip()
            finally:
                self.lock.release()
        else:
            result = self.dev.read().strip()

        return result

    def _query(self, command: str) -> str:
        """
        Writes "command" to the device and returns the response
        """
        self.lock.acquire()
        try:
            self._write(command, acquireLock=False)
            response = self._read(acquireLock=False)
        finally:
            self.lock.release()
        return response
