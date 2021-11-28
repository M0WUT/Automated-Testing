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
centreFreq = 50e6
toneSpacing = 1e6
lowerPower = -15
upperPower = 10
powerStep = 1
measureIMD3 = True
measureIMD5 = True
measureIMD7 = True

with TestSupervisor(
    loggingLevel=logging.INFO, instruments=instruments, calibrationPower=0, saveResults=False
) as supervisor:
    channel1 = sdg2122x.reserve_channel(1, "Channel 1")
    channel2 = sdg2122x.reserve_channel(2, "Channel 2")
    channel1.set_power(lowerPower)
    channel2.set_power(lowerPower)
    f1 = centreFreq - 0.5 * toneSpacing
    f2 = centreFreq + 0.5 * toneSpacing
    channel1.set_freq(f1)
    channel2.set_freq(f2)
    
    channel1.enable_output()
    channel2.enable_output()

    # Setup Spectrum analyser
    e4407b.set_ref_level(upperPower + 2)
    e4407b.set_centre_freq(centreFreq)
    e4407b.set_rbw(1000)

    # Sanity check measurement
    assert measureIMD3 or measureIMD5 or measureIMD7, \
        "No Measurement Requested"

    # Setup Headings
    print("Power per Tone Setpoint(dBm),Tone-Upper (dBm),Tone-Lower (dBm),", end='')
    if measureIMD3:
        print("IMD3-Upper (dBm),IMD3-Lower (dBm),", end='')
        e4407b.set_span(4 * toneSpacing)
    if measureIMD5:
        print("IMD5-Upper (dBm),IMD5-Lower (dBm),", end='')
        e4407b.set_span(6 * toneSpacing)
    if measureIMD7:
        print("IMD7-Upper (dBm),IMD7-Lower (dBm),", end='')
        e4407b.set_span(8 * toneSpacing)
    print("")


    for power in range(lowerPower, upperPower + powerStep, powerStep):
        channel1.set_power(power + 3.3)
        channel2.set_power(power + 3.3)
        e4407b._write(":INIT:IMM;*WAI")
        print(f"{power},{e4407b.measure_power_marker(f2)},{e4407b.measure_power_marker(f1)},", end='')
        if measureIMD3:
            print(f"{e4407b.measure_power_marker(2*f2 - f1)},{e4407b.measure_power_marker(2*f1 - f2)},", end='')
        if measureIMD5:
            print(f"{e4407b.measure_power_marker(3*f2 - 2*f1)},{e4407b.measure_power_marker(3*f1 - 2*f2)},", end='')
        if measureIMD7:
            print(f"{e4407b.measure_power_marker(4*f2 - 3*f1)},{e4407b.measure_power_marker(4*f1 - 3*f2)},", end='')
        print("")