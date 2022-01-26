from time import sleep

import pytest
from AutomatedTesting.Instruments.TopLevel.config import sdg2122x as sigGen
from AutomatedTesting.Instruments.TopLevel.InstrumentSupervisor import (
    InstrumentSupervisor,
)

with InstrumentSupervisor() as tb:

    @pytest.fixture
    def channel():
        tb.request_resources([sigGen])
        x = sigGen.reserve_channel(channelNumber=1, name="test")
        return x

    @pytest.mark.sdg2122x
    def test_validate_invalid_channel(channel):
        try:
            with pytest.raises(ValueError):
                sigGen.validate_channel_number(99)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_power(channel):
        try:
            channel.set_power(0)
            assert channel.read_power() == 0
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_freq(channel):
        try:
            channel.set_freq(118e6)
            assert channel.read_freq() == 118e6
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_high_invalid_power(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_power(50)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_low_invalid_power(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_power(-150)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_high_invalid_freq(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_freq(13e9)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_low_invalid_freq(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_freq(-5)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_invalid_power_limits(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_power_limits(-160, 1)  # ERROR
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_power_above_reduced_limits(channel):
        try:
            channel.set_power_limits(-60, -30)
            with pytest.raises(ValueError):
                channel.set_power(-20)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_power_below_reduced_limits(channel):
        try:
            channel.set_power_limits(0.5, 1)
            with pytest.raises(ValueError):
                channel.set_power(0.2)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_invalid_freq_limits(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_freq_limits(-1, 1)  # ERROR
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_freq_above_reduced_limits(channel):
        try:
            channel.set_freq_limits(1e3, 2e3)
            with pytest.raises(ValueError):
                channel.set_freq(3e3)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_set_freq_below_reduced_limits(channel):
        try:
            channel.set_freq_limits(1e3, 2e3)
            with pytest.raises(ValueError):
                channel.set_freq(500)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_output_enable(channel):
        try:
            channel.set_power(0)
            channel.set_freq(1e3)
            channel.enable_output(True)
            sleep(5)  # Sleep long enough for monitoring thread
            channel.enable_output(False)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.sdg2122x
    def test_output_enable_reenable(channel):
        try:
            channel.set_power(0)
            channel.set_freq(1e3)
            channel.enable_output(True)
            with pytest.raises(ValueError):
                channel.enable_output(True)
        finally:
            tb.free_resource(sigGen)
