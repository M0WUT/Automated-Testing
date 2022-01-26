import pytest
import pyvisa
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator, SignalGeneratorChannel)

rm = pyvisa.ResourceManager('@py')


def test_channel_count():
    with pytest.raises(AssertionError):
        _ = SignalGenerator(
            id="",
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[],  # ERROR
            address=None
        )


def test_invalid_channel():
    with pytest.raises(AssertionError):

        c = SignalGeneratorChannel(
            channelNumber=2,  # ERROR
            maxPower=1,
            minPower=0,
            maxFreq=1e9,
            minFreq=0.5e9
        )

        _ = SignalGenerator(
            id="",
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[c],
            address=None
        )


def test_invalid_power_limits():
    with pytest.raises(ValueError):

        c = SignalGeneratorChannel(
            channelNumber=1,
            maxPower=0,  # ERROR
            minPower=1,  # ERROR
            maxFreq=1e9,
            minFreq=0.5e9
        )

        _ = SignalGenerator(
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[c],
            hasOVP=0,
            hasOCP=0,
            address=None
        )


def test_invalid_freq_limits():
    with pytest.raises(ValueError):

        c = SignalGeneratorChannel(
            channelNumber=1,
            maxPower=1,
            minPower=0,
            maxFreq=0.5e9,  # ERROR
            minFreq=1e9  # ERROR
        )

        _ = SignalGenerator(
            id="",
            name="x",
            resourceManager=rm,
            channelCount=1,
            channels=[c],
            hasOVP=0,
            hasOCP=0,
            address=None
        )
