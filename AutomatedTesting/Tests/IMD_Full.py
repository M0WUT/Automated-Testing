import logging
import math
import pickle
from dataclasses import dataclass, field
from typing import Optional

import xlsxwriter

from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGeneratorChannel,
)
from AutomatedTesting.Instruments.spectrum_analyser.spectrum_analyser import (
    spectrum_analyser,
)
from AutomatedTesting.Misc.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.Misc.UsefulFunctions import (
    StraightLine,
    best_fit_line_with_known_gradient,
    intercept_point,
    readable_freq,
)


@dataclass
class IMDMeasurementPoint:
    tone_setpoint: float
    # Save all IMD tone power in dictionary
    # Key is the IMDn product with 0.1 added to indicate the upper tone
    # i.e. the value at index '3' corresponds to IMD3 (lower tone)
    # the value at index 5.1 corresponds to IMD5 (upper tone)
    # 0 is used for the input tone
    imd_points: dict[float, float] = field(default_factory=dict)


@dataclass
class SingleFreqSingleIMDPoint:
    best_fit: Optional[StraightLine] = None
    iipn: Optional[float] = None
    oipn: Optional[float] = None


def run_imd_test(
    freq_list: list[int],
    tone_spacing: int,
    channel1: SignalGeneratorChannel,
    channel2: SignalGeneratorChannel,
    spectrum_analyser: spectrum_analyser,
    lower_power_limit: float,
    upper_power_limit: float,
    ref_level: float,
    intermod_terms: Optional[list[int]] = None,
    # Offset of signal generator relative to spectrum analyser
    # e.g. for 2m transverter at 144MHz with a input of 28MHz
    # this should be set to -116e6
    freq_offset: float = 0,
    rbw: Optional[int] = None,
    use_zero_span: bool = False,
    pickle_file: Optional[str] = None,
    excel_workbook: Optional[xlsxwriter.workbook.Workbook] = None,
    combiner_insertion_loss: float = 3.3,
):
    datapoints: list[IMDMeasurementPoint]
    imd_sweeps: dict[float, list[IMDMeasurementPoint]]
    results: dict[float, dict]
    worksheet: ExcelWorksheetWrapper

    results = {}

    if not pickle_file:
        imd_sweeps = {}

        channel1.set_power(lower_power_limit)
        channel2.set_power(lower_power_limit)

        # Setup Spectrum analyser
        spectrum_analyser.set_ref_level(ref_level)
        if rbw:
            if rbw > tone_spacing / 20:
                logging.warning(
                    f"Requested RBW of {rbw} is too large"
                    "(> Tone Spacing / 20) and may lead to inaccurate"
                    " results"
                )

        spectrum_analyser.set_rbw(
            rbw if rbw else pow(10, math.floor(math.log10(tone_spacing / 20)))
        )

        # Sanity check measurement
        assert intermod_terms is not None, "No Measurement Requested"

        for x in intermod_terms:
            # All intermod terms must be odd
            assert (x > 1) and (x % 2 == 1), "Can only handle odd intermod terms"

        if use_zero_span:
            spectrum_analyser.set_span(0)
            spectrum_analyser.set_sweep_time(10)
            measure_power = spectrum_analyser.measure_power_zero_span
        else:
            max_intermod = max(intermod_terms)
            spectrum_analyser.set_span(tone_spacing * (max_intermod + 1))
            measure_power = spectrum_analyser.measure_power

        for freq in freq_list:
            datapoints = []
            channel1.disable_output()
            channel2.disable_output()

            f1 = freq - 0.5 * tone_spacing
            f2 = freq + 0.5 * tone_spacing
            channel1.set_power(lower_power_limit)
            channel1.set_freq(f1 + freq_offset)
            channel2.set_power(lower_power_limit)
            channel2.set_freq(f2 + freq_offset)

            spectrum_analyser.set_centre_freq(freq)

            channel1.enable_output()
            channel2.enable_output()

            power = lower_power_limit
            while power <= upper_power_limit:
                spectrum_analyser.set_ref_level(ref_level)
                channel1.set_power(round(power + combiner_insertion_loss, 3))
                channel2.set_power(round(power + combiner_insertion_loss, 3))
                spectrum_analyser.trigger_sweep()
                spectrum_analyser.set_ref_level(int(measure_power(f1)) + 5)
                spectrum_analyser.trigger_sweep()

                new_datapoint = IMDMeasurementPoint(tone_setpoint=power)

                new_datapoint.imd_points[1.1] = measure_power(f2)
                new_datapoint.imd_points[1] = measure_power(f1)

                # Iterate over all the requested intermod measurements
                for x in intermod_terms:
                    new_datapoint.imd_points[(x + 0.1)] = measure_power(
                        0.5 * (x + 1) * f2 - 0.5 * (x - 1) * f1
                    )
                    new_datapoint.imd_points[(x)] = measure_power(
                        0.5 * (x + 1) * f1 - 0.5 * (x - 1) * f2
                    )

                datapoints.append(new_datapoint)

                # Increase in 0.3dB steps
                power += 0.3
            # Save sweep to dictionary of IMD sweeps
            imd_sweeps[freq] = datapoints

        # Save results
        with open("imdTest.P", "wb") as pickle_file:
            pickle.dump(imd_sweeps, pickle_file)
    else:
        # Load results from file
        with open(pickle_file, "rb") as saved_data:
            imd_sweeps = pickle.load(saved_data)

    # We've got results, now process them
    if excel_workbook:
        workbook = excel_workbook
    else:
        workbook = xlsxwriter.Workbook("imdTest.xlsx")

    overall_worksheet_name = "Overall IMD results"
    overall_worksheet = workbook.add_worksheet(overall_worksheet_name)
    # Update worksheet to class with M0WUT wrapper
    overall_worksheet.__class__ = ExcelWorksheetWrapper
    overall_worksheet.initialise(name=overall_worksheet_name)
    overall_worksheet.set_column(first_col=0, last_col=0, width=140)
    overall_worksheet.set_column(first_col=1, last_col=200, width=18)
    chart = workbook.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
    overall_worksheet.chart = chart
    chart.set_title({"name": "Intermodulation Distortion"})
    chart.set_size({"x_scale": 2, "y_scale": 2})
    overall_worksheet.headers_column = 1
    overall_worksheet.insert_chart(overall_worksheet.headers_row, 0, chart)

    # Have to rediscover details about the sweep as we may have
    # loaded the results
    swept_frequencies = list(imd_sweeps.keys())
    swept_frequencies.sort()
    for freq in swept_frequencies:
        worksheet_name = f"IMD Measurements - {readable_freq(freq)}"
        worksheet = workbook.add_worksheet(worksheet_name)

        worksheet.__class__ = ExcelWorksheetWrapper
        worksheet.initialise(name=worksheet_name)

        worksheet.set_column(first_col=0, last_col=0, width=140)
        worksheet.set_column(first_col=1, last_col=200, width=18)
        worksheet.headers_column = 1

        datapoints = imd_sweeps[freq]
        freq_results = {}

        # @ TODO Add equipment information

        # Leave left column blank for the chart
        worksheet.current_column = 1

        # Create chart object and headings
        centred_format = workbook.add_format({"align": "center"})

        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        worksheet.chart = chart
        chart.set_title({"name": f"IMD - {readable_freq(freq)}"})
        chart.set_size({"x_scale": 2, "y_scale": 2})

        worksheet.insert_chart(worksheet.headers_row, 0, chart)

        # Attempt to linearise all of the curves and add headings for
        # measurements and best fit lines (if we could find one)

        # Ensure datapoints are sorted in increasing tone power
        datapoints.sort(key=lambda x: x.tone_setpoint)

        # Write setpoint
        worksheet.write_and_move_down("Tone Setpoint")
        for x in datapoints:
            worksheet.write_and_move_down(x.tone_setpoint)
        worksheet.hide_current_row()
        worksheet.write_and_move_down(100)
        worksheet.new_column()
        worksheet.current_row = worksheet.headers_row

        # Work out what IMD products have been measured (in case loaded)
        # from file
        measured_imd_temrs = [
            x for x in datapoints[0].imd_points.keys() if isinstance(x, int)
        ]

        measured_imd_temrs.sort()

        for imd_tone in measured_imd_temrs:
            measured_ipn = SingleFreqSingleIMDPoint()
            # Work through all measured IMD products

            # Upper tone
            if imd_tone == 1:
                tone_name = "Tone"
            else:
                tone_name = f"IMD{imd_tone}"

            worksheet.write_and_move_down(f"{tone_name} - Upper")
            for x in datapoints:
                worksheet.write_and_move_down(x.imd_points[imd_tone + 0.1])
            worksheet.plot_current_column()
            worksheet.new_column()
            worksheet.current_row = worksheet.headers_row

            # Lower tone
            worksheet.write_and_move_down(f"{tone_name} - Lower")
            for x in datapoints:
                worksheet.write_and_move_down(x.imd_points[imd_tone])
            worksheet.plot_current_column()
            worksheet.new_column()
            worksheet.current_row = worksheet.headers_row

            # Best fit on average of both tones
            measured_ipn.best_fit = best_fit_line_with_known_gradient(
                [x.tone_setpoint for x in datapoints],
                [
                    0.5 * (x.imd_points[imd_tone] + x.imd_points[imd_tone + 0.1])
                    for x in datapoints
                ],
                expectedGradient=imd_tone,
            )

            if imd_tone == 1:
                assert measured_ipn.best_fit, "Couldn't fit line to tone power"
                tone_best_fit = measured_ipn.best_fit

            if measured_ipn.best_fit:
                worksheet.hide_current_column()
                worksheet.write_and_move_down(f"{tone_name} - Best Fit")
                for x in datapoints:
                    worksheet.write_and_move_down(
                        measured_ipn.best_fit.evaluate(x.tone_setpoint)
                    )
                # Super high power point for trace extrapolation
                worksheet.write_and_move_down(measured_ipn.best_fit.evaluate(100))
                worksheet.new_column()
                worksheet.current_row = worksheet.headers_row

                if imd_tone > 1:
                    measured_ipn.iipn, measured_ipn.oipn = intercept_point(
                        measured_ipn.best_fit, tone_best_fit
                    )

                column = chr(worksheet.current_column - 1 + ord("A"))
                headers_column = chr(worksheet.headers_column + ord("A"))
                start_row = worksheet.headers_row + 2
                chart.add_series(
                    {
                        "name": f"{tone_name} - Best Fit",
                        "categories": f"='{worksheet.name}'"
                        f"!${headers_column}${start_row}:"
                        f"${headers_column}{worksheet.max_row + 1}",
                        "values": f"='{worksheet.name}'!${column}${start_row}:"
                        f"${column}{worksheet.max_row + 1}",
                        "line": {"dash_type": "round_dot"},
                    }
                )

            freq_results[imd_tone] = measured_ipn
        results[freq] = freq_results

        worksheet.merge_range(
            worksheet.headers_row - 1,
            1,
            worksheet.headers_row - 1,
            worksheet.max_column,
            "Output Power per Tone (dBm)",
            centred_format,
        )

        # Plot markers for each of the IPn points
        # Bearing in mind, there might not be any
        category_string = "={"
        value_string = "={"
        max_x = upper_power_limit
        min_x = lower_power_limit
        # min_y = Highest order IMD (as assume it'll be the lowest signal
        # level) of first data point
        min_y = datapoints[0].imd_points[max(measured_imd_temrs)]
        # max_y = 1st tone (fundamental) of final data point
        max_y = datapoints[-1].imd_points[1]

        ipn_labels = []
        num_best_fit_lines = 0
        for imd_tone, x in freq_results.items():
            if imd_tone != 1 and x.iipn is not None:
                category_string += f"{x.iipn},"
                value_string += f"{x.oipn},"
                ipn_labels.append(
                    {
                        "value": f"IIP{imd_tone} = {round(x.iipn, 1)}dBm\n"
                        f"OIP{imd_tone} = {round(x.oipn, 1)}dBm"
                    }
                )
                max_x = max(max_x, x.iipn)
                min_x = min(min_x, x.iipn)
                max_y = max(max_y, x.oipn)
                min_y = min(min_y, x.oipn)
                num_best_fit_lines += 1

        category_string = category_string[:-1] + "}"
        value_string = value_string[:-1] + "}"

        if "." in category_string:
            # We actually have some data to plot
            chart.add_series(
                {
                    "name": "IPn",
                    "categories": category_string,
                    "values": value_string,
                    "line": {"none": True},
                    "marker": {
                        "type": "square",
                        "size": 5,
                        "fill": {"color": "red"},
                    },
                    "data_labels": {
                        "values": True,
                        "custom": ipn_labels,
                        "position": "below",
                        "border": {"color": "red"},
                        "fill": {"color": "yellow"},
                    },
                }
            )
        ipn_series_index = 2 * len(intermod_terms) + 3 + num_best_fit_lines
        chart.set_legend({"delete_series": [ipn_series_index]})

        chart.show_hidden_data()
        chart.set_x_axis(
            {
                "name": "Tone Setpoint (dBm)",
                "min": 5 * math.floor(min_x / 5),
                "max": 5 * math.ceil(1 + max_x / 5),
                "crossing": -200,
                "major_unit": 5,
                "major_gridlines": {"visible": True},
            }
        )

        chart.set_y_axis(
            {
                "name": "Power per Tone (dBm)",
                "crossing": -200,
                "min": 5 * math.floor(min_y / 5 - 1),
                "max": 5 * math.ceil(1 + max_y / 5),
                "major_unit": 10,
                "minor_unit": 5,
                "major_gridlines": {"visible": True},
                "minor_gridlines": {"visible": True},
            }
        )

    # # We now have all the data plotted so add a final sheet
    # # with the overall results
    overall_worksheet.new_column()
    overall_worksheet.write_and_move_down("Frequency (MHz)")
    for freq in results:
        overall_worksheet.write_and_move_down(freq / 1e6)
    overall_worksheet.new_column()
    worksheet = overall_worksheet
    chart = worksheet.chart
    chart.show_blanks_as("span")
    chart.set_x_axis(
        {
            "name": "Frequency (MHz)",
            "crossing": -200,
            "major_gridlines": {"visible": True},
        }
    )

    chart.set_y_axis(
        {
            "name": "Power per Tone (dBm)",
            "crossing": -200,
            "major_gridlines": {"visible": True},
            "minor_gridlines": {"visible": True},
        }
    )
    for imd in intermod_terms:
        worksheet.write_and_move_down(f"IIP{imd} (dBm)")
        got_results = False
        for freq in results:
            try:
                x = results[freq][imd].iipn
                worksheet.write_and_move_down(round(x, 2) if x else "")
                got_results = True
            except KeyError:
                worksheet.write_and_move_down("")
        if got_results:
            column = chr(worksheet.current_column + ord("A"))
            headers_column = chr(worksheet.headers_column + ord("A"))
            start_row = worksheet.headers_row + 2
            chart.add_series(
                {
                    "name": f"IIP{imd}",
                    "categories": f"='{worksheet.name}'!${headers_column}${start_row}:"
                    f"${headers_column}{worksheet.max_row + 1}",
                    "values": f"='{worksheet.name}'!${column}${start_row}:"
                    f"${column}{worksheet.max_row + 1}",
                    "line": {"dash_type": "round_dot"},
                }
            )

        worksheet.new_column()
        worksheet.write_and_move_down(f"OIP{imd} (dBm)")

        for freq in results:
            try:
                x = results[freq][imd].oipn
                worksheet.write_and_move_down(round(x, 2) if x else "")

            except KeyError:
                worksheet.write_and_move_down("")

        column = chr(worksheet.current_column + ord("A"))
        headers_column = chr(worksheet.headers_column + ord("A"))
        start_row = worksheet.headers_row + 2
        chart.add_series(
            {
                "name": f"OIP{imd}",
                "categories": f"='{worksheet.name}'!${headers_column}${start_row}:"
                f"${headers_column}{worksheet.max_row + 1}",
                "values": f"='{worksheet.name}'!${column}${start_row}:"
                f"${column}{worksheet.max_row + 1}",
                "line": {"dash_type": "round_dot"},
            }
        )
        worksheet.new_column()

    if not excel_workbook:
        workbook.close()
