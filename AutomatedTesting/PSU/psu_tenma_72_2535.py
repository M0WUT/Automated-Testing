from AutomatedTesting.PSU.psu import PowerSupply, PowerSupplyChannel
from pyvisa.errors import VisaIOError
import logging


class Tenma_72_2535(PowerSupply):
    """
    Class for Tenma 72-2535 30V/3A PSU
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
    def __init__(self, address):

        channel1 = PowerSupplyChannel(
            channelNumber=1,
            maxVoltage=30.0,
            minVoltage=0.0,
            maxCurrent=3.0,
            minCurrent=0.0
        )

        super().__init__(
            id="TENMA 72-2535 V2.1",
            name="Tenma 72-2535",
            channelCount=1,
            channels=[channel1],
            hasOVP=True,
            hasOCP=True,
            address=address,
            baud_rate=9600,
            read_termination=None,
            write_termination=None,
            timeout=500
        )

    def read_id(self):
        """
        Queries PSU Device ID

        Args:
            None

        Returns:
            str: Device ID String

        Raises:
            None
        """
        return self._query("*IDN?")

    def _read(self):
        """
        Reads data from PSU as it's infernal with no termination

        Args:
            None

        Returns:
            str: Device ID String

        Raises:
            None
        """
        ret = ""
        while(1):
            try:
                ret += (self.dev.read_bytes(1).decode("utf-8"))
            except VisaIOError as e:
                if ret == "":
                    raise e
                else:
                    return ret

    def set_channel_voltage(self, channelNumber, voltage):
        """
        Sets the voltage on channel <channelNumber>
        to <voltage> Volts

        Args:
            channelNumber (int): Power Supply Channel Number
            voltage (float): Target Voltage in Volts

        Returns:
            None

        Raises:
            None
        """
        self._write(
            f"VSET{channelNumber}:{round(voltage, 2)}",
            acquireLock=True
        )

    def read_channel_voltage_setpoint(self, channelNumber):
        """
        Reads voltage setpoint on channel <channelNumber>

        Args:
            channelNumber (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's voltage setpoint

        Raises:
            None
        """
        return float(self._query(f"VSET{channelNumber}?"))

    def measure_channel_voltage(self, channelNumber):
        """
        Reads output voltage on channel <channelNumber>

        Args:
            channelNumber (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's output voltage in Volts

        Raises:
            None
        """
        return float(self._query(f"VOUT{channelNumber}?"))

    def set_channel_current(self, channelNumber, current):
        """
        Attempts to set the current on channel <channelNumber>
        to <current> Amps

        Args:
            channelNumber (int): Power Supply Channel Number
            current (float): Target Current in Amps

        Returns:
            None

        Raises:
            None
        """
        self._write(
            f"ISET{channelNumber}:{round(current, 3)}",
            acquireLock=True
        )

    def read_channel_current_setpoint(self, channelNumber):
        """
        Reads current setpoint on channel <channelNumber>

        Args:
            channelNumber (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's current setpoint

        Raises:
            None
        """
        return float(self._query(f"ISET{channelNumber}?"))

    def measure_channel_current(self, channelNumber):
        """
        Reads output current on channel <channelNumber>

        Args:
            channelNumber (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's output current in Amps

        Raises:
            None
        """
        return float(self._query(f"IOUT{channelNumber}?"))

    def enable_channel_output(self, channelNumber, enabled):
        """
        Enables / Disables channel output

        Args:
            channelNumber (int): Power Supply Channel Number
            enabled (bool): 0 = Disable output, 1 = Enable output

        Returns:
            None

        Raises:
            AssertionError: If enabled is not 0/1 or True/False
        """
        assert enabled in {True, False, 0, 1}
        self._write(
            f"OUT{1 if bool(enabled) else 0}",
            acquireLock=True
        )

    def check_channel_errors(self, channelNumber):
        """
        Checks for errors on channel with output enabled
        Errors are:
            Output channel has become disabled due to error
            Output channel is in constant current mode

        Args:
            channelNumber (int): Power Supply Channel Number

        Returns:
            bool: True if channel has errors

        Raises:
            None
        """

        # Get status byte and convert to string in reverse
        # order so status[0] = bit 0
        status = ord(self._query("STATUS?"))
        status = format(status, '08b')[::-1]

        # Only have one channel on this device
        if(status[0] == '0'):
            logging.error(
                f"PSU: {self.name}, "
                f"Channel {self.channels[channelNumber - 1].name} "
                "is current limiting"
            )
            return True
        elif (status[6] == '0'):
            logging.error(
                f"PSU: {self.name}, "
                f"Channel {self.channels[channelNumber - 1].name} "
                "has tripped protection circuitry"
            )
            return True
        else:
            return False
