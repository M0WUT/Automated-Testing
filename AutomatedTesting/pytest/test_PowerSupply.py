# Standard imports
import logging

# Third party imports
import pytest

# Local imports
from AutomatedTesting.Instruments.PowerSupply.PowerSupply import (
    PowerSupply,
    PowerSupplyChannel,
)
from AutomatedTesting.Instruments.InstrumentConfig import tenma_722940, siglent_spd3303x


pytestmark = pytest.mark.parametrize("power_supply", [tenma_722940, siglent_spd3303x])


@pytest.fixture(scope="function")
def psu(power_supply):
    with power_supply:
        yield power_supply


def test_parameter_validation(psu):
    # Test max voltage < min voltage
    with pytest.raises(ValueError):
        _ = PowerSupplyChannel(
            channel_num=1,
            instrument=None,  # type: ignore
            logging_level=logging.DEBUG,
            min_voltage=1,
            max_voltage=0.5,
            min_current=0,
            max_current=1,
        )

    # Test max current < min current
    with pytest.raises(ValueError):
        _ = PowerSupplyChannel(
            channel_num=1,
            instrument=None,  # type: ignore
            logging_level=logging.DEBUG,
            min_voltage=0.5,
            max_voltage=1,
            min_current=1,
            max_current=0,
        )


def test_channel_reservation(psu):
    with psu.reserve_channel(1, "test"):
        pass


def test_soft_voltage_limits(psu: PowerSupply):
    with psu.reserve_channel(1, "test") as ch:
        ch.set_soft_voltage_limits(ch.absolute_min_voltage, ch.absolute_max_voltage)
        # Max < min
        with pytest.raises(ValueError):
            ch.set_soft_voltage_limits(ch.absolute_max_voltage, ch.absolute_min_voltage)
        # Min outside range
        with pytest.raises(ValueError):
            ch.set_soft_voltage_limits(
                ch.absolute_min_voltage - 1, ch.absolute_max_voltage
            )
        # Max outside range
        with pytest.raises(ValueError):
            ch.set_soft_voltage_limits(
                ch.absolute_min_voltage, ch.absolute_max_voltage + 1
            )

        # Try setting outside range
        ch.set_soft_voltage_limits(
            0.5 * (ch.absolute_min_voltage + ch.absolute_max_voltage),
            ch.absolute_max_voltage,
        )
        with pytest.raises(ValueError):
            ch.set_voltage(ch.absolute_min_voltage)


def test_soft_current_limits(psu: PowerSupply):
    with psu.reserve_channel(1, "test") as ch:
        ch.set_soft_current_limits(ch.absolute_min_current, ch.absolute_max_current)
        # Max < min
        with pytest.raises(ValueError):
            ch.set_soft_current_limits(ch.absolute_max_current, ch.absolute_min_current)
        # Min outside range
        with pytest.raises(ValueError):
            ch.set_soft_current_limits(
                ch.absolute_min_current - 1, ch.absolute_max_current
            )
        # Max outside range
        with pytest.raises(ValueError):
            ch.set_soft_current_limits(
                ch.absolute_min_current, ch.absolute_max_current + 1
            )

        # Try setting outside range
        ch.set_soft_current_limits(
            0.5 * (ch.absolute_min_current + ch.absolute_max_current),
            ch.absolute_max_current,
        )
        with pytest.raises(ValueError):
            ch.set_current_limit(ch.absolute_min_current)


def test_normal_operation(psu: PowerSupply):
    for y in [x.channel_num for x in psu.channels]:
        with psu.reserve_channel(y, "test") as ch:
            ch.set_voltage(ch.absolute_min_voltage + 0.1)
            assert ch.get_voltage() == ch.absolute_min_voltage + 0.1
            ch.set_current_limit(ch.absolute_min_current + 0.01)
            assert ch.get_current_limit() == ch.absolute_min_current + 0.01
            ch.enable_output()
            ch.measure_voltage()
            ch.measure_current()
        assert psu.get_channel(y).get_output_enabled_state() is False
