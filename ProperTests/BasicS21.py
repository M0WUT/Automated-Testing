from AutomatedTesting.TestDefinitions.BaseTest import BaseTest
from AutomatedTesting.TestDefinitions.ResultsHandler import \
    MeasurementPoint
import logging
import math


class BasicS21(BaseTest):
    def __init__(
        self,
        freqRange,
        measurementPower,
        gateVoltage=None,
        drainVoltage=None
    ):
        self.freqRange = freqRange
        self.measurementPower = measurementPower
        self.measurements = []
        self.gateVoltage = gateVoltage
        self.drainVoltage = drainVoltage

    def generate_measurement_points(self):
        for f in self.freqRange:
            self.measurements.append(
                MeasurementPoint(
                    freq=f,
                    inputPower=self.measurementPower,
                    gateVoltage=self.gateVoltage,
                    drainVoltage=self.drainVoltage,
                )
            )
        logging.info(
            "Generated datapoints for Basic S21 test"
        )
        return self.measurements

    def process_results(self, results):
        logging.info(
            "Processing results for Basic S21 test"
        )
        super().retrieve_results(results)
        ws = results.excelFile.add_worksheet("Basic S21")
        # Sort measurements by frequency
        self.measurements.sort(key=lambda x: x.freq)

        if self.measurements[0].freq > 1e9:
            freqUnits = "GHz"
            freqDivider = 1e9
        elif self.measurements[0].freq > 1e6:
            freqUnits = "MHz"
            freqDivider = 1e6
        elif self.measurements[0].freq > 1e3:
            freqUnits = "kHz"
            freqDivider = 1e3
        else:
            freqUnits = "Hz"
            freqDivider = 1

        ws.write(0, 0, f"Frequency ({freqUnits})")
        ws.write(0, 1, "Gain (dB)")

        minGain = math.inf
        maxGain = -math.inf

        for x in self.measurements:
            rowIndex = 1 + self.measurements.index(x)
            ws.write(rowIndex, 0, x.freq / freqDivider)

            gain = x.outputPower - x.inputPower
            ws.write(rowIndex, 1, gain)
            minGain = min(minGain, gain)
            maxGain = max(maxGain, gain)

        chart = results.excelFile.add_chart({
            'type': 'scatter',
            'subtype': 'straight'
        })

        chart.add_series({
            'categories': f"='Basic S21'!$A$2:$A{1 + len(self.measurements)}",
            'values': f"='Basic S21'!$B$2:$B{1 + len(self.measurements)}"
        })

        chart.set_x_axis({
            'name': f"Frequency ({freqUnits})",
            'min': self.measurements[0].freq / freqDivider,
            'max': self.measurements[-1].freq / freqDivider,
            'crossing': -200
        })

        chart.set_y_axis({
            'name': 'Gain (dB)',
            'crossing': -200,
            'min': math.floor(minGain),
            'max': math.ceil(maxGain)
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

        ws.write(0, columnIndex, "Measurement Power:")
        ws.write(0, columnIndex + 1, f"{self.measurementPower}dBm")
        columnIndex += 3
