import logging
from time import sleep

from pyvisa import ResourceManager, VisaIOError

from AutomatedTesting.Instruments.MultichannelInstrument import InstrumentChannel
from AutomatedTesting.Instruments.PowerSupply.PowerSupply import (
    PowerSupply,
    PowerSupplyChannel,
)


class Tenma_Generic(PowerSupply):
    """
    Class for Tenma PSUs
    NB All the sleep() are really important

    Args:
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location

    Returns:
        None

    Raises:
        None
    """

    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        channel_count: int,
        channels: list[InstrumentChannel],
        logger: logging.Logger,
        *args,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            expected_idn_response=expected_idn_response,
            name=name,
            verify=verify,
            logger=logger,
            channel_count=channel_count,
            channels=channels,
            baud_rate=9600,
            read_termination=None,
            write_termination=None,
            timeout=500,
            *args,
            **kwargs,
        )

    def reset(self):
        """
        This PSU has no reset functionality so override default
        and do nothing

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        pass

    def _write(self, command, acquireLock=True):
        super()._write(command, acquireLock)
        sleep(0.1)  # Super important - do not delete

    def _read(self, num_bytes=0):
        """
        Reads data from PSU as it's infernal with no termination

        Args:
            None

        Returns:
            str: Device ID String

        Raises:
            None
        """
        if num_bytes:
            return_string = self.dev.read_bytes(num_bytes).decode("utf-8")
        else:
            return_string = ""
            while True:
                try:
                    return_string += self.dev.read_bytes(1).decode("utf-8")
                except VisaIOError:
                    break
        assert return_string

        sleep(0.1)  # Super important - do not delete
        return return_string

    def _query(self, command, num_bytes=None):
        """
        Sends command and returns response
        Due to this PSU being a total pain,
        need to specify number of bytes to read

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
            return self._read(num_bytes)
        finally:
            self.lock.release()

    def query_id(self):
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

    def set_channel_voltage(self, channel_number, voltage):
        """
        Sets the voltage on channel <channel_number>
        to <voltage> Volts

        Args:
            channel_number (int): Power Supply Channel Number
            voltage (float): Target Voltage in Volts

        Returns:
            None

        Raises:
            None
        """
        self._write(f"VSET{channel_number}:{round(voltage, 2)}")

    def get_channel_voltage(self, channel_number):
        """
        Reads voltage setpoint on channel <channel_number>

        Args:
            channel_number (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's voltage setpoint

        Raises:
            None
        """
        return float(self._query(f"VSET{channel_number}?", 5))

    def measure_channel_voltage(self, channel_number):
        """
        Reads output voltage on channel <channel_number>

        Args:
            channel_number (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's output voltage in Volts

        Raises:
            None
        """
        return float(self._query(f"VOUT{channel_number}?", 5))

    def set_channel_current_limit(self, channel_number, current):
        """
        Attempts to set the current on channel <channel_number>
        to <current> Amps

        Args:
            channel_number (int): Power Supply Channel Number
            current (float): Target Current in Amps

        Returns:
            None

        Raises:
            None
        """
        self._write(f"ISET{channel_number}:{round(current, 3)}")

    def get_channel_current_limit(self, channel_number):
        """
        Reads current setpoint on channel <channel_number>

        Args:
            channel_number (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's current setpoint

        Raises:
            None
        """
        return float(self._query(f"ISET{channel_number}?", 6))

    def measure_channel_current(self, channel_number):
        """
        Reads output current on channel <channel_number>

        Args:
            channel_number (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's output current in Amps

        Raises:
            None
        """
        return float(self._query(f"IOUT{channel_number}?", 5))

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        self._write(f"OUT{1 if enabled else 0}")
        if enabled:
            sleep(1)

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        status = self._get_status_byte()
        return status[6] == "1"

    def _get_status_byte(self) -> int:
        # Get status byte and convert to string in reverse
        # order so status[0] = bit 0
        status = ord(self._query("STATUS?", 1))
        status = format(status, "08b")[::-1]
        return status

    def get_channel_errors(self, channel_number):
        return []

    def check_channel_errors(self, channel_number):
        """
        Checks for errors on channel with output enabled
        Errors are:
            Output channel has become disabled due to error
            Output channel is in constant current mode

        Args:
            channel_number (int): Power Supply Channel Number

        Returns:
            bool: True if channel has errors

        Raises:
            None
        """
        status = self._get_status_byte()

        # Only have one channel on this device
        if status[0] == "0":
            logging.error(
                f"PSU: {self.name}, "
                f"Channel {self.channels[channel_number - 1].name} "
                "is current limiting"
            )
            return True
        else:
            return False

    def get_instrument_errors(self):
        """
        Checks for instrument errors

        Args:
            None

        Returns:
            list(Tuple): (error code, error message)

        Raises:
            None
        """
        # PSU too simple to have error monitoring
        # so assume everything is fine!
        return []


class Tenma_72_2535(Tenma_Generic):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: logging.Logger,
        *args,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            channel_count=1,
            channels=[
                PowerSupplyChannel(
                    channel_number=1,
                    instrument=self,
                    logger=logger,
                    min_voltage=0,
                    max_voltage=30,
                    min_current=0,
                    max_current=3,
                )
            ],
            logger=logger,
            *args,
            **kwargs,
        )


class Tenma_72_2940(Tenma_Generic):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logger: logging.Logger,
        *args,
        **kwargs,
    ):
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            channel_count=1,
            channels=[
                PowerSupplyChannel(
                    channel_number=1,
                    instrument=self,
                    logger=logger,
                    min_voltage=0,
                    max_voltage=60,
                    min_current=0,
                    max_current=3,
                )
            ],
            logger=logger,
            *args,
            **kwargs,
        )
