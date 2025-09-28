# Standard imports
from enum import StrEnum

# Third party imports

# Local imports


# Base class for all units
class Units(StrEnum):

    def scale_factor(self) -> float:
        """
        Returns scale factor to multiply values in base units
        e.g. Volts / Amps / Hz to convert to specified unit

        """
        raise NotImplementedError

    def label(self) -> str:
        """
        Returns a str that could be used to label an axis
        of a graph plotted in this unit
        """
        raise NotImplementedError


class AmplitudeUnits(Units):

    DBM = "dBm"
    DBMV = "dBmV"
    DBUV = "dBµV"
    VOLTS = "V"
    WATTS = "W"
    DBUA = "dBµA"

    def scale_factor(self) -> float:
        # Don't really know what to do here as it's not just
        # SI prefixes
        return 1

    def label(self) -> str:
        return f"Amplitude ({self.value})"


class FieldStrengthUnits(Units):
    DBUV_PER_M = "dBµV/m"
    DBUA_PER_M = "dBµA/m"

    def scale_factor(self) -> float:
        # Don't really know what to do here as it's not just
        # SI prefixes
        return 1

    def label(self) -> str:
        return f"Field Strength ({self.value})"


class FrequencyUnits(Units):
    GHZ = "GHz"
    MHZ = "MHz"
    KHZ = "kHz"
    HZ = "Hz"

    def scale_factor(self) -> float:
        factors = {
            FrequencyUnits.GHZ: 1 / 1e9,
            FrequencyUnits.MHZ: 1 / 1e6,
            FrequencyUnits.KHZ: 1 / 1e3,
            FrequencyUnits.HZ: 1,
        }
        return factors[self]

    def label(self) -> str:
        return f"Frequency ({self.value})"


class TimeUnits(Units):
    HOURS = "h"
    MINUTES = "min"
    SECONDS = "s"
    MILLISECONDS = "ms"
    MICROSECONDS = "µs"
    NANOSECONDS = "ns"
    PICOSECONDS = "ps"

    def scale_factor(self) -> float:
        factors = {
            TimeUnits.HOURS: 1 / 3600,
            TimeUnits.MINUTES: 1 / 60,
            TimeUnits.SECONDS: 1,
            TimeUnits.MILLISECONDS: 10e3,
            TimeUnits.MICROSECONDS: 10e6,
            TimeUnits.NANOSECONDS: 10e9,
            TimeUnits.PICOSECONDS: 10e12,
        }
        return factors[self]

    def label(self) -> str:
        return f"Time ({self.value})"
