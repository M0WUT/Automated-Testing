from AutomatedTesting.Instruments.EntireInstrument import EntireInstrument


class DigitalMultimeter(EntireInstrument):

    def measure_dc_voltage(self) -> float:
        raise NotImplementedError

    def measure_dc_current(self) -> float:
        raise NotImplementedError

    def measure_resistance(self) -> float:
        raise NotImplementedError

    def measure_diode_voltage(self) -> float:
        raise NotImplementedError

    def configure_dc_voltage(self, range="DEF", resolution="DEF"):
        raise NotImplementedError

    def configure_dc_current(self, range="DEF", resolution="DEF"):
        raise NotImplementedError

    def configure_resistance(self, range="DEF", resolution="DEF"):
        raise NotImplementedError

    def configure_diode_voltage(self):
        raise NotImplementedError

    def measure_value(self) -> float:
        raise NotImplementedError
