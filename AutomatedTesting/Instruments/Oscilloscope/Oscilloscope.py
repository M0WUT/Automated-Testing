import logging

from AutomatedTesting.Instruments.MultichannelInstrument import (
    InstrumentChannel,
    MultichannelInstrument,
)


class OscilloscopeChannel(InstrumentChannel):
    def __init__(
        self,
        channel_number: int,
        instrument: MultichannelInstrument,
        logger: logging.Logger,
        max_voltage: float,
        max_frequency: float,
        allowed_volts_per_div: list[float],
    ):
        self.max_voltage = max_voltage
        self.max_frequency = max_frequency
        self.allowed_volts_per_div = allowed_volts_per_div
        super().__init__(
            channel_number=channel_number, instrument=instrument, logger=logger
        )

    def _reserve(self, purpose: str):
        super()._reserve(purpose)
        self.enable_display()
        return self

    def free(self):
        self.disable_display()
        super().free()

    def set_output_enabled_state(self, enabled: bool):
        """
        Have to implement as this function is called during setup / teardown of
        multi-channel instruments
        """
        pass

    def set_input_coupling(self, dc_coupling: bool = False):
        self.instrument.set_channel_input_coupling(
            channel_number=self.channel_number, dc_coupling=dc_coupling
        )
        if self.instrument.verify:
            assert self.get_input_coupling() == dc_coupling

    def get_input_coupling(self) -> bool:
        """
        Returns True if the input is dc_coupled
        """
        dc_coupled = self.instrument.get_channel_input_coupling(
            channel_number=self.channel_number
        )
        return dc_coupled

    def set_input_coupling_ac(self):
        self.set_input_coupling(dc_coupling=False)

    def set_input_coupling_dc(self):
        self.set_input_coupling(dc_coupling=True)

    def set_display_enabled_state(self, enabled: bool):
        """
        En/disables the channel on the oscilloscope
        """
        self.instrument.set_channel_display_enabled_state(self.channel_number, enabled)
        if self.instrument.verify:
            assert self.get_display_enabled_state() == enabled

    def get_display_enabled_state(self) -> bool:
        """
        Returns True if the channel display is enabled
        """
        return self.instrument.get_channel_display_enabled_state(self.channel_number)

    def enable_display(self):
        self.set_display_enabled_state(True)

    def disable_display(self):
        self.set_display_enabled_state(False)

    def measure_rms(self) -> float:
        """
        Measures RMS voltage in Volts
        """
        return self.instrument.measure_channel_rms_voltage(self.channel_number)

    def set_voltage_range(self, voltage_range: float):
        """
        Sets maximum range in Volts
        """
        self.instrument.set_channel_voltage_range(self.channel_number, voltage_range)
        if self.instrument.verify:
            assert self.get_voltage_range() == voltage_range

    def get_voltage_range(self) -> float:
        """
        Returns full scale range in Volts
        """
        return float(self.instrument.get_channel_voltage_range(self.channel_number))

    def set_voltage_scale(self, volts_per_div: float):
        """
        Sets Volts per division
        """
        self.instrument.set_channel_voltage_scale(self.channel_number, volts_per_div)
        if self.instrument.verify:
            assert self.get_voltage_scale() == volts_per_div

    def get_voltage_scale(self) -> float:
        """
        Returns Volts per division
        """
        return float(self.instrument.get_channel_voltage_scale(self.channel_number))


class Oscilloscope(MultichannelInstrument):
    def initialise(self):
        super().initialise()
        if self.only_software_control:
            for x in self.channels:
                x.disable_display()
                x.set_input_coupling_ac()

    def set_channel_input_coupling(self, channel_number: int, dc_coupling: bool):
        raise NotImplementedError

    def get_channel_input_coupling(self, channel_number: int) -> bool:
        """
        Returns True if channel is DC coupled
        """
        raise NotImplementedError

    def set_channel_display_enabled_state(self, channel_number: int, enabled: bool):
        raise NotImplementedError

    def get_channel_display_enabled_state(self, channel_number: int) -> bool:
        """
        Returns True if the channel is enabled
        """
        raise NotImplementedError

    def measure_channel_rms_voltage(self, channel_number: int) -> float:
        raise NotImplementedError

    def set_timebase_scale(self, seconds_per_div: float):
        raise NotImplementedError

    def get_timebase_scale(self) -> float:
        """
        Returns in seconds per division
        """
        raise NotImplementedError

    def set_channel_voltage_range(self, channel_number: int, voltage_range: float):
        """
        Sets channel full scale range in Volts
        """
        raise NotImplementedError

    def get_channel_voltage_range(self, channel_number: int) -> float:
        """
        Returns channel full scale range in Volts
        """
        raise NotImplementedError
