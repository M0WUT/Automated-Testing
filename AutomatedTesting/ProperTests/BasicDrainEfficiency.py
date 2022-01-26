from AutomatedTesting.PytestDefinitions.BaseTest import BaseTest
from AutomatedTesting.PytestDefinitions.ResultsHandler import MeasurementPoint
import logging
from AutomatedTesting.TopLevel.UsefulFunctions import readable_freq
import math


class BasicDrainEfficiency(BaseTest):
    def __init__(
        self, powerRange, measurementFreq, gateVoltage=None, drainVoltage=None
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
                    drainVoltage=self.drainVoltage,
                    measureCurrent=True,
                )
            )
        logging.info("Generated datapoints for Basic drain efficiency test")
        return self.measurements

    def process_results(self, results):
        logging.info("Processing results for Basic drain efficiency test")
        super().retrieve_results(results)
        ws = results.excelFile.add_worksheet("Basic Drain Efficiency")
        # Sort measurements by input power
        self.measurements.sort(key=lambda x: x.inputPower)
        ws.write(0, 0, "Input Power (dBm)")
        ws.write(0, 1, "Drain Current (mA)")
        ws.write(0, 2, "Drain Efficiency (%)")

        maxEff = 0

        for x in self.measurements:
            rowIndex = 1 + self.measurements.index(x)
            ws.write(rowIndex, 0, x.inputPower)
            pin = x.drainVoltage * x.drainCurrent
            pout = 10 ** ((x.outputPower - 30) / 10)

            eff = pout * 100.0 / pin

            maxEff = max(eff, maxEff)

            ws.write(rowIndex, 1, x.drainCurrent * 1000)
            ws.write(rowIndex, 2, eff)

        chart = results.excelFile.add_chart({"type": "scatter", "subtype": "straight"})

        chart.add_series(
            {
                "name": "Drain Current",
                "categories": f"='Basic Drain Efficiency'!$A$2:"
                f"$A{1 + len(self.measurements)}",
                "values": f"='Basic Drain Efficiency'!$B$2:"
                f"$B{1 + len(self.measurements)}",
            }
        )

        chart.add_series(
            {
                "name": "Efficiency",
                "categories": f"='Basic Drain Efficiency'!$A$2:"
                f"$A{1 + len(self.measurements)}",
                "values": f"='Basic Drain Efficiency'!$C$2:"
                f"$C{1 + len(self.measurements)}",
                "y2_axis": 1,
            }
        )

        chart.set_x_axis(
            {
                "name": "Input Power (dBm)",
                "min": self.measurements[0].inputPower,
                "max": self.measurements[-1].inputPower,
                "crossing": -200,
            }
        )

        chart.set_y_axis({"name": "Drain Current (mA)", "crossing": -200})

        chart.set_y2_axis(
            {
                "name": "Drain Efficiency (%)",
                "crossing": -200,
                "max": math.ceil(maxEff / 10) * 10,
            }
        )

        chart.set_legend({"position": "bottom"})

        ws.insert_chart("E2", chart)

        columnIndex = 4

        if self.gateVoltage:
            ws.write(0, columnIndex, "Gate Voltage:")
            ws.write(0, columnIndex + 1, f"{self.gateVoltage}V")
            columnIndex += 3

        if self.drainVoltage:
            ws.write(0, columnIndex, "Drain Voltage:")
            ws.write(0, columnIndex + 1, f"{self.drainVoltage}V")
            columnIndex += 3

        ws.write(0, columnIndex, "Measurement Frequency:")
        ws.write(0, columnIndex + 1, f"{readable_freq(self.measurementFreq)}")
        columnIndex += 3
