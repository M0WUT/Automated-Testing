from copy import copy
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy
from scipy import stats


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
            x = str(x)
            x.removesuffix(".0")

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
    maxErrorPercentage: float = 3,
    window_size: int = 11,
) -> StraightLine:
    """
    Takes a list of y and x values, attempts to find line by removing data
    from whichever ends has gradient furthest from expected
    """
    assert len(xValues) == len(yValues)
    if window_size % 2 == 0:
        raise NotImplementedError("Only supports odd window sizes")
    x = numpy.array(xValues)
    y = numpy.array(yValues)
    gradients = []

    for end_index in range(window_size, len(y) + 1):
        x_values_in_window = x[end_index - window_size : end_index]
        y_values_in_window = y[end_index - window_size : end_index]
        slope = stats.linregress(x_values_in_window, y_values_in_window).slope
        gradients.append(slope)

    x = x[int(window_size / 2) :]  # Remove lost values of x at the start
    y = y[int(window_size / 2) :]  # Remove lost values of x at the start

    # Now need to find longest sub-list where the gradient over the window is within 20% of target
    best_start_index = 0
    best_length = 0
    for start_index in range(0, len(gradients)):
        sub_list_length = 0
        while (start_index + sub_list_length < len(gradients)) and (
            0.8 * expectedGradient
            <= gradients[start_index + sub_list_length]
            <= 1.2 * expectedGradient
        ):
            sub_list_length += 1
        if sub_list_length > best_length:
            best_start_index = start_index
            best_length = sub_list_length

    # if expectedGradient == 3:
    #     print(x)
    #     print(gradients)
    #     print(best_start_index)
    #     print(best_length)

    # Now have lists with plausible sub-section gradient
    x = x[best_start_index : best_start_index + best_length + 1]
    y = y[best_start_index : best_start_index + best_length + 1]

    # Now confirm gradient across whole lot and trim if necessary
    while len(x) > 4:
        # if expectedGradient == 3:
        #     print(x)
        #     print(y)
        gradient, intercept, _, _, _ = stats.linregress(x, y)
        if (
            (1 - maxErrorPercentage / 100) * expectedGradient
            <= gradient
            <= (1 + maxErrorPercentage / 100) * expectedGradient
        ):
            print("FOU*ND ONE")
            return StraightLine(round(gradient, 4), round(intercept, 4))
        else:
            # Work out slope if remove top or bottom element
            gradient_with_lowest_removed = stats.linregress(x[1:], y[1:]).slope
            gradient_with_highest_removed = stats.linregress(x[:-1], y[:-1]).slope

            if abs(gradient_with_highest_removed - expectedGradient) < abs(
                gradient_with_lowest_removed - expectedGradient
            ):
                x = x[:-1]
                y = y[:-1]
            else:
                x = x[1:]
                y = y[1:]

    # Failed to find appropriate line
    return None


if __name__ == "__main__":
    print(prefixify(13.2e6, "Hz", 2))
