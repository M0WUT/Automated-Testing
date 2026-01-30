# Standard imports
import logging
import os
import signal
from threading import Lock, Thread, Event
from time import sleep
from typing import Optional

# Third party imports
from pyvisa import ResourceManager, VisaIOError
from serial import SerialException

# Local imports


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
        verify: bool = True,
        logging_level: int = logging.INFO,
        only_software_control: bool = True,
        **kwargs,
    ):
        self.resource_manager = resource_manager
        self.visa_address = visa_address
        self.name = name
        self.expected_idn_response = expected_idn_response
        self.verify = verify
        self.logging_level = logging_level
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.logging_level)
        self.only_software_control = only_software_control

        self.kwargs = kwargs

        self.monitor_process = None
        self.terminate_monitor_process_flag = Event()
        self.lock = Lock()  # lock for access to the device connection

    def __enter__(self):
        """
        Opens connection to the instrument, checks the IDN response is correct
        and begins monitoring for errors
        """
        self.open_connection()
        self.logger.info("Connected")

        # Reset the Device and start error monitoring thread only if only
        # under software control (as opposed to being used interactively)
        if self.only_software_control:
            self.reset()
            self.clear_instrument_errors()
            self.monitor_process = Thread(
                target=self.check_instrument_errors, args=[os.getpid()], daemon=True
            )
            self.monitor_process.start()

        self.logger.info("Initialised")
        return self

    def __exit__(self, *args, **kwargs):
        self.shutdown()

    def shutdown(self) -> None:
        self.logger.info("Shutting down connection")
        if self.only_software_control:
            if self.monitor_process:
                self.terminate_monitor_process_flag.set()
                self.monitor_process.join()
            self.set_local_control()
        if self.dev:
            self.dev.close()
            self.dev = None
            self.logger.info("Connection closed")

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

        # Lock front panel control of the instrument
        self.set_remote_control()

        # Check device ID to ensure we're connecting the right thing
        idn_string = self.query_id()
        assert idn_string == self.expected_idn_response, (
            f"Unexpected IDN response from {self.name}. "
            f'Expected response: "{self.expected_idn_response}", '
            f'Received response: "{idn_string}"'
        )

    def reset(self):
        self._write("*RST")
        self.wait_until_op_complete()

    def clear_instrument_errors(self):
        self._write("*CLS")

    def set_remote_control(self):
        """
        Used if the instrument has any specific commands for remote control
        e.g. locking the front panel or blanking the display
        """
        self._set_remote_control()

    def set_local_control(self):
        """
        Returns the instrument back to local control
        """
        self._set_local_control()

    def check_instrument_errors(self, pid: int):
        """
        This function should be run in a separate thread.
        It queries the instrument then processes the results
        and decides whether to flag an issue to the main process
        """
        self.logger.debug("Started error monitoring thread")
        while not self.terminate_monitor_process_flag.is_set():
            sleep(3)
            error_list = self.get_instrument_errors()
            if error_list:
                for code, message in error_list:
                    self.logger.error(f"Error {code} ({message}). Shutting down...")
                # Inform main thread
                os.kill(pid, signal.SIGTERM)

    def get_instrument_errors(self) -> list[tuple[int, str]]:
        """
        Function to extract error messages from the device.
        """
        error_list = []
        errors = self._query("SYST:ERR:ALL?")

        if errors == "":
            return []

        for x in errors.split('",'):
            code, message = x.split(",")
            # Last item in list isn't comma terminated so need
            # to manually remove trailing speech marks
            message.replace('"', "")

            code = int(code)
            if code:
                error_list.append((code, message))

        return error_list

    def query_id(self) -> str:
        """
        Queries the device's ID string and returns it
        """
        return self._query("*IDN?")

    def _write(self, x: str, acquire_lock: bool = True):
        """
        Blocks until device is available, then writes to the device

        acquire_lock specifys whether this function should
        acquire the lock itself (e.g. when used with query,
        the lock will have already been acquired)
        """
        if acquire_lock:
            self.lock.acquire()
            try:
                self.dev.write(x)  # type: ignore
            finally:
                self.lock.release()
        else:
            self.dev.write(x)  # type: ignore
        self.logger.debug(f"SENT: {x}")

    def _read(
        self, acquire_lock: bool = True, timeout_s: Optional[float] = None
    ) -> str:
        """
        Blocks until device is available, then reads a line
        from the device

        acquire_lock specifys whether this function should
        acquire the lock itself (e.g. when used with query,
        the lock will have already been acquired)
        """
        if acquire_lock:
            self.lock.acquire()

        try:
            old_timeout = self.dev.timeout
            if timeout_s:
                self.dev.timeout = timeout_s * 1000
            result = self.dev.read().strip()  # type: ignore
        finally:
            self.dev.timeout = old_timeout
            if acquire_lock:
                self.lock.release()

        self.logger.debug(f"RCVD: {result}")
        return result

    def _query(self, command: str, timeout_s: Optional[float] = None) -> str:
        """
        Writes "command" to the device and returns the response
        """
        self.lock.acquire()
        try:
            self._write(command, acquire_lock=False)
            response = self._read(acquire_lock=False, timeout_s=timeout_s)
        finally:
            self.lock.release()
        return response

    def wait_until_op_complete(self, timeout_s: Optional[int] = None):
        """
        Blocks until current commmands have all been executed
        """
        self._query("*OPC?", timeout_s)

    ################################################################
    # Functions that must be implemented on a per-instrument basis #
    ################################################################
    def _set_remote_control(self) -> None:
        raise NotImplementedError

    def _set_local_control(self) -> None:
        raise NotImplementedError
