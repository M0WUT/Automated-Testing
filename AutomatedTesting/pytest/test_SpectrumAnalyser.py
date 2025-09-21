# Standard imports
import math

# Third party imports
import pytest

# Local imports
from AutomatedTesting.Instruments.InstrumentConfig import ssa3032x
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)


pytestmark = pytest.mark.parametrize("spectrum_analyser", [ssa3032x])


@pytest.fixture()
def sa(spectrum_analyser):
    with spectrum_analyser:
        yield spectrum_analyser


def test_parameter_validation(spectrum_analyser):
    # Check max_freq < min_freq validation
    with pytest.raises(ValueError):
        _ = SpectrumAnalyser(
            resource_manager=None,  # type: ignore
            visa_address=None,  # type: ignore
            name=None,  # type: ignore
            expected_idn_response=None,  # type: ignore
            verify=None,  # type: ignore
            logger=None,  # type: ignore
            min_freq=int(2e9),
            max_freq=int(1e9),
            min_num_sweep_points=10,
            max_num_sweep_points=10,
            min_span=10,
            max_span=10,
            min_attenuation_db=None,  # type: ignore
            max_attenuation_db=None,  # type: ignore
            has_preamp=None,  # type: ignore
            supported_rbw=None,  # type: ignore
            supported_vbw=None,  # type: ignore
            max_num_traces=None,  # type: ignore
            max_num_markers=None,  # type: ignore
            supports_emi_measurements=None,  # type: ignore
        )
    # Check max_num_sweep_points < min_num_sweep_points validation
    with pytest.raises(ValueError):
        _ = SpectrumAnalyser(
            resource_manager=None,  # type: ignore
            visa_address=None,  # type: ignore
            name=None,  # type: ignore
            expected_idn_response=None,  # type: ignore
            verify=None,  # type: ignore
            logger=None,  # type: ignore
            min_freq=int(1e9),
            max_freq=int(2e9),
            min_num_sweep_points=11,
            max_num_sweep_points=10,
            min_span=10,
            max_span=10,
            min_attenuation_db=None,  # type: ignore
            max_attenuation_db=None,  # type: ignore
            has_preamp=None,  # type: ignore
            supported_rbw=None,  # type: ignore
            supported_vbw=None,  # type: ignore
            max_num_traces=None,  # type: ignore
            max_num_markers=None,  # type: ignore
            supports_emi_measurements=None,  # type: ignore
        )

    # Check max_span < min_span validation
    with pytest.raises(ValueError):
        _ = SpectrumAnalyser(
            resource_manager=None,  # type: ignore
            visa_address=None,  # type: ignore
            name=None,  # type: ignore
            expected_idn_response=None,  # type: ignore
            verify=None,  # type: ignore
            logger=None,  # type: ignore
            min_freq=int(1e9),
            max_freq=int(2e9),
            min_num_sweep_points=10,
            max_num_sweep_points=10,
            min_span=11,
            max_span=10,
            min_attenuation_db=None,  # type: ignore
            max_attenuation_db=None,  # type: ignore
            has_preamp=None,  # type: ignore
            supported_rbw=None,  # type: ignore
            supported_vbw=None,  # type: ignore
            max_num_traces=None,  # type: ignore
            max_num_markers=None,  # type: ignore
            supports_emi_measurements=None,  # type: ignore
        )


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
    sa.enable_zero_span()
    sa.disable_zero_span()
    sa.set_span(sa.max_span)


def test_rbw(sa: SpectrumAnalyser):
    sa.set_rbw(1e6)
    with pytest.raises(ValueError):
        sa.set_rbw(int(0.5 * (sa.supported_rbw[0] + sa.supported_rbw[1])))
    if sa.supports_emi_measurements:
        assert sa.supported_emi_rbw and len(sa.supported_emi_rbw) >= 2
        sa.set_rbw(sa.supported_emi_rbw[0], SpectrumAnalyser.FilterType.EMI)
        with pytest.raises(ValueError):
            sa.set_rbw(
                int(0.5 * (sa.supported_emi_rbw[0] + sa.supported_emi_rbw[1])),
                SpectrumAnalyser.FilterType.EMI,
            )
    # Test to setup EMI filters on spectrum analyser that doesn't support it
    test = SpectrumAnalyser(
        resource_manager=None,  # type: ignore
        visa_address=None,  # type: ignore
        name=None,  # type: ignore
        expected_idn_response=None,  # type: ignore
        verify=None,  # type: ignore
        logger=None,  # type: ignore
        min_freq=int(1e9),
        max_freq=int(2e9),
        min_num_sweep_points=10,
        max_num_sweep_points=10,
        min_span=10,
        max_span=10,
        min_attenuation_db=None,  # type: ignore
        max_attenuation_db=None,  # type: ignore
        has_preamp=None,  # type: ignore
        supported_rbw=[1000],
        supported_vbw=None,  # type: ignore
        max_num_traces=None,  # type: ignore
        max_num_markers=None,  # type: ignore
        supports_emi_measurements=False,
    )
    with pytest.raises(ValueError):
        test.set_rbw(1000, SpectrumAnalyser.FilterType.EMI)


def test_vbw(sa: SpectrumAnalyser):
    sa.set_vbw(sa.supported_vbw[0])
    with pytest.raises(ValueError):
        assert sa.supported_vbw and len(sa.supported_vbw) >= 2
        sa.set_vbw(int(0.5 * (sa.supported_vbw[0] + sa.supported_vbw[1])))


def test_num_sweep_points(sa: SpectrumAnalyser):
    sa.set_num_sweep_points(sa.min_num_sweep_points)
    with pytest.raises(ValueError):
        sa.set_num_sweep_points(sa.min_num_sweep_points - 1)
    sa.set_num_sweep_points(sa.max_num_sweep_points)
    with pytest.raises(ValueError):
        sa.set_num_sweep_points(sa.max_num_sweep_points + 1)


def test_input_attenuation(sa: SpectrumAnalyser):
    sa.set_input_attenuation(sa.min_attenuation_db)
    sa.set_input_attenuation(sa.max_attenuation_db)
    with pytest.raises(ValueError):
        sa.set_input_attenuation(sa.min_attenuation_db - 1)
    with pytest.raises(ValueError):
        sa.set_input_attenuation(sa.max_attenuation_db + 1)


def test_ref_level(sa: SpectrumAnalyser):
    # Not really testing anything here, just that the function is implemented
    sa.set_ref_level(-20)


def test_trace_data(sa: SpectrumAnalyser):
    # Not really testing anything here, just that the function is implemented
    sa.trigger_sweep()
    sa.get_trace_data()
    with pytest.raises(ValueError):
        sa.set_trace_mode(sa.max_num_traces + 1, SpectrumAnalyser.TraceMode.CLEAR_WRITE)


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
        sa.set_marker_freq(
            sa.max_num_markers + 1,
            sa.min_freq,
        )
    with pytest.raises(ValueError):
        sa.get_marker_freq(sa.max_num_markers + 1)
    with pytest.raises(ValueError):
        sa.measure_marker_power(sa.max_num_markers + 1)
    with pytest.raises(ValueError):
        sa.measure_power(sa.min_freq, sa.max_num_markers + 1)


def test_instrument_errors(sa: SpectrumAnalyser):
    sa.get_instrument_errors()
