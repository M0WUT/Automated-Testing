from ast import Assert
from time import sleep

import pytest
from AutomatedTesting.Instruments.TopLevel.config import dsa815tg, e4407b
from AutomatedTesting.Instruments.TopLevel.InstrumentSupervisor import (
    InstrumentSupervisor,
)

instrumentsToTest = [dsa815tg]  # , e4407b]

with InstrumentSupervisor() as tb:

    @pytest.fixture(params=instrumentsToTest)
    def dut(request):
        x = request.param
        tb.request_resources([x])
        return x

    @pytest.mark.e4407b
    def test_validate_invalid_low_centre_freq(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_centre_freq(1)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_high_centre_freq(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_centre_freq(2 * dut.maxFreq)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_valid_centre_freq(dut):
        try:
            dut.set_centre_freq(1e9)
            assert dut.read_centre_freq() == 1e9
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_low_start_freq(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_start_freq(1)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_high_start_freq(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_start_freq(2 * dut.maxFreq)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_valid_start_freq(dut):
        try:
            dut.set_start_freq(1e9)
            assert dut.read_start_freq() == 1e9
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_freq_limits(dut):
        try:
            dut.set_span(0)
            dut.set_centre_freq(dut.minFreq)
            assert dut.read_centre_freq() == dut.minFreq
            dut.set_centre_freq(dut.maxFreq)
            assert dut.read_centre_freq() == dut.maxFreq
            with pytest.raises(ValueError):
                dut.set_centre_freq(dut.minFreq - 1)
            with pytest.raises(ValueError):
                dut.set_centre_freq(dut.maxFreq + 1)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_low_stop_freq(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_stop_freq(1)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_high_stop_freq(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_stop_freq(2 * dut.maxFreq)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_valid_stop_freq(dut):
        try:
            dut.set_stop_freq(1e9)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_valid_span(dut):
        try:
            dut.set_span(1e6)
            assert dut.read_span() == 1e6
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_span(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_span(2 * dut.maxFreq)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_sweep_points(dut):
        try:
            if dut.minSweepPoints:
                dut.set_sweep_points(dut.minSweepPoints)
                assert dut.read_sweep_points() == dut.minSweepPoints
                with pytest.raises(ValueError):
                    dut.set_sweep_points(2 * dut.maxFreq)
            else:
                with pytest.raises(AssertionError):
                    dut.set_sweep_points(401)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_invalid_sweep_time(dut):
        try:
            with pytest.raises(ValueError):
                dut.set_sweep_time(1e-6)
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_valid_sweep_time(dut):
        try:
            dut.set_sweep_time(1000)
            assert dut.read_sweep_time() == 1000
        finally:
            tb.free_resource(dut)

    @pytest.mark.e4407b
    def test_validate_preamp(dut):
        try:
            if dut.hasPreamp:
                dut.enable_preamp()
                assert dut.read_preamp_state()
                dut.disable_preamp()
                assert not dut.read_preamp_state()
            else:
                with pytest.raises(AssertionError):
                    dut.enable_preamp()
        finally:
            tb.free_resource(dut)
