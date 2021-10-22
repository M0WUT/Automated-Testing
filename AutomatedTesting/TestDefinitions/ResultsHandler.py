import pickle
import os
import xlsxwriter
import logging
from shutil import rmtree


class MeasurementPoint(object):
    def __init__(
        self,
        freq,
        inputPower,
        measureCurrent=False,
        gateVoltage=None,
        drainVoltage=None,
        drainCurrent=None,
        outputPower=None,
    ):
        # Inputs
        self.freq = freq
        self.inputPower = inputPower
        self.gateVoltage = gateVoltage
        self.drainVoltage = drainVoltage
        # Outputs
        self.drainCurrent = drainCurrent
        self.outputPower = outputPower
        # Measurement Settings
        self.measureCurrent = measureCurrent

    def __eq__(self, other):
        return(
            (self.freq == other.freq) and
            (self.inputPower == other.inputPower) and
            (self.gateVoltage == other.gateVoltage) and
            (self.drainVoltage == other.drainVoltage)
        )


class ResultsHandler():
    def __init__(self, name, fileToLoad=None):
        if(fileToLoad is None):
            # New set of results
            self.name = name
            self.measurements = []
            if not os.path.isdir("./Measurements"):
                os.mkdir("./Measurements")
            os.mkdir(f"./Measurements/{name}")
            logging.info(
                f"Results being saved in ./Measurements/{name}"
            )
            self.pickleFile = open(f"./Measurements/{name}/pickle.P", "wb")
            self.excelFile = xlsxwriter.Workbook(
                f"./Measurements/{name}/Results.xlsx"
            )
            self.csvFile = open(f"./Measurements/{name}/Raw.csv", "w+")
        else:
            raise NotImplementedError

            # I think the code below works but not tested
            # so raise error for now

            # Load existing measurements
            self.name = fileToLoad.split("/")[-2]
            self.measurements = pickle.load(
                fileToLoad
            )
            self.pickleFile = open(fileToLoad)
            self.excelFile = xlsxwriter.Workbook(
                "/".join(fileToLoad.split("/")) + "/Raw.xlsx"
            )
            logging.info(
                f"Measurements loaded from {fileToLoad}"
            )

        self.worksheet = self.excelFile.add_worksheet("Raw")
        self.worksheet.write(0, 0, "Frequency (Hz)")
        self.worksheet.write(0, 1, "Input Power (dBm)")
        self.worksheet.write(0, 2, "Gate Voltage (V)")
        self.worksheet.write(0, 3, "Supply Voltage (V)")
        self.worksheet.write(0, 4, "Supply Current (mA)")
        self.worksheet.write(0, 5, "Output Power (dBm)")
        self.csvFile.write(
            "Frequency (Hz),"
            "Input Power (dBm),"
            "Gate Voltage (V),"
            "Supply Voltage (V),"
            "Supply Current (mA),"
            "Output Power (dBm)\n"
        )

    def append(self, x):
        assert isinstance(x, MeasurementPoint)
        self.measurements.append(x)

    def __contains__(self, item):
        assert isinstance(item, MeasurementPoint)
        for x in self.measurements:
            # Primary key is (freq, inputPower, gateVoltage, drainVoltage)
            if x == item:
                return True
        return False

    def save(self):
        pickle.dump(
            self.measurements,
            self.pickleFile
        )

        for x in self.measurements:
            rowIndex = 1 + self.measurements.index(x)
            vgs = str(x.gateVoltage if x.gateVoltage is not None else "N/A")
            vds = str(x.drainVoltage if x.drainVoltage is not None else "N/A")
            ids = str(
                x.drainCurrent * 1000 if x.drainCurrent is not None else "N/A"
            )
            self.worksheet.write(rowIndex, 0, x.freq)
            self.worksheet.write(rowIndex, 1, x.inputPower)
            self.worksheet.write(rowIndex, 2, vgs)
            self.worksheet.write(rowIndex, 3, vds)
            self.worksheet.write(rowIndex, 4, ids)
            self.worksheet.write(rowIndex, 5, x.outputPower)
            self.csvFile.write(
                f"{x.freq},"
                f"{x.inputPower},"
                f"{vgs},"
                f"{vds},"
                f"{ids},"
                f"{x.outputPower}\n"
            )

    def cleanup(self):
        self.save()
        self.pickleFile.close()
        self.excelFile.close()
        self.csvFile.close()
        if self.measurements == []:
            logging.info(
                f"Deleting directory ./Measurements/{self.name} "
                "as no results generated"
            )
            rmtree(f"./Measurements/{self.name}")
