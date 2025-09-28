# Standard imports
from math import sqrt

# Third party imports

# Local imports
from AutomatedTesting.Instruments.Transducer.Transducer import Transducer
from AutomatedTesting.Misc.Units import FieldStrengthUnits, AmplitudeUnits
from AutomatedTesting.Misc.UsefulFunctions import dbm_to_power, amplitude_to_db


class TekboxTBTC1(Transducer):
    def __init__(self):
        super().__init__(
            input_units=FieldStrengthUnits.DBUV_PER_M,
            output_units=AmplitudeUnits.DBM,
            conversion_func_output_to_input=self.conversion_func,
        )

    @staticmethod
    def conversion_func(freq: float, value_in_dbm: float) -> float:
        # Taken from Tekbox TEM Cells Manual
        # Conversion is E (in V/m) = 20 * sqrt(P(in W) * 50Ω)
        power_linear = dbm_to_power(value_in_dbm)
        e_field = 20 * sqrt(power_linear * 50)
        # plus 60 to convert to dBuV/m
        return 60 + amplitude_to_db(e_field)
