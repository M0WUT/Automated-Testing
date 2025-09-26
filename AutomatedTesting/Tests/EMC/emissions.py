# Standard imports
from dataclasses import dataclass
from typing import Optional
from enum import StrEnum

# Third party imports
from matplotlib.axes import Axes

# Local imports
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)
from AutomatedTesting.Misc.units import AmplitudeUnits


class EmissionsType(StrEnum):
    CONDUCTED_VOLTAGE = "Conducted (Voltage)"
    CONDUCTED_CURRENT = "Conducted (Current)"
    RADIATED = "Radiated"


class EmissionsMeasurementRange:
    def __init__(
        self,
        start_freq: float,
        stop_freq: float,
        rbw_hz: float,
        rbw_filter_type: SpectrumAnalyser.FilterType,
        detector_types: list[SpectrumAnalyser.DetectorType],
        # Only one of the two following options should be specified
        seconds_per_mhz: Optional[float] = None,
        total_sweep_time_s: Optional[float] = None,
    ):
        assert stop_freq > start_freq
        self.start_freq = start_freq
        self.stop_freq = stop_freq
        self.rbw_hz = rbw_hz
        self.rbw_filter_type = rbw_filter_type
        self.detector_types = detector_types
        if seconds_per_mhz is not None:
            assert total_sweep_time_s is None
            self.seconds_per_mhz = seconds_per_mhz
        else:
            assert total_sweep_time_s is not None
            self.seconds_per_mhz = total_sweep_time_s / (
                (self.stop_freq - self.start_freq) / 1e6
            )

    def measure(self, sa: SpectrumAnalyser, units: AmplitudeUnits = AmplitudeUnits.DBM):
        return sa.perform_multi_part_sweep(
            self.start_freq,
            self.stop_freq,
            step_size=int(0.5 * self.rbw_hz),
            ensure_stop_freq_is_covered=False,
            detector_types=self.detector_types,
            seconds_per_mhz=self.seconds_per_mhz,
            units=units,
        )


@dataclass
class EmissionsLimitLine:
    """
    Limit is linearly interpolated from (start_freq, start_value)
    to (stop_freq, stop_value). For a constant limit value,
    set start_value and stop_value to same value
    """

    start_freq_hz: float
    stop_freq_hz: float
    start_value: float
    stop_value: float
    detector_type: SpectrumAnalyser.DetectorType

    def evaluate_at_freq(self, freq_hz: float) -> float:
        if not self.start_freq_hz <= freq_hz <= self.stop_freq_hz:
            raise ValueError
        return self.start_value + (self.stop_value - self.start_value) * (
            freq_hz - self.start_freq_hz
        ) / (self.stop_freq_hz - self.start_freq_hz)

    def plot(self, ax: Axes):

        limit_line_style = {
            SpectrumAnalyser.DetectorType.POSITIVE_PEAK: ("r", "solid"),
            SpectrumAnalyser.DetectorType.QUASI_PEAK: ("r", "dotted"),
            SpectrumAnalyser.DetectorType.AVERAGE: ("r", "dashed"),
            SpectrumAnalyser.DetectorType.NEGATIVE_PEAK: ("r", "dashdot"),
        }

        style = limit_line_style[self.detector_type]

        ax.plot(
            [self.start_freq_hz, self.stop_freq_hz],
            [self.start_value, self.stop_value],
            color=style[0],
            linestyle=style[1],
        )


class EmissionsConstantLimitLine(EmissionsLimitLine):
    def __init__(
        self,
        start_freq_hz: float,
        stop_freq_hz: float,
        value: float,
        detector_type: SpectrumAnalyser.DetectorType,
    ):
        super().__init__(start_freq_hz, stop_freq_hz, value, value, detector_type)

    def evaluate_at_freq(self, freq_hz: float) -> float:
        # Might speed things up, don't really know
        return self.start_value


@dataclass
class EmissionsMeasurement:
    name: str
    measurements: list[EmissionsMeasurementRange]
    limits: Optional[list[EmissionsLimitLine]] = None
    units: AmplitudeUnits = AmplitudeUnits.DBM  # Units to be used for plotting / limits

    def measure(
        self, spectrum_analyser: SpectrumAnalyser
    ) -> SpectrumAnalyser.SpectrumAnalyserMeasurements:
        results = SpectrumAnalyser.SpectrumAnalyserMeasurements(datapoints={})
        for x in self.measurements:
            results += x.measure(spectrum_analyser, self.units)
        return results

    def run(self, spectrum_analyser: SpectrumAnalyser, ax: Axes):
        results = self.measure(spectrum_analyser)
        for detector_type, data in results.datapoints.items():
            ax.plot(*zip(*data), label=detector_type.value)

        if self.limits:
            for limit in self.limits:
                limit.plot(ax)

        ax.set_title(self.name)
        ax.set_ylabel(f"Amplitude ({self.units.value})")
