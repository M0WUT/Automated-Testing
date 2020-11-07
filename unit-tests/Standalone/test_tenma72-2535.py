from AutomatedTesting.TopLevel.config import tenmaSingleChannel as psu
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
import pytest
from time import sleep

with InstrumentSupervisor() as tb:

    @pytest.fixture
    def channel():
        tb.request_resources([psu])
        x = psu.reserve_channel(
            channelNumber=1,
            name="test"
        )
        return x

    def test_validate_invalid_channel(channel):
        try:
            with pytest.raises(ValueError):
                psu.validate_channel_number(2)
        finally:
            tb.free_resouce(psu)

    def test_set_voltage(channel):
        try:
            channel.set_voltage(4)
            assert channel.read_voltage_setpoint() == 4
        finally:
            tb.free_resouce(psu)

    def test_set_current(channel):
        try:
            channel.set_current(1)
            assert channel.read_current_setpoint() == 1
        finally:
            tb.free_resouce(psu)

    def test_set_ovp(channel):
        try:
            channel.enable_ovp(True)
            sleep(0.5)
            channel.enable_ovp(False)
        finally:
            tb.free_resouce(psu)

    def test_set_ocp(channel):
        try:
            channel.enable_ocp(True)
            sleep(0.5)
            channel.enable_ocp(False)
        finally:
            tb.free_resouce(psu)

    def test_set_high_invalid_voltage(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_voltage(60)
        finally:
            tb.free_resouce(psu)

    def test_set_low_invalid_voltage(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_voltage(-5)
        finally:
            tb.free_resouce(psu)

    def test_set_high_invalid_current(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_current(10)
        finally:
            tb.free_resouce(psu)

    def test_set_low_invalid_current(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_voltage(-5)
        finally:
            tb.free_resouce(psu)

    def test_set_invalid_voltage_limits(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_voltage_limits(-1, 1)  # ERROR
        finally:
            tb.free_resouce(psu)

    def test_set_voltage_above_reduced_limits(channel):
        try:
            channel.set_voltage_limits(0, 1)
            with pytest.raises(ValueError):
                channel.set_voltage(2)
        finally:
            tb.free_resouce(psu)

    def test_set_voltage_below_reduced_limits(channel):
        try:
            channel.set_voltage_limits(0.5, 1)
            with pytest.raises(ValueError):
                channel.set_voltage(0.2)
        finally:
            tb.free_resouce(psu)

    def test_set_invalid_current_limits(channel):
        try:
            with pytest.raises(ValueError):
                channel.set_current_limits(-1, 1)
        finally:
            tb.free_resouce(psu)

    def test_set_current_above_reduced_limits(channel):
        try:
            channel.set_current_limits(0, 1)
            with pytest.raises(ValueError):
                channel.set_current(2)
        finally:
            tb.free_resouce(psu)

    def test_set_current_below_reduced_limits(channel):
        try:
            channel.set_current_limits(0.5, 1)
            with pytest.raises(ValueError):
                channel.set_current(0.2)
        finally:
            tb.free_resouce(psu)

    def test_output_measure(channel):
        try:
            channel.set_voltage(1)
            channel.set_current(0.01)
            channel.enable_output(True)
            assert channel.measure_voltage() == 1
            assert channel.measure_current() == 0
        finally:
            tb.free_resouce(psu)

    def test_output_enable_and_measure(channel):
        try:
            channel.set_voltage(1)
            channel.set_current(0.01)
            channel.enable_output(True)
            assert channel.measure_voltage() == 1
            assert channel.measure_current() == 0
            channel.set_voltage(2)

            # Wait to ensure monitoring thread runs
            sleep(4)
            channel.enable_output(False)

        finally:
            tb.free_resouce(psu)
