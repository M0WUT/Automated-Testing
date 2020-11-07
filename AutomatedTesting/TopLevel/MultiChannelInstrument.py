from AutomatedTesting.TopLevel.BaseInstrument import BaseInstrument
import logging


class MultiChannelInstrument(BaseInstrument):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate_channel_number(self, channelNumber):
        """
        Throws Error if channelNumber is invalid for that device

        Args:
            channelNumber (int): proposed Channel Number

        Returns:
            None

        Raises:
            ValueError: If Channel Number is not valid
        """
        if(
            int(channelNumber) != channelNumber or
            channelNumber < 0 or
            channelNumber > self.channelCount
        ):
            raise ValueError(
                f"Invalid channel number {channelNumber} for "
                f"{self.name}"
            )

    def reserve_channel(self, channelNumber, name):
        """
        Marks Instrument Channel as reserved and assigns a name to it

        Args:
            channelNumber (int): proposed Channel Number to reserve
            name (str): name to identify channel purpose

        Returns:
            PowerSupplyChannel: the reserved channel

        Raises:
            AssertionError: If requested channel is already reserved
        """
        self.validate_channel_number(channelNumber)
        assert self.channels[channelNumber - 1].reserved is False, \
            f"Channel {channelNumber} on Instrument {self.name} already " \
            f"reserved for \"{self.channels[channelNumber - 1].name}\""

        self.channels[channelNumber - 1].reserved = True
        self.channels[channelNumber - 1].name = f"\"{name}\""
        logging.info(
            f"Instrument: {self.name}, Channel {channelNumber} "
            f"reserved for \"{name}\""
        )
        return self.channels[channelNumber - 1]

    def cleanup(self):
        """
        Returns instrument to a safe state

        Args:
            None

        Returns:
            None

        Raises:
            None
        """
        for x in self.channels:
            x.cleanup()
        super().cleanup()
        logging.info(f"Instrument: {self.name} Shutdown")
