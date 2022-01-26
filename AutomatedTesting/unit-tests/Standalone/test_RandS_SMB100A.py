from time import sleep

import pytest
from AutomatedTesting.Instruments.TopLevel.config import smb100a as sigGen
from AutomatedTesting.Instruments.TopLevel.InstrumentSupervisor import (
    InstrumentSupervisor,
)

with InstrumentSupervisor() as tb:

    @pytest.fixture
    def channel():
        tb.request_resources([sigGen])
        x = sigGen.reserve_channel(channelNumber=1, name="test")
        return x

    @pytest.mark.smb100a
    def test_validate_invalid_channel(channel):
        try:
            with pytest.raises(ValueError):
                sigGen.validate_channel_number(2)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_power(channel):
        try:
            channel.set_power(0)
            assert channel.read_power() == 0
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_high_resolution_power(channel):
        try:
            channel.set_power(0.001)
            assert channel.read_power() == 0
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_freq(channel):
        try:
            channel.set_freq(1e9)
            assert channel.read_freq() == 1e9
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_high_resolution_freq(channel):
        try:
            channel.set_freq(1e9 + 0.00001)
            assert channel.read_freq() == 1e9
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_high_invalid_power(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_power(50)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_low_invalid_power(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_power(-150)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_high_invalid_freq(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_freq(13e9)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_low_invalid_freq(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_freq(-5)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_invalid_power_limits(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_power_limits(-160, 1)  # ERROR
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_power_above_reduced_limits(channel):
        try:
            channel.set_power_limits(-60, -30)
            with pytest.raises(ValueError):
                channel.set_power(-20)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_power_below_reduced_limits(channel):
        try:
            channel.set_power_limits(0.5, 1)
            with pytest.raises(ValueError):
                channel.set_power(0.2)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_invalid_freq_limits(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_freq_limits(-1, 1)  # ERROR
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_freq_above_reduced_limits(channel):
        try:
            channel.set_freq_limits(1e9, 2e9)
            with pytest.raises(ValueError):
                channel.set_freq(3e9)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_set_freq_below_reduced_limits(channel):
        try:
            channel.set_freq_limits(1e9, 2e9)
            with pytest.raises(ValueError):
                channel.set_freq(500e6)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_output_enable(channel):
        try:
            channel.set_power(0)
            channel.set_freq(1e9)
            channel.enable_output(True)
            sleep(5)  # Sleep long enough for monitoring thread
            channel.enable_output(False)
        finally:
            tb.free_resource(sigGen)

    @pytest.mark.smb100a
    def test_output_enable_reenable(channel):
        try:
            channel.set_power(0)
            channel.set_freq(1e9)
            channel.enable_output(True)
            with pytest.raises(ValueError):
                channel.enable_output(True)
        finally:
            tb.free_resource(sigGen)
