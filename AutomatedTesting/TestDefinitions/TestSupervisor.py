from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from AutomatedTesting.TestDefinitions.ResultsHandler import \
    ResultsHandler, MeasurementPoint
from AutomatedTesting.TopLevel.PowerCorrections import PowerCorrections
import os
import logging


class TestSupervisor():
    def __init__(
        self, loggingLevel, setup,
        saveResults=True, calibrationPower=-30
    ):
        logging.getLogger("pyvisa").setLevel(logging.WARNING)
        if saveResults is True:
            self.name = input(
                "Please enter DUT name and press Enter...\n"
            )
            while(os.path.isdir(f"./Measurements/{self.name}")):
                self.name = input(
                    "Name already taken, please enter another...\n"
                )
        self.loggingLevel = loggingLevel
        self.instrumentSupervisor = InstrumentSupervisor(loggingLevel)
        self.saveResults = saveResults
        self.calibrationPower = calibrationPower

        # If we want to save results, load results handler
        # Otherwise, just store in a list that never gets used
        if self.saveResults:
            self.results = ResultsHandler(self.name)
        else:
            self.results = []

        self.requestedMeasurements = []
        self.setup = setup
        self.gateSupply = None
        self.drainSupply = None
        self.gateVoltmeter = None
        self.drainVoltmeter = None
        self.drainAmmeter = None
        self.measurementFreqs = []
        # Request source / as these are mandatory
        self.instrumentSupervisor.request_resources(
            [self.setup.signalSource, self.setup.signalSink]
        )

        self.signalSink = self.setup.signalSink

        # Setup limits on input device
        self.signalSource = self.setup.signalSource.reserve_channel(
            self.setup.signalSourceChannel,
            "Signal Source"
        )

        self.signalSource.set_freq_limits(
            self.setup.dutLimits.minFreq,
            self.setup.dutLimits.maxFreq,
        )

        self.signalSource.set_power_limits(
            self.signalSource.absoluteMinPower,
            self.setup.dutLimits.maxInputPower
        )

        # Setup gate supply (if needed)
        if self.setup.gateSupply:
            self.instrumentSupervisor.request_resources(
                [self.setup.gateSupply]
            )

            self.gateSupply = self.setup.gateSupply.reserve_channel(
                self.setup.gateSupplyChannel,
                "Gate Voltage"
            )

            self.gateSupply.set_voltage_limits(
                0,
                self.setup.dutLimits.maxGateVoltage
            )

            self.gateSupply.set_current(
                50e-3
            )

            self.drainSupply.enable_ocp()

        # @TODO Add voltmeter
        if self.setup.gateVoltmeter:
            raise NotImplementedError

        if self.setup.drainSupply:
            self.instrumentSupervisor.request_resources(
                [self.setup.drainSupply]
            )

            self.drainSupply = self.setup.drainSupply.reserve_channel(
                self.setup.drainSupplyChannel,
                "Drain Voltage"
            )

            self.drainSupply.set_voltage_limits(
                0,
                self.setup.dutLimits.maxDrainVoltage
            )

            self.drainSupply.set_current_limits(
                0,
                self.setup.dutLimits.maxDrainCurrent
            )

            self.drainSupply.set_current(
                self.setup.dutLimits.maxDrainCurrent
            )

            self.drainSupply.enable_ocp()

        # @TODO Add voltmeter
        if self.setup.drainVoltmeter:
            raise NotImplementedError

        # @TODO Add ammeter
        if self.setup.drainAmmeter:
            raise NotImplementedError

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.instrumentSupervisor.cleanup()
        if self.saveResults is True:
            self.results.cleanup()

    def request_measurements(self, measurements):
        assert isinstance(measurements[0], MeasurementPoint)
        for x in measurements:
            if x not in self.requestedMeasurements:
                # Sanity check measurement
                assert self.setup.dutLimits.minFreq <= x.freq \
                    and x.freq <= self.setup.dutLimits.maxFreq

                if(x.freq not in self.measurementFreqs):
                    self.measurementFreqs.append(x.freq)

                assert x.inputPower < self.setup.dutLimits.maxInputPower

                if x.gateVoltage:
                    assert self.gateSupply
                    assert x.gateVoltage <= self.setup.dutLimits.maxGateVoltage

                if self.gateSupply:
                    assert x.gateVoltage

                if x.drainVoltage:
                    assert self.drainSupply
                    assert x.drainVoltage <= \
                        self.setup.dutLimits.maxDrainVoltage

                if self.drainSupply:
                    assert x.drainVoltage

                self.requestedMeasurements.append(x)
            else:
                index = self.requestedMeasurements.index(x)
                self.requestedMeasurements[index].measureCurrent \
                    |= x.measureCurrent

    def _setup_measurement(self, x):
        assert isinstance(x, MeasurementPoint)
        if x.drainVoltage:
            self.drainSupply.set_voltage(x.drainVoltage)
            if self.drainSupply.outputEnabled is False:
                self.drainSupply.enable_output()

        if x.gateVoltage:
            self.gateSupply.set_voltage(x.gateVoltage)
            if self.gateSupply.outputEnabled is False:
                self.gateSupply.enable_output()

        self.signalSource.set_freq(x.freq)
        self.signalSource.set_power(x.inputPower)
        if self.signalSource.outputEnabled is False:
            self.signalSource.enable_output()

    def run_measurements(self):

        # Normalise system
        self.signalSink.apply_corrections(
            PowerCorrections(
                self.signalSource,
                self.signalSink,
                self.measurementFreqs,
                self.calibrationPower
            )
        )

        logging.info("Starting Measurements")
        for x in self.requestedMeasurements:
            self._setup_measurement(x)

            if self.gateVoltmeter:
                # @TODO Measure with voltmeter
                raise NotImplementedError

            if self.drainVoltmeter:
                # @TODO Measure with voltmeter
                raise NotImplementedError

            if x.measureCurrent:
                if self.drainAmmeter:
                    # @TODO Measure with ammeter
                    raise NotImplementedError
                else:
                    x.drainCurrent = self.drainSupply.measure_current()

            x.outputPower = self.signalSink.measure_power(
                x.freq
            )

            self.results.append(x)
        logging.info("Measurements complete")
