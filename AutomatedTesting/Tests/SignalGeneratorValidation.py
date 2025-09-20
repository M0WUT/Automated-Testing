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

power_steps = list(range(MIN_POWER, MAX_POWER + 1, STEP))

results = {}

pickle_file = ""  # "imdTest.P"

if pickle_file:
    with open(pickle_file, "rb") as saved_data:
        results = pickle.load(saved_data)
else:
    results[0] = power_steps
    with e4433b as sig_gen, u2001a as power_meter:
        test_source = sig_gen.reserve_channel(1, "Test Source")
        power_meter.reserve("Power Meter")
        test_source.enable_output()
        test_source.set_soft_power_limits(-60, 13)
        for freq in [10e6, 50e6, 100e6, 500e6, 1e9, 2e9, 4e9, 6e9]:
            single_freq_results = []
            test_source.set_freq(freq)
            power_meter.set_freq(freq)
            for power in power_steps:
                test_source.set_power(power)
                sleep(1)
                single_freq_results.append(power_meter.measure_power(freq))
            results[freq] = single_freq_results
    # Save results to Pickle File
    with open("imdTest.P", "wb") as pickle_file:
        pickle.dump(results, pickle_file)

now = datetime.now().strftime("%Y%m%d-%H%M%S")
results_directory = "/mnt/Transit"

with Workbook(f"{results_directory}/results_{now}.xlsx") as workbook:
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
