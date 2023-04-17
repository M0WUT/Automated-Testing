import pickle
from datetime import datetime
from time import sleep

from xlsxwriter import Workbook

from AutomatedTesting.Instruments.InstrumentConfig import e4433b, u2001a
from AutomatedTesting.Misc.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.Misc.UsefulFunctions import readable_freq

MIN_POWER = -60
MAX_POWER = 13
STEP = 1

powerSteps = list(range(MIN_POWER, MAX_POWER + 1, STEP))

results = {}

pickleFile = ""  # "imdTest.P"

if pickleFile:
    with open(pickleFile, "rb") as savedData:
        results = pickle.load(savedData)
else:
    results[0] = powerSteps
    with e4433b as sigGen, u2001a as powerMeter:
        testSource = sigGen.reserve_channel(1, "Test Source")
        powerMeter.reserve("Power Meter")
        testSource.enable_output()
        testSource.set_soft_power_limits(-60, 13)
        for freq in [10e6, 50e6, 100e6, 500e6, 1e9, 2e9, 4e9, 6e9]:
            singleFreqResults = []
            testSource.set_freq(freq)
            powerMeter.set_freq(freq)
            for power in powerSteps:
                testSource.set_power(power)
                sleep(1)
                singleFreqResults.append(powerMeter.measure_power(freq))
            results[freq] = singleFreqResults
    # Save results to Pickle File
    with open("imdTest.P", "wb") as pickleFile:
        pickle.dump(results, pickleFile)

now = datetime.now().strftime("%Y%m%d-%H%M%S")
resultsDirectory = "/mnt/Transit"

with Workbook(f"{resultsDirectory}/results_{now}.xlsx") as workbook:
    worksheet = workbook.add_worksheet("Results")
    worksheet.__class__ = ExcelWorksheetWrapper
    worksheet.initialise("Results")
    for freq, powers in results.items():
        worksheet.write_and_move_down(
            readable_freq(freq) if freq != 0 else "Requested Power"
        )
        for x in powers:
            worksheet.write_and_move_down(round(x, 2))
        worksheet.new_column()
