import logging

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.Oscilloscope.Oscilloscope import (
    Oscilloscope,
    OscilloscopeChannel,
)


class Keysight_MSOX2024A(Oscilloscope):
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
            channel_count=4,
            channels=[
                OscilloscopeChannel(
                    channel_number=1,
                    instrument=self,
                    logger=logger,
                    max_voltage=200,
                    max_frequency=200e6,
                ),
                OscilloscopeChannel(
                    channel_number=2,
                    instrument=self,
                    logger=logger,
                    max_voltage=200,
                    max_frequency=200e6,
                ),
                OscilloscopeChannel(
                    channel_number=3,
                    instrument=self,
                    logger=logger,
                    max_voltage=200,
                    max_frequency=200e6,
                ),
                OscilloscopeChannel(
                    channel_number=4,
                    instrument=self,
                    logger=logger,
                    max_voltage=200,
                    max_frequency=200e6,
                ),
            ],
            logger=logger,
            *args,
            **kwargs,
        )

    def set_channel_input_coupling(self, channel_number: int, dc_coupling: bool):
        self._write(f":CHAN{channel_number}:COUP {'DC' if dc_coupling else 'AC'}")

    def get_channel_input_coupling(self, channel_number: int) -> bool:
        """
        Returns True if channel is DC coupled
        """
        return self._query(f":CHAN{channel_number}:COUP?") == "DC"

    def set_channel_display_enabled_state(self, channel_number: int, enabled: bool):
        self._write(f":CHAN{channel_number}:DISP {'1' if enabled else '0'}")

    def get_channel_display_enabled_state(self, channel_number: int) -> bool:
        return self._query(f":CHAN{channel_number}:DISP?") == "1"
