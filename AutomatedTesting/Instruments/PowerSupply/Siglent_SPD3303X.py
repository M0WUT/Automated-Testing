# Standard imports
import logging
from time import sleep

from pyvisa import ResourceManager

# Third party imports
from AutomatedTesting.Instruments.PowerSupply.PowerSupply import (
    PowerSupply, PowerSupplyChannel)

# Local imports


class SiglentSPD3303X(PowerSupply):
    # Bit masks for status byte
    CHANNEL1_MODE_BIT = 0
    CHANNEL2_MODE_BIT = 1
    MODE_LSB = 2
    MODE_MSB = 3
    CHANNEL1_STATUS = 4
    CHANNEL2_STATUS = 5
    TIMER1_STATUS = 6
    TIMER2_STATUS = 7
    CHANNEL1_DISPLAY = 8
    CHANNEL2_DISPLAY = 9

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
            channel_count=2,
            channels=[
                PowerSupplyChannel(
                    channel_number=1,
                    instrument=self,
                    logger=logger,
                    min_voltage=0,
                    max_voltage=32,
                    min_current=0,
                    max_current=3.2,
                ),
                PowerSupplyChannel(
                    channel_number=2,
                    instrument=self,
                    logger=logger,
                    min_voltage=0,
                    max_voltage=32,
                    min_current=0,
                    max_current=3.2,
                ),
            ],
            logger=logger,
            *args,
            **kwargs,
        )

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
        self._write(f"CH{channel_number}:VOLT {round(voltage, 3)}")

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
        return float(self._query(f"CH{channel_number}:VOLT?"))

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
        return float(self._query(f"MEAS:VOLT? CH{channel_number}"))

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
        self._write(f"CH{channel_number}:CURR {round(current, 3)}")

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
        return float(self._query(f"CH{channel_number}:CURR?"))

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
        return float(self._query(f"MEAS:CURR? CH{channel_number}"))

    def set_channel_output_enabled_state(self, channel_number: int, enabled: bool):
        self._write(f"OUTP CH{channel_number},{'ON' if enabled else 'OFF'}")
        if enabled:
            sleep(1)

    def get_channel_output_enabled_state(self, channel_number: int) -> bool:
        status = self._get_status_byte()
        if channel_number == 1:
            return status[self.CHANNEL1_STATUS] == "1"
        else:
            return status[self.CHANNEL2_STATUS] == "1"

    def _get_status_byte(self) -> str:
        # Get status byte and convert to string in reverse
        # order so status[0] = bit 0
        response = self._query("SYST:STATUS?")
        status = int(response, 0)
        status = format(status, "010b")[::-1]
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

        if (channel_number == 1 and status[self.CHANNEL1_MODE_BIT] == "1") or (
            channel_number == 2 and status[self.CHANNEL2_MODE_BIT] == "1"
        ):
            logging.error(
                f"PSU: {self.name}, "
                f"Channel {self.channels[channel_number - 1].name} "
                "is current limiting"
            )
            return True
        else:
            return False

    def factory_mode(self):
        self._write("FACTORY ON")
