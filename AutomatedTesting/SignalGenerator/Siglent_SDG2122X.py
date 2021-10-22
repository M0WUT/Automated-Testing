from AutomatedTesting.SignalGenerator.SignalGenerator import \
    SignalGenerator, SignalGeneratorChannel


class Siglent_SDG2122X(SignalGenerator):
    """
    Class for Siglent 2122X

    Args:
        address (str):
            PyVisa String e.g. "GPIB0::14::INSTR"
            with device location

    Returns:
        None

    Raises:
        None
    """
    def __init__(self, address, name="SDG2122X"):

        channel1 = SignalGeneratorChannel(
            channelNumber=1,
            maxPower=30,
            minPower=-145,
            maxFreq=120e6,
            minFreq=1e-6
        )

        channel2 = SignalGeneratorChannel(
            channelNumber=2,
            maxPower=30,
            minPower=-145,
            maxFreq=120e6,
            minFreq=1e-6
        )

        super().__init__(
            id="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",
            name=name,
            channelCount=2,
            channels=[channel1, channel2],
            address=address
        )

    #################################
    # Inheritied function overrides #
    #################################

    def initialise(self, resourceManager, supervisor):
        super().initialise(resourceManager, supervisor)
        self.set_output_load_50R()
        self.set_wavetype_sine()

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
        assert isinstance(enabled, bool)
        self._write(
            f"C{channelNumber} OUTP {1 if bool(enabled) else 0}"
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
        self._write(f"C{channelNumber}:BSWV AMPDBM,{power}")

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
        channelStatus = self._query(f"C{channelNumber}:BSWV?")
        return float(channelStatus.split("AMPDBM,")[1].split("d")[0])

    def set_channel_freq(self, channelNumber, freq):
        assert round(freq) == freq, "Frequency must be integer number of Hz"
        self._write(f"C{channelNumber}:BSWV FRQ,{freq}")

    def read_channel_freq(self, channelNumber):
        channelStatus = self._query(f"C{channelNumber}:BSWV?")
        freq = float(channelStatus.split("FRQ,")[1].split("HZ")[0])
        return freq

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
        return []

    def check_channel_errors(self, channelNumber):
        # SMB100A has only 1 channel so no channel specific errors
        pass

    def close_remote_session(self):
        super().close_remote_session()

    #############################
    # Device specific functions #
    #############################

    def set_output_load_50R(self):
        # Set all calculations to be in 50 ohm mode
        self._write("C1:OUTP LOAD,50")
        self._write("C2:OUTP LOAD,50")

    def set_output_load_hiz(self):
        self._write("C1:OUTP LOAD,HZ")
        self._write("C2:OUTP LOAD,HZ")

    def set_wavetype_sine(self):
        self._write("C1:BSWV WVTP SINE")
        self._write("C2:BSWV WVTP SINE")
