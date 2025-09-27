from dataclasses import dataclass
from typing import Optional, Any

import numpy
from scipy import stats


def prefixify(x: float, units: str = "", decimal_places: Optional[int] = None) -> str:
    """
    Converts a value to use prefixes
    (and optionally round to a certain number of decimal places)
    """

    agilent_overload_magic_number = 9.9e37

    si_prefixes = {
        1e12: "P",
        1e9: "G",
        1e6: "M",
        1e3: "k",
        1: "",
        1e-3: "m",
        1e-6: "μ",
        1e-9: "n",
        1e-12: "p",
        1e-15: "f",
    }

    if x == agilent_overload_magic_number:
        return "OVLD"

    sign_str = "-" if x < 0 else ""
    x = abs(x)

    if x == 0:
        return f"0{units}"

    for exponent, prefix in si_prefixes.items():
        if x >= exponent:
            x /= exponent

            if decimal_places:
                x = round(x, decimal_places)
            result = str(x)
            result = result.removesuffix(".0")

            return f"{sign_str}{result}{prefix}{units}"
    raise ValueError(f"Could not convert {x} to SI notation")


def get_key_from_dict_value(dict: dict, value: Any):
    reversed_dict = {v: k for k, v in dict.items()}
    return reversed_dict[value]


def readable_freq(freq: float) -> str:
    return prefixify(freq, units="Hz", decimal_places=9)


@dataclass
class StraightLine:
    gradient: float
    intercept: float

    def evaluate(self, x: float) -> float:
        "Evaluates itself at x = <x> and returns the y value"
        return self.gradient * x + self.intercept


def intercept_point(a: StraightLine, b: StraightLine) -> tuple[float, float]:
    """Takes two straight lines and returns the x and y coordinates that intercept"""
    assert a.gradient != b.gradient, "Two parallel lines will never intercept"
    x = (b.intercept - a.intercept) / (a.gradient - b.gradient)
    y = a.evaluate(x)
    assert abs(a.evaluate(x) - b.evaluate(x)) < 0.01
    return x, y


def best_fit_line_with_known_gradient(
    x_values: list[float],
    y_values: list[float],
    expected_gradient: float = 3,
    max_error_percentage: float = 3,
    window_size: int = 11,
) -> Optional[StraightLine]:
    """
    Takes a list of y and x values, attempts to find line by removing data
    from whichever ends has gradient furthest from expected
    """
    assert len(x_values) == len(y_values)
    if window_size % 2 == 0:
        raise NotImplementedError("Only supports odd window sizes")
    x = numpy.array(x_values)
    y = numpy.array(y_values)
    gradients = []

    for end_index in range(window_size, len(y) + 1):
        x_values_in_window = x[end_index - window_size : end_index]
        y_values_in_window = y[end_index - window_size : end_index]
        slope = stats.linregress(
            x_values_in_window, y_values_in_window
        ).slope  # pyright: ignore[reportAttributeAccessIssue]
        gradients.append(slope)

    x = x[int(window_size / 2) :]  # Remove lost values of x at the start
    y = y[int(window_size / 2) :]  # Remove lost values of x at the start

    # Now need to find longest sub-list where the gradient over the
    # window is within 20% of target
    best_start_index = 0
    best_length = 0
    for start_index in range(0, len(gradients)):
        sub_list_length = 0
        while (start_index + sub_list_length < len(gradients)) and (
            0.8 * expected_gradient
            <= gradients[start_index + sub_list_length]
            <= 1.2 * expected_gradient
        ):
            sub_list_length += 1
        if sub_list_length > best_length:
            best_start_index = start_index
            best_length = sub_list_length

    # if expected_gradient == 3:
    #     print(x)
    #     print(gradients)
    #     print(best_start_index)
    #     print(best_length)

    # Now have lists with plausible sub-section gradient
    x = x[best_start_index : best_start_index + best_length + 1]
    y = y[best_start_index : best_start_index + best_length + 1]

    # Now confirm gradient across whole lot and trim if necessary
    while len(x) > 4:
        # if expected_gradient == 3:
        #     print(x)
        #     print(y)

        gradient: float = 0
        intercept: float = 0

        gradient, intercept, _, _, _ = stats.linregress(
            x, y
        )  # pyright: ignore[reportAssignmentType]
        if (
            (1 - max_error_percentage / 100) * expected_gradient
            <= gradient
            <= (1 + max_error_percentage / 100) * expected_gradient
        ):
            return StraightLine(expected_gradient, round(intercept, 4))
        else:
            # Work out slope if remove top or bottom element
            gradient_with_lowest_removed = stats.linregress(
                x[1:], y[1:]
            ).slope  # pyright: ignore[reportAttributeAccessIssue]
            gradient_with_highest_removed = stats.linregress(
                x[:-1], y[:-1]
            ).slope  # pyright: ignore[reportAttributeAccessIssue]

            if abs(gradient_with_highest_removed - expected_gradient) < abs(
                gradient_with_lowest_removed - expected_gradient
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
