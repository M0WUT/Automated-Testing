from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq
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
    smb100a, u2001a, tenmaSingleChannel, sdg2122x, e4407b

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

instruments = [sdg2122x, e4407b]
#instruments = [sdg2122x, tenmaSingleChannel]


freqList = [1e6, 10e6, 50e6, 100e6, 120e6]

with TestSupervisor(
    loggingLevel=logging.INFO, instruments=instruments, calibrationPower=0, saveResults=False
) as supervisor:
    signal = sdg2122x.reserve_channel(1, "test")
    signal.set_freq(1e6)
    signal.set_power(-50)
    signal.enable_output()
    print("Setpoint,", end='')
    for x in freqList:
        print(readable_freq(x) + ",", end='')
    print("")

    e4407b.set_span(1000)
    e4407b.set_rbw(1000)
    e4407b.set_sweep_points(101)
    signal.set_power_limits(-60, -0)

    for power in arange(-50, 1, 1):
        signal.set_power(power)
        print(f"{power},", end='')
        for freq in freqList:
            signal.set_freq(freq)
            print(f"{e4407b.measure_power(freq)},", end='')
        print("")
            


    



    """
    for x in tests_to_perform:
        supervisor.request_measurements(x.generate_measurement_points())
    supervisor.run_measurements()
    for x in tests_to_perform:
        x.process_results(supervisor.results)
    """
