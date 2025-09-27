# Standard imports
from enum import Enum, auto
from typing import Optional

# Third party imports
from matplotlib.axes import Axes
from matplotlib.ticker import FuncFormatter
from numpy import arange

# Local imports
from AutomatedTesting.Misc.UsefulFunctions import readable_freq
from AutomatedTesting.Misc.units import Units


class PlotXAxisType(Enum):
    LINEAR = auto()
    LOGARITHMIC = auto()


def apply_default_plot_settings(
    ax: Axes,
    x_axis_type: PlotXAxisType = PlotXAxisType.LINEAR,
    x_axis_units: Optional[Units] = None,
    y_axis_type: PlotXAxisType = PlotXAxisType.LINEAR,
    y_axis_units: Optional[Units] = None,
) -> None:

    ax.legend()
    ax.grid(axis="both", which="major", color=(0.6, 0.6, 0.6))
    ax.grid(axis="both", which="minor", color=(0.9, 0.9, 0.9))
    ax.set_xscale("log" if x_axis_type == PlotXAxisType.LOGARITHMIC else "linear")
    ax.set_yscale("log" if y_axis_type == PlotXAxisType.LOGARITHMIC else "linear")
    if x_axis_units:
        x_tick_formatter = FuncFormatter(
            lambda x, pos: f"{str(round(x * x_axis_units.scale_factor(),3)).removesuffix('.0')}"
        )
        ax.xaxis.set_major_formatter(x_tick_formatter)
        ax.set_xlabel(x_axis_units.label())

    if y_axis_units:
        y_tick_formatter = FuncFormatter(
            lambda x, pos: f"{str(round(x * y_axis_units.scale_factor(),3)).removesuffix('.0')}"
        )
        ax.yaxis.set_major_formatter(y_tick_formatter)
        ax.set_ylabel(y_axis_units.label())


def apply_default_emissions_plot_settings(
    ax: Axes,
    x_axis_type: PlotXAxisType = PlotXAxisType.LOGARITHMIC,
    x_axis_units: Optional[Units] = None,
    y_axis_type: PlotXAxisType = PlotXAxisType.LINEAR,
    y_axis_units: Optional[Units] = None,
) -> None:
    apply_default_plot_settings(
        ax, x_axis_type, x_axis_units, y_axis_type, y_axis_units
    )
    start, end = ax.get_ylim()
    start = round(start, -1)
    ax.yaxis.set_ticks(arange(start, end, 10))
    ax.yaxis.set_ticks(arange(start, end, 2), minor=True)
    if x_axis_type == PlotXAxisType.LOGARITHMIC:
        ax.xaxis.set_major_formatter(lambda x, _: readable_freq(x))
