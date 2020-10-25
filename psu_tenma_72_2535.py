from psu import PowerSupply, PowerSupplyChannel
from pyvisa.errors import VisaIOError
from time import sleep


class Tenma_72_2535(PowerSupply):
    """
    Class for Tenma 72-2535 30V/3A PSU
    NB All the sleep() are really important

    Args:
        resourceManager (pyvisa.ResourceManager):
            PyVisa Resource Manager.
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location

    Returns:
        None

    Raises:
        None
    """
    def __init__(self, resourceManager, address):

        self.id = "TENMA 72-2535 V2.1"
        self.channelCount = 1

        channel1 = PowerSupplyChannel(
            channelNumber=1,
            maxVoltage=30.0,
            minVoltage=0.0,
            maxCurrent=3.0,
            minCurrent=0.0
        )

        super().__init__(
            resourceManager=resourceManager,
            channelCount=self.channelCount,
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
            except VisaIOError:
                break
        return ret

    def _write(self, command):
        """
        Writes Data to PSU - needs sleep otherwise data gets dropped

        Args:
            command (str): Command to send

        Returns:
            None

        Raises:
            None
        """
        sleep(0.1)
        self.dev.write(command)

    def _query(self, command):
        """
        Sends command and returns response

        Args:
            command (str): Command to send

        Returns:
            str: Response from PSU

        Raises:
            None
        """
        self._write(command)
        return self._read()

    def set_channel_voltage(self, channelNumber, voltage):
        """
        Attempts to set the voltage on channel <channelNumber>
        to <voltage> Volts

        Args:
            channelNumber (int): Power Supply Channel Number
            voltage (float): Target Voltage in Volts

        Returns:
            None

        Raises:
            AssertionError: If readback setpoint != voltage
            ValueError: If channelNumber is not valid
        """
        super().validate_channel_number(channelNumber)
        self._write(f"VSET{channelNumber}:{round(voltage, 2)}")

    def read_channel_voltage(self, channelNumber):
        """
        Reads voltage setpoint on channel <channelNumber>

        Args:
            channelNumber (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's voltage setpoint

        Raises:
            ValueError: If channelNumber is not valid
        """
        super().validate_channel_number(channelNumber)
        return float(self._query(f"VSET{channelNumber}?"))

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
            ValueError: If channelNumber is not valid
        """
        super().validate_channel_number(channelNumber)
        self._write(f"ISET{channelNumber}:{round(current, 3)}")

    def read_channel_current(self, channelNumber):
        """
        Reads current setpoint on channel <channelNumber>

        Args:
            channelNumber (int): Power Supply Channel Number
                to read

        Returns:
            float: Channel's current setpoint

        Raises:
            ValueError: If channelNumber is not valid
        """
        super().validate_channel_number(channelNumber)
        return float(self._query(f"ISET{channelNumber}?"))


if __name__ == '__main__':
    import pyvisa
    # PyVisa Resource Manager
    rm = pyvisa.ResourceManager('@py')

    psu1 = Tenma_72_2535(rm, "ASRL/dev/ttyACM0::INSTR")
    psu1.channels[0].set_voltage(3.0)
    psu1.channels[0].set_current(0.5)
