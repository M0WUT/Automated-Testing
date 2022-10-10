import pickle
from datetime import datetime
from time import sleep

from xlsxwriter import Workbook

from AutomatedTesting.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.Instruments.InstrumentConfig import e4433b, u2001a
from AutomatedTesting.UsefulFunctions import readable_freq

with e4433b as sigGen:
    dut = e4433b.reserve_channel(1, "main")
    while True:
        print(
            f"{readable_freq(dut.get_freq())}, {dut.get_power()}, {dut.get_output_state()}"
        )
        sleep(2)
