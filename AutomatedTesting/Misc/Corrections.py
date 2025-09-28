# Standard imports

# Third party imports
from numpy import interp

# Local imports
from AutomatedTesting.Misc.UsefulFunctions import readable_freq


class Corrections:
    """
    Class containing S21 between the DUT and the test equipment
    that should be corrected for. Corrections must be initialised with
    a list of (<freq-in-hz>, <s21-in-dB>) tuples. N.B. This is S21, not
    loss so a cable should have negative values for the second item in the
    tuple.

    The returned value from calculate_correction_value
    is the correction (in dB) that should be applied to the requested / measured value
    to give the DUT-referred value. How each instrument handles those
    corrections is up to it. e.g. for a spectrum analyser, it should
    add the correction data from its reading to give measurement
    at the DUT. A signal generator should set its output to the
    requested value plus the correction data (loss will be negative)
    to give the correct signal level at the DUT.
    """

    def __init__(self, corrections: list[tuple[float, float]]):
        self.corrections = sorted(corrections, key=lambda x: x[0])
        self.min_freq = self.corrections[0][0]
        self.max_freq = self.corrections[-1][0]

    def calculate_correction_value(self, freq_hz: float) -> float:
        if not self.min_freq <= freq_hz <= self.max_freq:
            raise ValueError(
                f"Attempted to correct measurement at {readable_freq(freq_hz)}. "
                f"Correction data is valid for {readable_freq(self.min_freq)} - "
                f"{readable_freq(self.max_freq)}"
            )
        return -1 * interp(
            freq_hz, [x[0] for x in self.corrections], [x[1] for x in self.corrections]
        )

    def correct(self, freq_hz: float, value: float) -> float:
        return value + self.calculate_correction_value(freq_hz)


def main():
    x = Corrections([(0, 0), (1e6, -10)])
    print(x.calculate_correction_value(500e3))


if __name__ == "__main__":
    main()
