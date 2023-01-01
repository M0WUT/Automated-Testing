import logging
import os
import signal
from multiprocessing import Lock, Process
from time import sleep
from typing import List, Tuple

from pyvisa import ResourceManager, VisaIOError
from serial import SerialException


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
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: logging.Logger,
        only_software_control: bool = True,
        **kwargs,
    ):
        self.resource_manager = resource_manager
        self.visa_address = visa_address
        self.name = name
        self.expected_idn_response = expected_idn_response
        self.verify = verify
        self.logger = logger
        self.kwargs = kwargs
        self.only_software_control = only_software_control

        self.dev = None  # Connection to the device
        self.lock = Lock()  # lock for access to the device connection

    def __enter__(self):
        self.initialise()

    def initialise(self):
        """
        Opens connection to the instrument, checks the IDN response is correct
        and begins monitoring for errors
        """
        self.open_connection()
        self.logger.info(f"Connected to {self.name}")

        # Reset the Device and start error monitoring thread only if only under software control
        # (as opposed to being used interactively)
        if self.only_software_control:
            self.reset()

            self.error_process = Process(
                target=self.check_instrument_errors, args=[os.getpid()], daemon=True
            )
            self.error_process.start()

            # Lock front panel control of the instrument
            self.set_remote_control()
        self.logger.info(f"{self.name} initialised")

    def __exit__(self, *args, **kwargs):
        self.cleanup()

    def cleanup(self):
        if self.only_software_control:
            self.set_local_control()
            if self.error_process:
                self.error_process.terminate()
        if self.dev:
            self.dev.close()
            self.dev = None
            self.logger.info(f"Connection to {self.name} closed")

    def open_connection(self):
        """
        Opens the connection to the device
        """
        try:
            self.dev = self.resource_manager.open_resource(
                self.visa_address, **self.kwargs
            )
        except (VisaIOError, ValueError, SerialException):
            raise InstrumentConnectionError(
                f'Connection to "{self.name}" at VISA address '
                f'"{self.visa_address}" failed.\r\nAvailable VISA address:'
                f" {self.resource_manager.list_resources()}"
            )

        # Check device ID to ensure we're connecting the right thing
        idnString = self.query_id()
        assert idnString == self.expected_idn_response, (
            f"Unexpected IDN response from {self.name}. "
            f'Expected response: "{self.expected_idn_response}", '
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
        except (InstrumentConnectionError, VisaIOError):
            return False
        finally:
            if self.dev:
                # Just in case the instrument automatically goes to remote
                self.set_local_control()
                self.dev.close()

    def is_connected(self) -> bool:
        """Returns True if connected to the instrument"""
        return bool(self.dev)

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
        self.logger.debug(f"Started error monitoring thread for {self.name}")
        while True:
            sleep(3)
            error_list = self.get_instrument_errors()
            if error_list:
                for code, message in error_list:
                    self.logger.error(
                        f"{self.name} reporting error "
                        f"{code} ({message}). Shutting down..."
                    )

                # Inform main thread
                os.kill(pid, signal.SIGUSR1)

    def get_instrument_errors(self) -> List[Tuple[int, str]]:
        """
        Function to extract error messages from the device.
        This can be overwritten by sub-classes if this uses different syntax
        """
        error_list = []
        errors = self._query("SYST:ERR?")

        for x in errors.split('",'):
            code, message = x.strip('"').split(',"')
            # Last item in list isn't comma terminated so need
            # to manually remove trailing speech marks
            code = int(code)
            message.rstrip('"')
            if code:
                error_list.append((code, message))
        return error_list

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
        self.logger.debug(x)

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
