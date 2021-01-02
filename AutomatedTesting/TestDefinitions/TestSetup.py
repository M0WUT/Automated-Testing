from AutomatedTesting.SignalGenerator.SignalGenerator import SignalGenerator
from AutomatedTesting.PSU.PSU import PowerSupply
from AutomatedTesting.PowerMeter.PowerMeter import PowerMeter
from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser


class TestSetup():
    def __init__(
        self,
        signalSource,
        signalSourceChannel,
        signalSink,
        dutLimits,
        gateSupply=None,
        gateSupplyChannel=None,
        gateVoltmeter=None,
        drainSupply=None,
        drainSupplyChannel=None,
        drainVoltmeter=None,
        drainAmmeter=None,
    ):
        # @TODO Add noise source here once created
        assert isinstance(signalSource, SignalGenerator)

        # @TODO Check Volt/Ammeters once created

        assert isinstance(dutLimits, DUTLimits)

        # @TODO Add spectrum analyser here once created
        assert isinstance(signalSink, PowerMeter) or \
            isinstance(signalSink, SpectrumAnalyser)

        if gateSupply is not None:
            assert isinstance(gateSupply, PowerSupply)
            assert gateSupplyChannel is not None
            assert dutLimits.maxGateVoltage is not None
        else:
            assert gateVoltmeter is None

        if drainSupply is not None:
            assert isinstance(drainSupply, PowerSupply)
            assert drainSupplyChannel is not None
            assert dutLimits.maxDrainVoltage is not None
            assert dutLimits.maxDrainCurrent is not None
        else:
            assert drainVoltmeter is None and drainAmmeter is None

        self.signalSource = signalSource
        self.signalSourceChannel = signalSourceChannel
        self.gateSupply = gateSupply
        self.gateSupplyChannel = gateSupplyChannel
        self.gateVoltmeter = gateVoltmeter
        self.drainSupply = drainSupply
        self.drainSupplyChannel = drainSupplyChannel
        self.drainVoltmeter = drainVoltmeter
        self.drainAmmeter = drainAmmeter
        self.signalSink = signalSink
        self.dutLimits = dutLimits


class DUTLimits():
    def __init__(
        self,
        minFreq,
        maxFreq,
        maxInputPower,
        maxGateVoltage=None,
        maxDrainVoltage=None,
        maxDrainCurrent=None
    ):
        assert maxFreq > minFreq
        self.minFreq = minFreq
        self.maxFreq = maxFreq
        self.maxInputPower = maxInputPower
        self.maxGateVoltage = maxGateVoltage

        if maxDrainVoltage is not None:
            assert maxDrainCurrent is not None
        self.maxDrainVoltage = maxDrainVoltage
        self.maxDrainCurrent = maxDrainCurrent
