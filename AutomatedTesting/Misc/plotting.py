# Standard imports
from enum import Enum, auto

# Third party imports
from matplotlib.axes import Axes
from numpy import arange

# Local imports
from AutomatedTesting.Misc.UsefulFunctions import readable_freq


class PlotXAxisType(Enum):
    LINEAR = auto()
    LOGARITHMIC = auto()


def apply_default_plot_settings(ax: Axes, x_axis_type: PlotXAxisType) -> None:

    ax.legend()
    ax.grid(axis="both", which="major", color=(0.6, 0.6, 0.6))
    ax.grid(axis="both", which="minor", color=(0.9, 0.9, 0.9))
    ax.set_xscale("log" if x_axis_type == PlotXAxisType.LOGARITHMIC else "linear")


def apply_default_emissions_plot_settings(ax: Axes, x_axis_type: PlotXAxisType) -> None:
    apply_default_plot_settings(ax, x_axis_type)
    start, end = ax.get_ylim()
    start = round(start, -1)
    ax.yaxis.set_ticks(arange(start, end, 10))
    ax.yaxis.set_ticks(arange(start, end, 2), minor=True)
    ax.xaxis.set_major_formatter(lambda x, _: readable_freq(x))
