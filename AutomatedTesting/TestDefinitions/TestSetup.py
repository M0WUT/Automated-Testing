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

        if gateSupply:
            assert isinstance(gateSupply, PowerSupply)
            assert gateSupplyChannel
            assert dutLimits.maxGateVoltage
        else:
            assert gateVoltmeter is None

        if drainSupply:
            assert isinstance(drainSupply, PowerSupply)
            assert drainSupplyChannel
            assert dutLimits.maxDrainVoltage
            assert dutLimits.maxDrainCurrent
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

        if maxDrainVoltage:
            assert maxDrainCurrent
        self.maxDrainVoltage = maxDrainVoltage
        self.maxDrainCurrent = maxDrainCurrent
