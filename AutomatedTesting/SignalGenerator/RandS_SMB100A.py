from AutomatedTesting.SignalGenerator.SignalGenerator import \
    SignalGenerator, SignalGeneratorChannel


class RandS_SMB100A(SignalGenerator):
    """
    Class for Rohde and Schwarz SMB100A

    Args:
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location

    Returns:
        None

    Raises:
        None
    """
    def __init__(self, address, name="SMB100A"):

        channel1 = SignalGeneratorChannel(
            channelNumber=1,
            maxPower=30,
            minPower=-145,
            maxFreq=12.75e9,
            minFreq=100e3
        )

        super().__init__(
            id="Rohde&Schwarz,SMB100A,1406.6000k03/180437,"
               "3.1.19.15-3.20.390.24",
            name=name,
            channelCount=1,
            channels=[channel1],
            address=address
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
            f"OUTP {1 if bool(enabled) else 0}",
            acquireLock=True
        )

    def close_remote_session(self):
        self._write("&GTL")
        super().close_remote_session()
