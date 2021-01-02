from AutomatedTesting.TestDefinitions.BaseTest import BaseTest
from AutomatedTesting.TestDefinitions.ResultsHandler import \
    MeasurementPoint
import logging
from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq


class BasicGainFlatness(BaseTest):
    def __init__(
        self,
        powerRange,
        measurementFreq,
        gateVoltage=None,
        drainVoltage=None
    ):
        self.powerRange = powerRange
        self.measurementFreq = measurementFreq
        self.measurements = []
        self.gateVoltage = gateVoltage
        self.drainVoltage = drainVoltage

    def generate_measurement_points(self):
        for p in self.powerRange:
            self.measurements.append(
                MeasurementPoint(
                    freq=self.measurementFreq,
                    inputPower=p,
                    gateVoltage=self.gateVoltage,
                    drainVoltage=self.drainVoltage
                )
            )
        logging.info(
            "Generated datapoints for Basic gain flatness test"
        )
        return self.measurements

    def process_results(self, results):
        logging.info(
            "Processing results for Basic gain flatness test"
        )
        super().retrieve_results(results)
        ws = results.excelFile.add_worksheet("Basic Gain Flatness")
        # Sort measurements by input power
        self.measurements.sort(key=lambda x: x.inputPower)
        ws.write(0, 0, "Input Power (dBm)")
        ws.write(0, 1, "Gain (dB)")

        for x in self.measurements:
            rowIndex = 1 + self.measurements.index(x)
            ws.write(rowIndex, 0, x.inputPower)
            gain = x.outputPower - x.inputPower
            ws.write(rowIndex, 1, gain)

        chart = results.excelFile.add_chart({
            'type': 'scatter',
            'subtype': 'smooth'
        })

        chart.add_series({
            'categories':   f"='Basic Gain Flatness'!$A$2:"
                            f"$A{1 + len(self.measurements)}",
            'values':       f"='Basic Gain Flatness'!$B$2:"
                            f"$B{1 + len(self.measurements)}"
        })

        chart.set_x_axis({
            'name': "Input Power (dBm)",
            'min': self.measurements[0].inputPower,
            'max': self.measurements[-1].inputPower,
            'crossing': -200
        })

        chart.set_y_axis({
            'name': 'Gain (dB)',
            'crossing': -200
        })

        chart.set_legend({'none': True})

        ws.insert_chart('D2', chart)

        columnIndex = 3

        if self.gateVoltage is not None:
            ws.write(0, columnIndex, "Gate Voltage:")
            ws.write(0, columnIndex + 1, f"{self.gateVoltage}V")
            columnIndex += 3

        if self.drainVoltage is not None:
            ws.write(0, columnIndex, "Drain Voltage:")
            ws.write(0, columnIndex + 1, f"{self.drainVoltage}V")
            columnIndex += 3

        ws.write(0, columnIndex, "Measurement Frequency:")
        ws.write(0, columnIndex + 1, f"{readable_freq(self.measurementFreq)}")
        columnIndex += 3 
