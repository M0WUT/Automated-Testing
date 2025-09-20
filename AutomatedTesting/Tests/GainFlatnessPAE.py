import pickle
from dataclasses import dataclass
from time import sleep
from typing import Optional, Union

import xlsxwriter

from AutomatedTesting.Instruments.DigitalMultimeter.DigitalMultimeter import (
    DigitalMultimeter,
)
from AutomatedTesting.Instruments.PowerMeter.PowerMeter import PowerMeter
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGeneratorChannel,
)
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)
from AutomatedTesting.Misc.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.Misc.UsefulFunctions import readable_freq


@dataclass
class SingleMeasurement:
    input_power: float
    output_power: float
    gain: float
    dc_voltage: float
    dc_current: float
    pae: float


def run_gain_flatness_test(
    freq_list: list[int],
    input_power_list: list[float],
    sig_gen: SignalGeneratorChannel,
    power_meter: Union[PowerMeter, SpectrumAnalyser],
    ref_level: float,
    dmm: DigitalMultimeter,
    supply_voltage: float = 5,
    loss_before_dut: float = 0.2,
    loss_after_dut: float = 0.5,
    pickle_file: Optional[str] = None,
    excel_workbook: Optional[xlsxwriter.workbook.Workbook] = None,
):
    if pickle_file is None:
        results = {}
        if isinstance(power_meter, SpectrumAnalyser):
            power_meter.set_span(1e6)
            power_meter.set_rbw(10e3)
            power_meter.set_ref_level(30)
        sig_gen.set_freq(min(freq_list))
        sig_gen.set_power(min(input_power_list) + loss_before_dut)
        sig_gen.enable_output()
        for freq in freq_list:
            results[freq] = []
            sig_gen.set_freq(freq)
            if isinstance(power_meter, SpectrumAnalyser):
                power_meter.set_centre_freq(freq)
            for power in input_power_list:
                if isinstance(power_meter, SpectrumAnalyser):
                    power_meter.set_ref_level(ref_level)

                sig_gen.set_power(power + loss_before_dut)

                sleep(0.1)
                if isinstance(power_meter, SpectrumAnalyser):
                    power_meter.trigger_sweep()
                output_power = power_meter.measure_power(freq)
                if isinstance(power_meter, SpectrumAnalyser):
                    power_meter.set_ref_level(int(output_power) + 10)
                    power_meter.trigger_sweep()
                    output_power = power_meter.measure_power(freq)
                dut_input_power = power
                dut_output_power = output_power + loss_after_dut
                gain = dut_output_power - dut_input_power
                dut_input_power_watts = 10 ** ((dut_input_power - 30) / 10)
                dut_output_power_watts = 10 ** ((dut_output_power - 30) / 10)
                dut_dc_current = dmm.measure_dc_current()
                dut_dc_power = supply_voltage * dut_dc_current
                pae = (
                    100
                    * (dut_output_power_watts - dut_input_power_watts)
                    / dut_dc_power
                )
                results[freq].append(
                    SingleMeasurement(
                        input_power=dut_input_power,
                        output_power=dut_output_power,
                        gain=gain,
                        dc_voltage=supply_voltage,
                        dc_current=dut_dc_current,
                        pae=pae,
                    )
                )

        # Save results
        with open("pae.P", "wb") as pickle_file:
            pickle.dump(results, pickle_file)
    else:
        # Load results from file
        with open(pickle_file, "rb") as saved_data:
            results = pickle.load(saved_data)

    # We've got results, now process them
    if excel_workbook:
        workbook = excel_workbook
    else:
        workbook = xlsxwriter.Workbook("pae.xlsx")

    worksheet_name = "Overall IMD results"
    worksheet = workbook.add_worksheet(worksheet_name)

    worksheet.__class__ = ExcelWorksheetWrapper
    worksheet.initialise(name="Power Added Efficiency")
    worksheet.set_column(first_col=0, last_col=0, width=140)
    worksheet.set_column(first_col=1, last_col=200, width=18)
    chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
    worksheet.chart = chart
    chart.set_title({"name": "Gain (solid) / PAE (dashed)"})
    chart.set_size({"x_scale": 2, "y_scale": 2})

    chart.set_x_axis({"name": "Input Power (dBm)", "crossing": "min"})

    chart.set_y_axis({"name": "Gain (dB)", "crossing": "min"})

    chart.set_y2_axis(
        {
            "name": "Power Added Efficiency (%)",
            "min": 0,
            "max": 100,
            "major_unit": 10,
            "minor_unit": 5,
            "major_gridlines": {"visible": True, "line": {"dash_type": "dash"}},
            "visible": True,
            "crossing": "min",
        }
    )
    worksheet.headers_column = 1
    worksheet.insert_chart(worksheet.headers_row, 0, chart)

    # Leave left column blank for the chart
    worksheet.current_column = 1

    # Have to rediscover details about the sweep as we may have
    # loaded the results
    swept_frequencies = list(results.keys())
    swept_frequencies.sort()

    assert len(swept_frequencies) <= len(worksheet.AVAILABLE_COLOURS)

    for freq, colour in zip(swept_frequencies, worksheet.AVAILABLE_COLOURS):
        # Only look at datapoints for this frequency and sort by input power
        datapoints = results[freq]
        datapoints.sort(key=lambda x: x.input_power)
        # Check if first column so we'll need to to plot input power too
        if freq == min(swept_frequencies):
            worksheet.write_and_move_down("Input Power (dBm)")
            for data in datapoints:
                worksheet.write_and_move_down(data.input_power)
            worksheet.new_column()

        worksheet.write_and_move_down(f"Output Power (dBm) - {readable_freq(freq)}")
        for data in datapoints:
            worksheet.write_and_move_down(round(data.output_power, 2))
        worksheet.new_column()

        worksheet.write_and_move_down(f"Gain (dB) - {readable_freq(freq)}")
        for data in datapoints:
            worksheet.write_and_move_down(round(data.gain, 2))
        worksheet.plot_current_column(
            {"line": {"color": colour}, "name": readable_freq(freq)}
        )
        worksheet.new_column()

        worksheet.write_and_move_down(f"Supply Voltage (V) - {readable_freq(freq)}")
        for data in datapoints:
            worksheet.write_and_move_down(round(data.dc_voltage, 2))
        worksheet.new_column()

        worksheet.write_and_move_down(f"Supply Current (mA) - {readable_freq(freq)}")
        for data in datapoints:
            worksheet.write_and_move_down(int(1000 * data.dc_current))
        worksheet.new_column()

        worksheet.write_and_move_down(f"PAE (%) - {readable_freq(freq)}")
        for data in datapoints:
            worksheet.write_and_move_down(round(data.pae, 1))
        worksheet.plot_current_column(
            {
                "y2_axis": 1,
                "line": {"color": colour, "dash_type": "dash"},
                "name": readable_freq(freq),
            }
        )
        worksheet.new_column()

    chart.set_legend(
        {
            "position": "bottom",
            "delete_series": [
                x for x in range(len(swept_frequencies), 2 * len(swept_frequencies))
            ],
        }
    )

    if not excel_workbook:
        workbook.close()
