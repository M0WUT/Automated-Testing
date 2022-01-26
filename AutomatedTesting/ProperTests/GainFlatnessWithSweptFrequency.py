from AutomatedTesting.PytestDefinitions.BaseTest import BaseTest
from AutomatedTesting.PytestDefinitions.ResultsHandler import MeasurementPoint
import logging
from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq
import math


class GainFlatnessWithSweptFrequency(BaseTest):
    def __init__(self, powerRange, freqRange, gateVoltage=None, drainVoltage=None):
        self.powerRange = powerRange
        self.freqRange = freqRange
        self.measurements = []
        self.gateVoltage = gateVoltage
        self.drainVoltage = drainVoltage

    def generate_measurement_points(self):
        for f in self.freqRange:
            for p in self.powerRange:
                self.measurements.append(
                    MeasurementPoint(
                        freq=f,
                        inputPower=p,
                        gateVoltage=self.gateVoltage,
                        drainVoltage=self.drainVoltage,
                    )
                )
        logging.info("Generated datapoints for Frequency swept gain flatness test")
        return self.measurements

    def process_results(self, results):
        logging.info("Processing results for Frequency swept gain flatness test")
        super().retrieve_results(results)
        ws = results.excelFile.add_worksheet("Frequency Swept Gain Flatness")

        measuredFrequencies = [e for e in self.freqRange]
        measuredFrequencies.sort()
        measuredPowers = [e for e in self.powerRange]
        measuredPowers.sort()
        merge_format = results.excelFile.add_format({"align": "center"})
        ws.merge_range(0, 0, 1, 0, "Input Power (dBm)", merge_format)

        for x in measuredPowers:
            ws.write(2 + measuredPowers.index(x), 0, x)

        chart = results.excelFile.add_chart({"type": "scatter", "subtype": "straight"})

        minGain = math.inf
        maxGain = -math.inf

        for f in measuredFrequencies:
            columnIndex = 1 + 2 * measuredFrequencies.index(f)
            ws.merge_range(
                0, columnIndex, 0, columnIndex + 1, readable_freq(f), merge_format
            )
            ws.write(1, columnIndex, "Output Power (dBm)")
            ws.write(1, columnIndex + 1, "Gain (dB)")
            validPoints = [x for x in self.measurements if x.freq == f]
            validPoints.sort(key=lambda x: x.inputPower)
            for x in validPoints:
                # Assert we've got all requested points
                rowIndex = validPoints.index(x)
                assert x.inputPower == measuredPowers[rowIndex]

                gain = x.outputPower - x.inputPower
                minGain = min(minGain, gain)
                maxGain = max(maxGain, gain)

                ws.write(2 + rowIndex, columnIndex, x.outputPower)

                ws.write(2 + rowIndex, columnIndex + 1, gain)

            chart.add_series(
                {
                    "name": f"Output Power - {readable_freq(f)}",
                    "categories": f"='Frequency Swept Gain Flatness'!$A$3:$A${2 + len(validPoints)}",
                    "values": f"='Frequency Swept Gain Flatness'!${chr(66 + 2 * measuredFrequencies.index(f))}$3:"
                    f"${chr(66 + 2 * measuredFrequencies.index(f))}${2 + len(validPoints)}",
                }
            )

            chart.add_series(
                {
                    "name": f"Gain - {readable_freq(f)}",
                    "categories": f"='Frequency Swept Gain Flatness'!$A$3:$A${2 + len(validPoints)}",
                    "values": f"='Frequency Swept Gain Flatness'!${chr(67 + 2 * measuredFrequencies.index(f))}$3:"
                    f"${chr(67 + 2 * measuredFrequencies.index(f))}${2 + len(validPoints)}",
                    "y2_axis": 1,
                }
            )

        chart.set_x_axis(
            {
                "name": "Input Power (dBm)",
                "min": min(measuredPowers),
                "max": max(measuredPowers),
                "crossing": -200,
            }
        )

        chart.set_y_axis({"name": "Output Power (dBm)", "crossing": -200})

        chart.set_y2_axis(
            {
                "name": "Gain (dB)",
                "crossing": -200,
                "min": math.floor(minGain - 0.5),
                "max": math.ceil(maxGain + 0.5),
            }
        )

        chart.set_legend({"position": "bottom"})

        columnIndex = 2 + 2 * len(measuredFrequencies)
        ws.insert_chart(1, columnIndex, chart)

        if self.gateVoltage is not None:
            ws.write(0, columnIndex, "Gate Voltage:")
            ws.write(0, columnIndex + 1, f"{self.gateVoltage}V")
            columnIndex += 3

        if self.drainVoltage is not None:
            ws.write(0, columnIndex, "Drain Voltage:")
            ws.write(0, columnIndex + 1, f"{self.drainVoltage}V")
            columnIndex += 3
