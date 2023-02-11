from time import sleep

from AutomatedTesting.Instruments.DigitalMultimeter.DigitalMultimeter import (
    DigitalMultimeter,
)


class Agilent34401A(DigitalMultimeter):
    def set_remote_control(self):
        self._write(":SYST:REM")
        sleep(1)

    def set_local_control(self):
        self._write(":SYST:LOC")
        sleep(1)

    def cleanup(self):
        self.set_local_control()
        super().cleanup()

    def reset(self):
        """
        Resets the device and clears all errors
        """
        self._write("*RST")
        sleep(1)

        self._write("*CLS")

    def measure_dc_voltage(self) -> float:
        return float(self._query("MEAS:VOLT:DC? DEF,DEF"))

    def measure_dc_current(self) -> float:
        return float(self._query("MEAS:CURR:DC? 1,DEF"))
