# Standard imports
import math

# Third party imports
import pytest

# Local imports
from AutomatedTesting.Instruments.InstrumentConfig import ssa3032x
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)


@pytest.fixture(scope="function")
def sa(spectrum_analyser):
    with spectrum_analyser:
        yield spectrum_analyser


pytestmark = pytest.mark.parametrize("spectrum_analyser", [ssa3032x])


def test_min_freq(sa: SpectrumAnalyser):
    sa.set_start_freq(sa.min_freq)
    with pytest.raises(ValueError):
        sa.set_start_freq(sa.max_freq + 1)
    if sa.min_freq > 0:
        with pytest.raises(ValueError):
            sa.set_start_freq(sa.min_freq - 1)


def test_max_freq(sa: SpectrumAnalyser):
    sa.set_stop_freq(sa.max_freq)
    with pytest.raises(ValueError):
        sa.set_stop_freq(sa.max_freq + 1)


def test_centre_freq(sa: SpectrumAnalyser):
    sa.set_centre_freq(sa.min_freq + math.ceil(0.5 * sa.min_span))
    sa.set_centre_freq(sa.max_freq - math.ceil(0.5 * sa.min_span))
    with pytest.raises(ValueError):
        sa.set_centre_freq(sa.max_freq + 1)
    with pytest.raises(AssertionError):
        sa.set_centre_freq(sa.min_freq + math.ceil(0.5 * sa.min_span) - 1)
    with pytest.raises(AssertionError):
        sa.set_centre_freq(sa.max_freq + 1 - math.ceil(0.5 * sa.min_span))


def test_span(sa: SpectrumAnalyser):
    sa.set_span(sa.min_span)
    sa.set_span(sa.max_span)
    with pytest.raises(ValueError):
        sa.set_span(sa.min_span - 1)
    with pytest.raises(ValueError):
        sa.set_span(sa.max_span + 1)
    with pytest.raises(ValueError):
        sa.set_span(0)
    sa.set_zero_span()


def test_rbw(sa: SpectrumAnalyser):
    # Kinda tricky to define as it's normally a discrete list
    # Most Spectrum Analysers will support RBW = 1MHz
    # Most Spectrum Analyser will not support RBW = 277kHz (random number)
    sa.set_rbw(1e6)
    with pytest.raises(ValueError):
        sa.set_rbw(277e3)


def test_vbw(sa: SpectrumAnalyser):
    # Kinda tricky to define as it's normally a discrete list
    # Most Spectrum Analysers will support VBW = 1MHz
    # Most Spectrum Analyser will not support VBW = 277kHz (random number)
    sa.set_vbw(1e6)
    with pytest.raises(ValueError):
        sa.set_vbw(277e3)


def test_rbw_vbw_ratio(sa: SpectrumAnalyser):
    # Kinda tricky to define as it's normally a discrete list
    # Most Spectrum Analysers will support VBW = RBW
    # Most Spectrum Analyser will not support VBW = 27 * RBW
    sa.set_vbw_rbw_ratio(1)
    with pytest.raises(AssertionError):
        sa.set_vbw_rbw_ratio(27)


def test_sweep_points(sa: SpectrumAnalyser):
    sa.set_sweep_points(sa.min_sweep_points)
    with pytest.raises(ValueError):
        sa.set_sweep_points(sa.min_sweep_points - 1)
    sa.set_sweep_points(sa.max_sweep_points)
    with pytest.raises(ValueError):
        sa.set_sweep_points(sa.max_sweep_points + 1)


def test_input_attenuation(sa: SpectrumAnalyser):
    sa.set_input_attenuation(sa.min_attenuation)
    sa.set_input_attenuation(sa.max_attenuation)
    with pytest.raises(ValueError):
        sa.set_input_attenuation(sa.min_attenuation - 1)
    with pytest.raises(ValueError):
        sa.set_input_attenuation(sa.max_attenuation + 1)


def test_ref_level(sa: SpectrumAnalyser):
    # Not really testing anything here, just that the function is implemented
    sa.set_ref_level(-20)


def test_trace_data(sa: SpectrumAnalyser):
    # Not really testing anything here, just that the function is implemented
    sa.trigger_sweep()
    sa.get_trace_data()


def test_marker_power(sa: SpectrumAnalyser):
    sa.set_start_freq(sa.min_freq)
    sa.set_stop_freq(sa.max_freq)
    sa.measure_power(0.5 * (sa.min_freq + sa.max_freq))
    sa.disable_marker(1)
    with pytest.raises(ValueError):
        sa.set_marker_enabled_state(sa.max_num_markers + 1, True)
    with pytest.raises(ValueError):
        sa.get_marker_enabled_state(sa.max_num_markers + 1)
    with pytest.raises(ValueError):
        sa.set_marker_frequency(sa.min_freq, sa.max_num_markers + 1)
    with pytest.raises(ValueError):
        sa.get_marker_frequency(sa.max_num_markers + 1)
    with pytest.raises(ValueError):
        sa.measure_marker_power(sa.max_num_markers + 1)
    with pytest.raises(ValueError):
        sa.measure_power(sa.min_freq, sa.max_num_markers + 1)


def test_instrument_errors(sa: SpectrumAnalyser):
    sa.get_instrument_errors()
