from AutomatedTesting.PSU.Tenma_72_2535 import Tenma_72_2535
from AutomatedTesting.SignalGenerator.RandS_SMB100A import RandS_SMB100A
from AutomatedTesting.PowerMeter.Agilent_U2001A import Agilent_U2001A
from AutomatedTesting.SpectrumAnalyser.Agilent_E4407B import Agilent_E4407B
from AutomatedTesting.TestDefinitions.TestSetup import TestSetup, DUTLimits
from ProperTests.BasicS21 import BasicS21
from ProperTests.BasicGainFlatness import BasicGainFlatness
from ProperTests.GainFlatnessWithSweptFrequency import \
    GainFlatnessWithSweptFrequency
from ProperTests.BasicDrainEfficiency import BasicDrainEfficiency
from numpy import arange

tenmaSingleChannel = Tenma_72_2535("ASRL/dev/ttyACM0::INSTR")
smb100a = RandS_SMB100A("TCPIP::192.168.0.23::INSTR")
u2001a = Agilent_U2001A("USB0::2391::11032::MY53150007::0::INSTR")
e4407b = Agilent_E4407B("GPIB0::18::INSTR", enableDisplay=False)

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
