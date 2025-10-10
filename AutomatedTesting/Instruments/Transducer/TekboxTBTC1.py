# Standard imports
from math import log10

# Third party imports

# Local imports
from AutomatedTesting.Instruments.Transducer.Transducer import Transducer
from AutomatedTesting.Misc.Units import FieldStrengthUnits, AmplitudeUnits

# from AutomatedTesting.Misc.UsefulFunctions import dbm_to_power, amplitude_to_db


class TekboxTBTC1(Transducer):
    def __init__(self):
        super().__init__(
            input_units=FieldStrengthUnits.DBUV_PER_M,
            output_units=AmplitudeUnits.DBUV,
            conversion_func_output_to_input=self.conversion_func,
        )

    @staticmethod
    def conversion_func(freq: float, value_in_dbuv: float) -> float:
        # Taken from Tekbox TEM Cells Manual
        # Conversion is E (in V/m) = 20 * sqrt(P(in W) * 50Ω)

        # This a trivial conversion in the septum gap is 50cm
        # i.e. 1/20 of a metre so field strength = voltage / (1/20 metre)

        # power_linear = dbm_to_power(value_in_dbm)
        # e_field = 20 * sqrt(power_linear * 50)
        # # plus 120 to convert to dBuV/m
        # return 120 + amplitude_to_db(e_field)
        antenna_factor = 20 * log10(20)
        return value_in_dbuv + antenna_factor


def main():
    x = TekboxTBTC1()
    print(x.conversion_func(0, -105))


if __name__ == "__main__":
    main()
