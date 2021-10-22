from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from AutomatedTesting.TestDefinitions.ResultsHandler import \
    ResultsHandler, MeasurementPoint
from AutomatedTesting.TopLevel.PowerCorrections import PowerCorrections
import os
import logging


class TestSupervisor():
    def __init__(
        self, loggingLevel, instruments,
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
        self.instruments = instruments
        self.gateSupply = None
        self.drainSupply = None
        self.gateVoltmeter = None
        self.drainVoltmeter = None
        self.drainAmmeter = None
        self.measurementFreqs = []
        # Request source / as these are mandatory
        self.instrumentSupervisor.request_resources(
            self.instruments
        )

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.instrumentSupervisor.cleanup()
        if self.saveResults:
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
