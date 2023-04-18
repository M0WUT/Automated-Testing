from copy import copy
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy


def prefixify(x: float, units: str = "", decimal_places: Optional[int] = None) -> str:
    """
    Converts a value to use prefixes (and optionally round to a certain number of decimal places)
    """

    AGILENT_OVERLOAD_MAGIC_NUMBER = 9.9e37

    SI_PREFIXES = {
        1e12: "P",
        1e9: "G",
        1e6: "M",
        1e3: "k",
        1: "",
        1e-3: "m",
        1e-6: "μ",
        1e-9: "n",
        1e-12: "p",
    }

    if x == AGILENT_OVERLOAD_MAGIC_NUMBER:
        return "OVLD"

    for exponent, prefix in SI_PREFIXES.items():
        if x >= exponent:
            x /= exponent

            if decimal_places:
                x = round(x, decimal_places)

            return f"{x}{prefix}{units}"


def readable_freq(freq: float) -> str:
    return prefixify(freq, units="Hz", decimal_places=9)


@dataclass
class StraightLine:
    gradient: float
    intercept: float

    def evaluate(self, x: float) -> float:
        "Evaluates itself at x = <x> and returns the y value"
        return self.gradient * x + self.intercept


def intercept_point(a: StraightLine, b: StraightLine) -> Tuple[float, float]:
    """Takes two straight lines and returns the x and y coordinates that that intercept"""
    assert a.gradient != b.gradient, "Two parallel lines will never intercept"
    x = (b.intercept - a.intercept) / (a.gradient - b.gradient)
    y = a.evaluate(x)
    assert abs(a.evaluate(x) - b.evaluate(x)) < 0.01
    return x, y


def best_fit_line_with_known_gradient(
    xValues: List[float],
    yValues: List[float],
    expectedGradient: float = 3,
    maxErrorPercentage: float = 1,
) -> StraightLine:
    """
    Takes a list of y and x values, attempts to find line by removing data
    from whichever ends has gradient furthest from expected
    """
    assert len(xValues) == len(yValues)
    x = copy(xValues)
    y = copy(yValues)

    # Distortion is probably at the start / end due to
    # noise floor / compression so run a rough check on points
    # with pairwise gradient that's completely outside of spec
    try:
        while abs(((y[1] - y[0]) / (x[1] - x[0])) - expectedGradient) > 1:
            x = x[1:]
            y = y[1:]
    except IndexError:
        return None
    try:
        while abs(((y[-1] - y[-2]) / (x[-1] - x[-2])) - expectedGradient) > 1:
            x = x[:-1]
            y = y[:-1]
    except IndexError:
        return None

    while len(x) >= 4:
        # Best fit line
        gradient, intercept = numpy.polyfit(numpy.array(x), numpy.array(y), 1)
        if (
            1 - maxErrorPercentage / 100
        ) * expectedGradient <= gradient and gradient <= (
            1 + maxErrorPercentage / 100
        ) * expectedGradient:
            # We've found a solution
            return StraightLine(round(gradient, 4), round(intercept, 4))

        # Check whether the top pair or the bottom pair of datapoints
        # have a gradient furthest from the target and discard them
        bottomPairwiseGradient = (y[1] - y[0]) / (x[1] - x[0])
        topPairwiseGradient = (y[-1] - y[-2]) / (x[-1] - x[-2])
        bottomError = abs(bottomPairwiseGradient - expectedGradient)
        topError = abs(topPairwiseGradient - expectedGradient)
        if bottomError > topError:
            x = x[1:]
            y = y[1:]
        else:
            x = x[:-1]
            y = y[:-1]

    return None


if __name__ == "__main__":
    print(prefixify(13.2e6, "Hz", 2))
