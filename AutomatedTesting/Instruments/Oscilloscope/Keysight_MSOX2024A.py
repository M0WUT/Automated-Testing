# Standard imports

# Third party imports
from pyvisa import ResourceManager

# Local imports
from AutomatedTesting.Instruments.Oscilloscope.Oscilloscope import (
    Oscilloscope,
    OscilloscopeChannel,
)

ALLOWED_VOLTS_PER_DIV = [
    10e-3,
    20e-3,
    50e-3,
    100e-3,
    200e-3,
    500e-3,
    1,
    2,
    5,
    10,
    20,
    50,
]


class KeysightMSOX2024A(Oscilloscope):
    def __init__(
        self,
        resource_manager: ResourceManager,
        visa_address: str,
        name: str,
        expected_idn_response: str,
        verify: bool,
        logging_level: int,
        *args,
        **kwargs,
    ):
        self.name = name
        super().__init__(
            resource_manager=resource_manager,
            visa_address=visa_address,
            name=name,
            expected_idn_response=expected_idn_response,
            verify=verify,
            channels=[
                OscilloscopeChannel(
                    channel_num=1,
                    instrument=self,
                    logging_level=logging_level,
                    max_voltage=200,
                    max_frequency=200e6,
                    allowed_volts_per_div=ALLOWED_VOLTS_PER_DIV,
                ),
                OscilloscopeChannel(
                    channel_num=2,
                    instrument=self,
                    logging_level=logging_level,
                    max_voltage=200,
                    max_frequency=200e6,
                    allowed_volts_per_div=ALLOWED_VOLTS_PER_DIV,
                ),
                OscilloscopeChannel(
                    channel_num=3,
                    instrument=self,
                    logging_level=logging_level,
                    max_voltage=200,
                    max_frequency=200e6,
                    allowed_volts_per_div=ALLOWED_VOLTS_PER_DIV,
                ),
                OscilloscopeChannel(
                    channel_num=4,
                    instrument=self,
                    logging_level=logging_level,
                    max_voltage=200,
                    max_frequency=200e6,
                    allowed_volts_per_div=ALLOWED_VOLTS_PER_DIV,
                ),
            ],
            logging_level=logging_level,
            *args,
            **kwargs,
        )

    def set_channel_input_coupling(self, channel_num: int, dc_coupling: bool):
        self._write(f":CHAN{channel_num}:COUP {'DC' if dc_coupling else 'AC'}")

    def get_channel_input_coupling(self, channel_num: int) -> bool:
        """
        Returns True if channel is DC coupled
        """
        return self._query(f":CHAN{channel_num}:COUP?") == "DC"

    def set_channel_display_enabled_state(self, channel_num: int, enabled: bool):
        self._write(f":CHAN{channel_num}:DISP {'1' if enabled else '0'}")

    def get_channel_display_enabled_state(self, channel_num: int) -> bool:
        return self._query(f":CHAN{channel_num}:DISP?") == "1"

    def measure_channel_rms_voltage(self, channel_num: int) -> float:
        x = float(self._query(f":MEAS:VRMS? CYCL,DC,CHAN{channel_num}"))
        if x == 9.9e37:
            return float("inf")
        else:
            return float(x)

    def set_timebase_scale(self, seconds_per_div: float):
        self._write(f":TIM:SCAL {seconds_per_div}")
        if self.verify:
            assert self.get_timebase_scale() == seconds_per_div

    def get_timebase_scale(self) -> float:
        return float(self._query(":TIM:SCAL?"))

    def set_channel_voltage_range(self, channel_num: int, voltage_range: float):
        self._write(f":CHAN{channel_num}:RANG {voltage_range}")

    def get_channel_voltage_range(self, channel_num: int) -> float:
        return float(self._query(f":CHAN{channel_num}:RANG?"))

    def set_channel_voltage_scale(self, channel_num: int, volts_per_div: float):
        self._write(f":CHAN{channel_num}:SCAL {volts_per_div}")

    def get_channel_voltage_scale(self, channel_num: int) -> float:
        return float(self._query(f":CHAN{channel_num}:SCAL?"))
