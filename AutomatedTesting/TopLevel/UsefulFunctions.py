from dataclasses import dataclass
from typing import List, Tuple
from copy import copy
import numpy
import logging


def readable_freq(freq):
    """
    Converts frequency in Hz to human readable
    form.

    Args:
        freq (float): Frequency in Hz

    Returns:
        str: Frequency as nicely formatted string

    Raises:
        None
    """
    if(freq >= 1e9):
        divider = 1e9
        units = "GHz"
    elif(freq >= 1e6):
        divider = 1e6
        units = "MHz"
    elif(freq >= 1e3):
        divider = 1e3
        units = "kHz"
    else:
        divider = 1
        units = "Hz"

    x = str(freq / divider)

    # See if we can trim annoying ".0" that
    # Python puts on integer floats
    if x[-2:] == '.0':
        x = x[:-2]
    return x + units


@dataclass
class StraightLine():
    gradient: float
    intercept: float

    def evaluate(self, x: float) -> float:
        "Evaluates itself at x = <x> and returns the y value"
        return self.gradient * x + self.intercept


def intercept_point(a: StraightLine, b: StraightLine) -> Tuple[float, float]:
    """ Takes two straight lines and returns the x and y coordinates that that intercept"""
    assert a.gradient != b.gradient, "Two parallel lines will never intercept"
    x = (b.intercept - a.intercept) / (a.gradient - b.gradient)
    y = a.evaluate(x)
    assert abs(a.evaluate(x) - b.evaluate(x)) < 0.01
    return x, y


def best_fit_line_with_known_gradient(
    xValues: List[float],
    yValues: List[float],
    expectedGradient: float = 3,
    maxErrorPercentage: float = 1.5
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
        gradient, intercept = numpy.polyfit(
            numpy.array(x),
            numpy.array(y),
            1
        )
        if (
            (1 - maxErrorPercentage / 100) * expectedGradient <= gradient and
            gradient <= (1 + maxErrorPercentage / 100) * expectedGradient
        ):
            # We've found a solution
            return StraightLine(
                round(gradient, 4), round(intercept, 4)
            )

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
if __name__ == '__main__':
    print(readable_freq(50e6))
