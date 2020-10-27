from AutomatedTesting.TopLevel.config import tenmaSingleChannel as psu
import pytest
x = psu.channels[0]


def test_set_voltage():
    x.set_voltage(4)
    assert x.read_voltage_setpoint() == 4


def test_set_current():
    x.set_current(1)
    assert x.read_current_setpoint() == 1


def test_set_high_invalid_voltage():
    with pytest.raises(ValueError):
        x.set_voltage(60)


def test_set_low_invalid_voltage():
    with pytest.raises(ValueError):
        x.set_voltage(-5)


def test_set_high_invalid_current():
    with pytest.raises(ValueError):
        x.set_current(10)


def test_set_low_invalid_current():
    with pytest.raises(ValueError):
        x.set_voltage(-5)


def test_output_measure():
    x.set_voltage(1)
    x.set_current(0.01)
    x.enable_output(True)
    assert x.measure_voltage() == 1
    assert x.measure_current() == 0
    x.enable_output(False)
