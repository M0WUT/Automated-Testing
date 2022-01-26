import pytest
import pyvisa
from AutomatedTesting.Instruments.PSU.PSU import PowerSupply, PowerSupplyChannel

rm = pyvisa.ResourceManager("@py")


def test_channel_count():
    with pytest.raises(AssertionError):
        _ = PowerSupply(
            id="",
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[],  # ERROR
            hasOVP=0,
            hasOCP=0,
            address=None,
        )


def test_invalid_channel():
    with pytest.raises(AssertionError):

        c = PowerSupplyChannel(
            channelNumber=2,  # ERROR
            maxVoltage=1,
            minVoltage=0,
            maxCurrent=1,
            minCurrent=0,
        )

        _ = PowerSupply(
            id="",
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[c],
            hasOVP=0,
            hasOCP=0,
            address=None,
        )


def test_invalid_voltage_limits():
    with pytest.raises(ValueError):

        c = PowerSupplyChannel(
            channelNumber=1,
            maxVoltage=0,  # ERROR
            minVoltage=1,  # ERROR
            maxCurrent=1,
            minCurrent=0,
        )

        _ = PowerSupply(
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[c],
            hasOVP=0,
            hasOCP=0,
            address=None,
        )


def test_invalid_current_limits():
    with pytest.raises(ValueError):

        c = PowerSupplyChannel(
            channelNumber=1,
            maxVoltage=1,
            minVoltage=0,
            maxCurrent=0,  # ERROR
            minCurrent=1,  # ERROR
        )

        _ = PowerSupply(
            id="",
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[c],
            hasOVP=0,
            hasOCP=0,
            address=None,
        )
