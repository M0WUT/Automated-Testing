from ProperTests.BasicS21 import BasicS21
from ProperTests.GainFlatnessWithSweptFrequency import \
    GainFlatnessWithSweptFrequency
from ProperTests.BasicDrainEfficiency import BasicDrainEfficiency
from numpy import arange
import logging
from AutomatedTesting.TestDefinitions.TestSupervisor import TestSupervisor
from AutomatedTesting.TestDefinitions.TestSetup import TestSetup, DUTLimits
from time import sleep
from AutomatedTesting.TopLevel.config import \
    smb100a, u2001a, tenmaSingleChannel, sdg2122X

POWER_RANGE = arange(-50, 0, 0.5)
FREQ_RANGE = arange(2.3e9, 2.6e9, 1e6)
DEFAULT_FREQ = 2.4e9
DEFAULT_DRAIN_VOLTAGE = 24

limits = DUTLimits(
    minFreq=2e9,
    maxFreq=3e9,
    maxInputPower=18,
    maxDrainVoltage=24,
    maxDrainCurrent=1.5
)

testSetup = TestSetup(
    signalSource=smb100a,
    signalSourceChannel=1,
    signalSink=u2001a,
    dutLimits=limits,
    drainSupply=tenmaSingleChannel,
    drainSupplyChannel=1
)

s21 = BasicS21(
    freqRange=FREQ_RANGE,
    measurementPower=-10,
    drainVoltage=DEFAULT_DRAIN_VOLTAGE
)

gainFlatness = GainFlatnessWithSweptFrequency(
    powerRange=POWER_RANGE,
    freqRange=[2.4e9, 2.45e9, 2.5e9],
    drainVoltage=DEFAULT_DRAIN_VOLTAGE
)

eff = BasicDrainEfficiency(
    powerRange=POWER_RANGE,
    measurementFreq=DEFAULT_FREQ,
    drainVoltage=DEFAULT_DRAIN_VOLTAGE
)

tests_to_perform = [s21, gainFlatness, eff]

x = sdg2122X


with TestSupervisor(
    loggingLevel=logging.INFO, instruments=[x], calibrationPower=0, saveResults=False
) as supervisor:
    channel = x.reserve_channel(1, "test")
    channel.set_power(0)
    channel.set_freq(1e6)
    sleep(1)
    assert False
    for x in tests_to_perform:
        supervisor.request_measurements(x.generate_measurement_points())
    supervisor.run_measurements()
    for x in tests_to_perform:
        x.process_results(supervisor.results)
