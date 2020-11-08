from AutomatedTesting.SignalGenerator.SignalGenerator import \
    SignalGenerator, SignalGeneratorChannel
import logging


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

    def set_channel_power(self, channelNumber, power):
        """
        Sets output power on requested channel

        Args:
            channelNumber (int): Power Supply Channel Number
            power (float): Output power in dBm

        Returns:
            None

        Raises:
            None
        """
        if(round(power, 2) != power):
            logging.warning(
                f"{self.name} has resolution of 0.01dBm."
                f"Requested power of {power}dBm was truncated"
            )
        # Single Channel device so not dependant on channel number
        self._write(f"SOURce:POWer:POWer {round(power, 2)}")

    def read_channel_power(self, channelNumber):
        """
        Reads output power on requested channel

        Args:
            channelNumber (int): Power Supply Channel Number

        Returns:
            float: Channel output power in dBm

        Raises:
            None
        """
        # Single Channel device so not dependant on channel number
        return float(self._query("SOURce:POWer:POWer?"))

    def set_channel_freq(self, channelNumber, freq):
        self._write(f"FREQ {freq}")

    def read_channel_freq(self, channelNumber):
        return float(self._query("FREQ?"))

    def set_channel_modulation(self, channelNumber, modulation):
        raise NotImplementedError  # pragma: no cover

    def read_channel_modulation(self, channelNumber):
        raise NotImplementedError  # pragma: no cover

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
        errors = self._query("SYSTem:ERRor:ALL?").strip()
        if(errors != '0,"No error"'):
            errorList = []
            errorStrings = errors.split('",')

            for x in errorStrings:
                errorCode, errorMessage = x.split(',"')
                # Last item in list isn't comma terminated so need
                # to manually remove trailing speech marks
                if(errorMessage[-1:] == '"'):
                    errorMessage = errorMessage[:-1]
                errorList.append((int(errorCode), errorMessage))
        return errorList

    def check_channel_errors(self, channelNumber):
        # SMB100A has only 1 channel so no channel specific errors
        pass

    def close_remote_session(self):
        self._write("&GTL")
        super().close_remote_session()
