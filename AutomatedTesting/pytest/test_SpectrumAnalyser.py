# Standard imports
import math

# Third party imports
import pytest

# Local imports
from AutomatedTesting.Instruments.InstrumentConfig import ssa3032x
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)
from AutomatedTesting.Instruments.Transducer.TekboxTBTC1 import TekboxTBTC1
from AutomatedTesting.Misc.Corrections import Corrections
from AutomatedTesting.Misc.Units import AmplitudeUnits


pytestmark = pytest.mark.parametrize("spectrum_analyser", [ssa3032x])


@pytest.fixture(scope="function")
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
            min_sweep_time_s=None,  # type:ignore
            max_sweep_time_s=None,  # type:ignore
            min_span_hz=10,
            max_span_hz=10,
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
            min_sweep_time_s=None,  # type:ignore
            max_sweep_time_s=None,  # type:ignore
            min_span_hz=10,
            max_span_hz=10,
            min_attenuation_db=None,  # type: ignore
            max_attenuation_db=None,  # type: ignore
            has_preamp=None,  # type: ignore
            supported_rbw=None,  # type: ignore
            supported_vbw=None,  # type: ignore
            max_num_traces=None,  # type: ignore
            max_num_markers=None,  # type: ignore
            supports_emi_measurements=None,  # type: ignore
        )

    # Check max_span_hz < min_span_hz validation
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
            min_sweep_time_s=None,  # type:ignore
            max_sweep_time_s=None,  # type:ignore
            min_span_hz=11,
            max_span_hz=10,
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
    sa.set_centre_freq(sa.min_freq + math.ceil(0.5 * sa.min_span_hz))
    sa.set_centre_freq(sa.max_freq - math.ceil(0.5 * sa.min_span_hz))
    with pytest.raises(ValueError):
        sa.set_centre_freq(sa.max_freq + 1)
    with pytest.raises(AssertionError):
        sa.set_centre_freq(sa.min_freq + math.ceil(0.5 * sa.min_span_hz) - 1)
    with pytest.raises(AssertionError):
        sa.set_centre_freq(sa.max_freq + 1 - math.ceil(0.5 * sa.min_span_hz))


def test_span(sa: SpectrumAnalyser):
    sa.set_span(sa.min_span_hz)
    sa.set_span(sa.max_span_hz)
    with pytest.raises(ValueError):
        sa.set_span(sa.min_span_hz - 1)
    with pytest.raises(ValueError):
        sa.set_span(sa.max_span_hz + 1)
    with pytest.raises(ValueError):
        sa.set_span(0)
    sa.enable_zero_span()
    sa.disable_zero_span()
    sa.set_span(sa.max_span_hz)


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
        min_sweep_time_s=None,  # type:ignore
        max_sweep_time_s=None,  # type:ignore
        min_span_hz=10,
        max_span_hz=10,
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
    sa.enable_zero_span()
    sa.trigger_sweep()
    with pytest.raises(RuntimeError):
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


def test_multipart_sweep(sa: SpectrumAnalyser):
    sa.set_trace_mode(1, SpectrumAnalyser.TraceMode.CLEAR_WRITE)
    if sa.max_freq <= sa.min_freq + 2 * (sa.max_num_sweep_points + 1) * 1e6:
        raise NotImplementedError

    for ensure_stop_freq_is_covered in [True, False]:
        for num_points in [
            sa.min_num_sweep_points,
            sa.max_num_sweep_points,
            sa.max_num_sweep_points + 1,
            2 * sa.max_num_sweep_points - 1,
            2 * sa.max_num_sweep_points,
            2 * sa.max_num_sweep_points + 1,
        ]:
            max_freq = sa.min_freq + 1e6 * (num_points - 1)
            results = sa.perform_multi_part_sweep(
                sa.min_freq,
                max_freq,
                1e6,
                ensure_stop_freq_is_covered,
                seconds_per_mhz=1e-3,
            )
            if ensure_stop_freq_is_covered:
                assert (
                    results.datapoints[SpectrumAnalyser.DetectorType.POSITIVE_PEAK][-1][
                        0
                    ]
                    >= max_freq
                )
            else:
                assert (
                    results.datapoints[SpectrumAnalyser.DetectorType.POSITIVE_PEAK][-1][
                        0
                    ]
                    <= max_freq
                )
        # Check correct behaviour when seconds_per_mhz is not defined
        # Use convenient values left over from last iteration of main test
        sa.perform_multi_part_sweep(
            sa.min_freq, max_freq, 1e6, ensure_stop_freq_is_covered
        )


def test_preamp(sa: SpectrumAnalyser):
    if sa.has_preamp:
        sa.enable_preamp()
        sa.disable_preamp()

    # Test to test preamp on a spectrum analyser that doesn't support it
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
        min_sweep_time_s=None,  # type:ignore
        max_sweep_time_s=None,  # type:ignore
        min_span_hz=10,
        max_span_hz=10,
        min_attenuation_db=None,  # type: ignore
        max_attenuation_db=None,  # type: ignore
        has_preamp=False,
        supported_rbw=[1000],
        supported_vbw=None,  # type: ignore
        max_num_traces=None,  # type: ignore
        max_num_markers=None,  # type: ignore
        supports_emi_measurements=False,
    )
    with pytest.raises(RuntimeError):
        test.set_preamp_enabled_state(False)
    with pytest.raises(RuntimeError):
        test.get_preamp_enabled_state()


def test_sweep_time(sa: SpectrumAnalyser):
    # Test reasonable value
    sa.set_sweep_time(1)
    # Test < sa.min_sweep_time
    with pytest.raises(ValueError):
        sa.set_sweep_time(0)
    # Test a value x, sa.min_sweep_time < x < auto_sweep_time
    sa.enable_auto_sweep_time()
    auto_sweep_time = sa.get_sweep_time()
    assert auto_sweep_time != sa.min_sweep_time_s
    with pytest.raises(ValueError):
        sa.set_sweep_time(0.5 * (sa.min_sweep_time_s + auto_sweep_time))


def test_spectrum_analyser_measurement_combination(spectrum_analyser):
    x = SpectrumAnalyser.SpectrumAnalyserMeasurement(
        datapoints={
            SpectrumAnalyser.DetectorType.POSITIVE_PEAK: [(0, 1), (2, 3)],
            SpectrumAnalyser.DetectorType.AVERAGE: [(4, 5), (6, 7)],
            # Have a detector not present in the other to check
            # correct response
            SpectrumAnalyser.DetectorType.NEGATIVE_PEAK: [(8, 9), (10, 11)],
        },
        units=AmplitudeUnits.DBM,
    )

    y = SpectrumAnalyser.SpectrumAnalyserMeasurement(
        datapoints={
            SpectrumAnalyser.DetectorType.POSITIVE_PEAK: [(12, 13), (14, 15)],
            SpectrumAnalyser.DetectorType.AVERAGE: [(16, 17), (18, 19)],
            # Have a detector not present in the other to check
            # correct response
            SpectrumAnalyser.DetectorType.QUASI_PEAK: [(20, 21), (22, 23)],
        },
        units=AmplitudeUnits.DBM,
    )

    z = x + y

    assert (
        z.datapoints[SpectrumAnalyser.DetectorType.POSITIVE_PEAK]
        == x.datapoints[SpectrumAnalyser.DetectorType.POSITIVE_PEAK]
        + y.datapoints[SpectrumAnalyser.DetectorType.POSITIVE_PEAK]
    )
    assert (
        z.datapoints[SpectrumAnalyser.DetectorType.AVERAGE]
        == x.datapoints[SpectrumAnalyser.DetectorType.AVERAGE]
        + y.datapoints[SpectrumAnalyser.DetectorType.AVERAGE]
    )
    assert (
        z.datapoints[SpectrumAnalyser.DetectorType.NEGATIVE_PEAK]
        == x.datapoints[SpectrumAnalyser.DetectorType.NEGATIVE_PEAK]
    )
    assert (
        z.datapoints[SpectrumAnalyser.DetectorType.QUASI_PEAK]
        == y.datapoints[SpectrumAnalyser.DetectorType.QUASI_PEAK]
    )

    # Check overlapping frequencies raises Error
    with pytest.raises(AssertionError):
        _ = x + SpectrumAnalyser.SpectrumAnalyserMeasurement(
            datapoints={
                SpectrumAnalyser.DetectorType.POSITIVE_PEAK: [
                    x.datapoints[SpectrumAnalyser.DetectorType.POSITIVE_PEAK][0]
                ],
            },
            units=AmplitudeUnits.DBM,
        )


def test_transducer(sa: SpectrumAnalyser):
    sa.apply_transducer(TekboxTBTC1())
    sa.set_trace_mode(1, SpectrumAnalyser.TraceMode.CLEAR_WRITE)
    sa.get_trace_data()


def test_correction(sa: SpectrumAnalyser):
    sa.set_trace_mode(1, SpectrumAnalyser.TraceMode.CLEAR_WRITE)
    sa.apply_corrections(Corrections([(0, 0), (100e9, -10)]))
    sa.get_trace_data()

    # Check that a measurement without complete correction data throws an error
    sa.apply_corrections(Corrections([(0, 0), (sa.max_freq - 1, -10)]))
    with pytest.raises(ValueError):
        sa.get_trace_data()


def test_file_saving(sa: SpectrumAnalyser):
    sa.set_trace_mode(1, SpectrumAnalyser.TraceMode.CLEAR_WRITE)
    x = sa.get_trace_data()
    paths = x.save_to_file(filename_prefix="test")
    for p in paths:
        assert p.exists()
        p.unlink()
