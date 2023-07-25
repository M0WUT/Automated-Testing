import argparse
import logging
import math
import pickle
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Union

import xlsxwriter

from AutomatedTesting.Instruments.InstrumentConfig import sdg2122x, ssa3032x
from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import (
    SignalGenerator,
    SignalGeneratorChannel,
)
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
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
    toneSetpoint: float
    # Save all IMD tone power in dictionary
    # Key is the IMDn product with 0.1 added to indicate the upper tone
    # i.e. the value at index '3' corresponds to IMD3 (lower tone)
    # the value at index 5.1 corresponds to IMD5 (upper tone)
    # 0 is used for the input tone
    imdPoints: "dict[float, float]" = field(default_factory=dict)


@dataclass
class SingleFreqSingleIMDPoint:
    best_fit: StraightLine = None
    iipn: float = None
    oipn: float = None


def run_imd_test(
    freqList: List[int],
    toneSpacing: int,
    channel1: SignalGeneratorChannel,
    channel2: SignalGeneratorChannel,
    spectrumAnalyser: SpectrumAnalyser,
    lowerPowerLimit: float,
    upperPowerLimit: float,
    refLevel: float,
    intermodTerms: Optional[list[int]] = None,
    # Offset of signal generator relative to spectrum analyser
    # e.g. for 2m transverter at 144MHz with a input of 28MHz
    # this should be set to -116e6
    freqOffset: float = 0,
    resolutionBandWidth: int = None,
    useZeroSpan: bool = False,
    pickleFile: str = None,
    excelWorkbook: Optional[xlsxwriter.workbook.Workbook] = None,
    combinerInsertionLoss: float = 3.3,
):
    datapoints: List[IMDMeasurementPoint]
    imdSweeps: "dict[float, List[IMDMeasurementPoint]]"
    results: "dict[float, dict]"
    worksheet: ExcelWorksheetWrapper

    results = {}

    if not pickleFile:
        imdSweeps = {}

        channel1.set_power(lowerPowerLimit)
        channel2.set_power(lowerPowerLimit)

        # Setup Spectrum analyser
        spectrumAnalyser.set_ref_level(refLevel)
        if resolutionBandWidth:
            if resolutionBandWidth > toneSpacing / 20:
                logging.warning(
                    f"Requested RBW of {resolutionBandWidth} is too large"
                    "(> Tone Spacing / 20) and may lead to inaccurate"
                    " results"
                )

        spectrumAnalyser.set_rbw(
            resolutionBandWidth
            if resolutionBandWidth
            else pow(10, math.floor(math.log10(toneSpacing / 20)))
        )

        # Sanity check measurement
        assert intermodTerms is not None, "No Measurement Requested"

        for x in intermodTerms:
            # All intermod terms must be odd
            assert (x > 1) and (x % 2 == 1), "Can only handle odd intermod terms"

        if useZeroSpan:
            spectrumAnalyser.set_span(0)
            spectrumAnalyser.set_sweep_time(10)
            measure_power = spectrumAnalyser.measure_power_zero_span
        else:
            maxIntermod = max(intermodTerms)
            spectrumAnalyser.set_span(toneSpacing * (maxIntermod + 1))
            measure_power = spectrumAnalyser.measure_power

        for freq in freqList:
            datapoints = []
            channel1.disable_output()
            channel2.disable_output()

            f1 = freq - 0.5 * toneSpacing
            f2 = freq + 0.5 * toneSpacing
            channel1.set_power(lowerPowerLimit)
            channel1.set_freq(f1 + freqOffset)
            channel2.set_power(lowerPowerLimit)
            channel2.set_freq(f2 + freqOffset)

            spectrumAnalyser.set_centre_freq(freq)

            # Get Noise Floor with no tones
            # This allows for faster sweeping by ignoring points
            # with negligible IMD
            spectrumAnalyser.trigger_sweep()
            noiseFloor = measure_power(f1)

            channel1.enable_output()
            channel2.enable_output()

            power = lowerPowerLimit
            while power <= upperPowerLimit:
                spectrumAnalyser.set_ref_level(refLevel)
                channel1.set_power(round(power + combinerInsertionLoss, 3))
                channel2.set_power(round(power + combinerInsertionLoss, 3))
                spectrumAnalyser.trigger_sweep()
                spectrumAnalyser.set_ref_level(int(measure_power(f1)) + 5)
                spectrumAnalyser.trigger_sweep()

                newDatapoint = IMDMeasurementPoint(toneSetpoint=power)

                newDatapoint.imdPoints[1.1] = measure_power(f2)
                newDatapoint.imdPoints[1] = measure_power(f1)

                # Iterate over all the requested intermod measurements
                for x in intermodTerms:
                    newDatapoint.imdPoints[(x + 0.1)] = measure_power(
                        0.5 * (x + 1) * f2 - 0.5 * (x - 1) * f1
                    )
                    newDatapoint.imdPoints[(x)] = measure_power(
                        0.5 * (x + 1) * f1 - 0.5 * (x - 1) * f2
                    )

                datapoints.append(newDatapoint)

                # Increase in 0.25dB steps
                power += 0.25
            # Save sweep to dictionary of IMD sweeps
            imdSweeps[freq] = datapoints

        # Save results
        with open("imdTest.P", "wb") as pickleFile:
            pickle.dump(imdSweeps, pickleFile)
    else:
        # Load results from file
        with open(pickleFile, "rb") as savedData:
            imdSweeps = pickle.load(savedData)

    # We've got results, now process them
    if excelWorkbook:
        workbook = excelWorkbook
    else:
        workbook = xlsxwriter.Workbook("imdTest.xlsx")

    overallResultsWorksheetName = "Overall IMD results"
    overallWorksheet = workbook.add_worksheet(overallResultsWorksheetName)
    # Update worksheet to class with M0WUT wrapper
    overallWorksheet.__class__ = ExcelWorksheetWrapper
    overallWorksheet.initialise(name=overallResultsWorksheetName)
    overallWorksheet.set_column(first_col=0, last_col=0, width=140)
    overallWorksheet.set_column(first_col=1, last_col=200, width=18)
    chart = workbook.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
    overallWorksheet.chart = chart
    chart.set_title({"name": "Intermodulation Distortion"})
    chart.set_size({"x_scale": 2, "y_scale": 2})
    overallWorksheet.headers_column = 1
    overallWorksheet.insert_chart(overallWorksheet.headers_row, 0, chart)

    # Have to rediscover details about the sweep as we may have
    # loaded the results
    sweptFrequencies = list(imdSweeps.keys())
    sweptFrequencies.sort()
    for freq in sweptFrequencies:
        worksheetName = f"IMD Measurements - {readable_freq(freq)}"
        worksheet = workbook.add_worksheet(worksheetName)

        worksheet.__class__ = ExcelWorksheetWrapper
        worksheet.initialise(name=worksheetName)

        worksheet.set_column(first_col=0, last_col=0, width=140)
        worksheet.set_column(first_col=1, last_col=200, width=18)
        worksheet.headers_column = 1

        datapoints = imdSweeps[freq]
        freqResults = {}

        # @ TODO Add equipment information

        # Leave left column blank for the chart
        worksheet.current_column = 1

        # Create chart object and headings
        centeredFormat = workbook.add_format({"align": "center"})

        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        worksheet.chart = chart
        chart.set_title({"name": f"IMD - {readable_freq(freq)}"})
        chart.set_size({"x_scale": 2, "y_scale": 2})

        worksheet.insert_chart(worksheet.headers_row, 0, chart)

        # Attempt to linearise all of the curves and add headings for
        # measurements and best fit lines (if we could find one)

        # Ensure datapoints are sorted in increasing tone power
        datapoints.sort(key=lambda x: x.toneSetpoint)

        # Write setpoint
        worksheet.write_and_move_down("Tone Setpoint")
        for x in datapoints:
            worksheet.write_and_move_down(x.toneSetpoint)
        worksheet.hide_current_row()
        worksheet.write_and_move_down(100)
        worksheet.new_column()
        worksheet.current_row = worksheet.headers_row

        # Work out what IMD products have been measured (in case loaded)
        # from file
        measuredIMDTerms = [
            x for x in datapoints[0].imdPoints.keys() if isinstance(x, int)
        ]

        measuredIMDTerms.sort()

        for imdTone in measuredIMDTerms:
            measuredIPn = SingleFreqSingleIMDPoint()
            # Work through all measured IMD products

            # Upper tone
            if imdTone == 1:
                toneName = "Tone"
            else:
                toneName = f"IMD{imdTone}"

            worksheet.write_and_move_down(f"{toneName} - Upper")
            for x in datapoints:
                worksheet.write_and_move_down(x.imdPoints[imdTone + 0.1])
            worksheet.plot_current_column()
            worksheet.new_column()
            worksheet.current_row = worksheet.headers_row

            # Lower tone
            worksheet.write_and_move_down(f"{toneName} - Lower")
            for x in datapoints:
                worksheet.write_and_move_down(x.imdPoints[imdTone])
            worksheet.plot_current_column()
            worksheet.new_column()
            worksheet.current_row = worksheet.headers_row

            # Best fit on average of both tones
            measuredIPn.best_fit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [
                    0.5 * (x.imdPoints[imdTone] + x.imdPoints[imdTone + 0.1])
                    for x in datapoints
                ],
                expectedGradient=imdTone,
            )

            if imdTone == 1:
                assert measuredIPn.best_fit, "Couldn't fit line to tone power"
                tone_best_fit = measuredIPn.best_fit

            if measuredIPn.best_fit:
                worksheet.hide_current_column()
                worksheet.write_and_move_down(f"{toneName} - Best Fit")
                for x in datapoints:
                    worksheet.write_and_move_down(
                        measuredIPn.best_fit.evaluate(x.toneSetpoint)
                    )
                # Super high power point for trace extrapolation
                worksheet.write_and_move_down(measuredIPn.best_fit.evaluate(100))
                worksheet.new_column()
                worksheet.current_row = worksheet.headers_row

                if imdTone > 1:
                    measuredIPn.iipn, measuredIPn.oipn = intercept_point(
                        measuredIPn.best_fit, tone_best_fit
                    )

                column = chr(worksheet.current_column - 1 + ord("A"))
                headers_column = chr(worksheet.headers_column + ord("A"))
                startRow = worksheet.headers_row + 2
                chart.add_series(
                    {
                        "name": f"{toneName} - Best Fit",
                        "categories": f"='{worksheet.name}'"
                        f"!${headers_column}${startRow}:"
                        f"${headers_column}{worksheet.max_row + 1}",
                        "values": f"='{worksheet.name}'!${column}${startRow}:"
                        f"${column}{worksheet.max_row + 1}",
                        "line": {"dash_type": "round_dot"},
                    }
                )

            freqResults[imdTone] = measuredIPn
        results[freq] = freqResults

        worksheet.merge_range(
            worksheet.headers_row - 1,
            1,
            worksheet.headers_row - 1,
            worksheet.max_column,
            "Output Power per Tone (dBm)",
            centeredFormat,
        )

        # Plot markers for each of the IPn points
        # Bearing in mind, there might not be any
        categoryString = "={"
        valueString = "={"
        maxX = upperPowerLimit
        minX = lowerPowerLimit
        # minY = Highest order IMD (as assume it'll be the lowest signal
        # level) of first data point
        minY = datapoints[0].imdPoints[max(measuredIMDTerms)]
        # maxY = 1st tone (fundamental) of final data point
        maxY = datapoints[-1].imdPoints[1]

        ipnLabels = []
        numBestFitLines = 0
        for imdTone, x in freqResults.items():
            if imdTone != 1 and x.iipn is not None:
                categoryString += f"{x.iipn},"
                valueString += f"{x.oipn},"
                ipnLabels.append(
                    {
                        "value": f"IIP{imdTone} = {round(x.iipn, 1)}dBm\n"
                        f"OIP{imdTone} = {round(x.oipn, 1)}dBm"
                    }
                )
                maxX = max(maxX, x.iipn)
                minX = min(minX, x.iipn)
                maxY = max(maxY, x.oipn)
                minY = min(minY, x.oipn)
                numBestFitLines += 1

        categoryString = categoryString[:-1] + "}"
        valueString = valueString[:-1] + "}"

        if "." in categoryString:
            # We actually have some data to plot
            chart.add_series(
                {
                    "name": "IPn",
                    "categories": categoryString,
                    "values": valueString,
                    "line": {"none": True},
                    "marker": {"type": "square", "size": 5, "fill": {"color": "red"}},
                    "data_labels": {
                        "values": True,
                        "custom": ipnLabels,
                        "position": "below",
                        "border": {"color": "red"},
                        "fill": {"color": "yellow"},
                    },
                }
            )
        ipnSeriesIndex = 2 * len(intermodTerms) + 3 + numBestFitLines
        chart.set_legend({"delete_series": [ipnSeriesIndex]})

        chart.show_hidden_data()
        chart.set_x_axis(
            {
                "name": "Tone Setpoint (dBm)",
                "min": 5 * math.floor(minX / 5),
                "max": 5 * math.ceil(1 + maxX / 5),
                "crossing": -200,
                "major_unit": 5,
                "major_gridlines": {"visible": True},
            }
        )

        chart.set_y_axis(
            {
                "name": "Power per Tone (dBm)",
                "crossing": -200,
                "min": 5 * math.floor(minY / 5 - 1),
                "max": 5 * math.ceil(1 + maxY / 5),
                "major_unit": 10,
                "minor_unit": 5,
                "major_gridlines": {"visible": True},
                "minor_gridlines": {"visible": True},
            }
        )

    # # We now have all the data plotted so add a final sheet
    # # with the overall results
    overallWorksheet.new_column()
    overallWorksheet.write_and_move_down("Frequency (MHz)")
    for freq in results:
        overallWorksheet.write_and_move_down(freq / 1e6)
    overallWorksheet.new_column()
    worksheet = overallWorksheet
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
    for imd in intermodTerms:
        worksheet.write_and_move_down(f"IIP{imd} (dBm)")
        gotResults = False
        for freq in results:
            try:
                x = results[freq][imd].iipn
                worksheet.write_and_move_down(round(x, 2) if x else "")
                gotResults = True
            except KeyError:
                worksheet.write_and_move_down("")
        if gotResults:
            column = chr(worksheet.current_column + ord("A"))
            headers_column = chr(worksheet.headers_column + ord("A"))
            startRow = worksheet.headers_row + 2
            chart.add_series(
                {
                    "name": f"IIP{imd}",
                    "categories": f"='{worksheet.name}'!${headers_column}${startRow}:"
                    f"${headers_column}{worksheet.max_row + 1}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
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
        startRow = worksheet.headers_row + 2
        chart.add_series(
            {
                "name": f"OIP{imd}",
                "categories": f"='{worksheet.name}'!${headers_column}${startRow}:"
                f"${headers_column}{worksheet.max_row + 1}",
                "values": f"='{worksheet.name}'!${column}${startRow}:"
                f"${column}{worksheet.max_row + 1}",
                "line": {"dash_type": "round_dot"},
            }
        )
        worksheet.new_column()

    if not excelWorkbook:
        workbook.close()
