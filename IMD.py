import argparse
import logging
import math
import pickle
from dataclasses import dataclass, field
from typing import List, Union

import xlsxwriter
from AutomatedTesting.SignalGenerator.SignalGenerator import (
    SignalGenerator, SignalGeneratorChannel)
from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser
from AutomatedTesting.TestDefinitions.TestSupervisor import TestSupervisor
from AutomatedTesting.TopLevel.config import e4407b, sdg2122x
from AutomatedTesting.TopLevel.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.TopLevel.UsefulFunctions import (
    StraightLine, best_fit_line_with_known_gradient, intercept_point,
    readable_freq)


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
    upperBestFit: StraightLine = None
    lowerBestFit: StraightLine = None
    # Final results are the ones use to calculate IIPn/OIPn
    # and should be equal to either upper or lower best fit
    finalBestFit: StraightLine = None
    iipn: float = None
    oipn: float = None


def main(
    freqList: List[int],
    toneSpacing: int,
    spectrumAnalyser: SpectrumAnalyser,
    signalGenerator: SignalGenerator,
    signalGeneratorChannels: List[int],
    lowerPowerLimit: float,
    upperPowerLimit: float,
    refLevel: float,
    intermodTerms: "Union[list[int], None]" = None,
    # Offset of signal generator relative to spectrum analyser
    # e.g. for 2m transverter at 144MHz with a input of 28MHz
    # this should be set to -116e6
    freqOffset: float = 0,
    resolutionBandWidth: int = None,
    useZeroSpan: bool = False,
    pickleFile: str = None,
    excelWorkbook: "Union[xlsxwriter.workbook.Workbook, None]" = None,
):

    channel1: SignalGeneratorChannel
    channel2: SignalGeneratorChannel
    datapoints: List[IMDMeasurementPoint]
    imdSweeps: "dict[float, List[IMDMeasurementPoint]]"
    results: "dict[float, dict]"
    worksheet: ExcelWorksheetWrapper

    results = {}

    if not pickleFile:
        imdSweeps = {}
        assert (
            len(signalGeneratorChannels) == 2
        ), "Exactly 2 channel numbers must be specified"

        with TestSupervisor(
            loggingLevel=logging.DEBUG,
            instruments=[spectrumAnalyser, signalGenerator],
            calibrationPower=0,
            saveResults=False,
        ) as _:
            channel1 = signalGenerator.reserve_channel(
                signalGeneratorChannels[0], "Lower IMD Tone"
            )
            channel2 = signalGenerator.reserve_channel(
                signalGeneratorChannels[1], "Upper IMD Tone"
            )
            channel1.set_power(lowerPowerLimit)
            channel2.set_power(lowerPowerLimit)

            # Setup Spectrum analyser
            spectrumAnalyser.set_ref_level(refLevel)
            if resolutionBandWidth:
                if resolutionBandWidth > toneSpacing / 200:
                    logging.warning(
                        f"Requested RBW of {resolutionBandWidth} is too large"
                        "(> Tone Spacing / 200) and may lead to inaccurate"
                        " results"
                    )
            else:
                spectrumAnalyser.set_rbw(
                    resolutionBandWidth if resolutionBandWidth else 1000
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
                # It's really important that each tone aligns perfectly with
                # a measurement points. Really suggest locking the oscillators
                # of the spectrum analyser and signal generator
                requiredSweepPoints = 100 * (maxIntermod + 1) + 1
                spectrumAnalyser.set_sweep_points(requiredSweepPoints)
                assert spectrumAnalyser.get_sweep_points() == requiredSweepPoints
                measure_power = spectrumAnalyser.measure_power_marker

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
                spectrumAnalyser.trigger_measurement()
                noiseFloor = measure_power(f1)

                channel1.enable_output()
                channel2.enable_output()

                power = lowerPowerLimit
                while power <= upperPowerLimit:
                    channel1.set_power(power + 3.3)
                    channel2.set_power(power + 3.3)
                    spectrumAnalyser.trigger_measurement()

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

                    # Go in 2dB steps if negligible IMD else go in 1dB steps
                    if measure_power(2 * f2 - f1) > noiseFloor + 3:
                        power += 1
                    else:
                        power += 2

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
    overallWorksheet.add_wrapper_attributes(name=overallResultsWorksheetName)
    overallWorksheet.set_column(first_col=0, last_col=0, width=140)
    overallWorksheet.set_column(first_col=1, last_col=200, width=18)
    overallWorksheet.headersColumn = "B"
    chart = workbook.add_chart({"type": "scatter", "subtype": "straight_with_markers"})
    overallWorksheet.chart = chart
    chart.set_title({"name": "Intermodulation Distortion"})
    chart.set_size({"x_scale": 2, "y_scale": 2})
    overallWorksheet.insert_chart(0, 0, chart)

    # Have to rediscover details about the sweep as we may have
    # loaded the results
    sweptFrequencies = list(imdSweeps.keys())
    sweptFrequencies.sort()
    for freq in sweptFrequencies:

        worksheetName = f"IMD Measurements - {readable_freq(freq)}"
        worksheet = workbook.add_worksheet(worksheetName)

        # Update worksheet to class with M0WUT wrapper
        worksheet.__class__ = ExcelWorksheetWrapper
        worksheet.add_wrapper_attributes(name=worksheetName)

        worksheet.set_column(first_col=0, last_col=0, width=140)
        worksheet.set_column(first_col=1, last_col=200, width=18)
        worksheet.headersColumn = "B"

        datapoints = imdSweeps[freq]
        freqResults = {}

        # @ TODO Add equipment information

        # Add section headings
        worksheet.new_row()
        worksheet.new_row()
        worksheet.save_headers_row()
        # Leave left column blank for the chart
        worksheet.currentColumn += 1

        # Create chart object and headings
        centeredFormat = workbook.add_format({"align": "center"})
        worksheet.merge_range(
            worksheet.headersRow - 1,
            1,
            worksheet.headersRow - 1,
            worksheet.maxColumn,
            "Power per Tone (dBm)",
            centeredFormat,
        )

        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        worksheet.chart = chart
        chart.set_title({"name": f"IMD - {readable_freq(freq)}"})
        chart.set_size({"x_scale": 2, "y_scale": 2})

        worksheet.insert_chart(0, 0, chart)

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
        worksheet.currentRow = worksheet.headersRow

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
            worksheet.currentRow = worksheet.headersRow

            # Upper tone - best fit
            measuredIPn.upperBestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.imdPoints[imdTone + 0.1] for x in datapoints],
                expectedGradient=imdTone,
            )

            if imdTone == 1:
                assert measuredIPn.upperBestFit
                toneBestFit = measuredIPn.upperBestFit

            if measuredIPn.upperBestFit:
                worksheet.hide_current_column()
                worksheet.write_and_move_down(f"{toneName} - Upper (Best Fit)")
                for x in datapoints:
                    worksheet.write_and_move_down(
                        measuredIPn.upperBestFit.evaluate(x.toneSetpoint)
                    )
                # Super high power point for trace extrapolation
                worksheet.write_and_move_down(measuredIPn.upperBestFit.evaluate(100))
                worksheet.new_column()
                worksheet.currentRow = worksheet.headersRow

            # Lower tone
            worksheet.write_and_move_down(f"{toneName} - Lower")
            for x in datapoints:
                worksheet.write_and_move_down(x.imdPoints[imdTone])
            worksheet.plot_current_column()
            worksheet.new_column()
            worksheet.currentRow = worksheet.headersRow

            # Lower tone - best fit
            measuredIPn.lowerBestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.imdPoints[imdTone] for x in datapoints],
                expectedGradient=imdTone,
            )

            if measuredIPn.lowerBestFit:
                worksheet.hide_current_column()
                worksheet.write_and_move_down(f"{toneName} - Lower (Best Fit)")
                for x in datapoints:
                    worksheet.write_and_move_down(
                        measuredIPn.lowerBestFit.evaluate(x.toneSetpoint)
                    )
                # Super high power point for trace extrapolation
                worksheet.write_and_move_down(measuredIPn.lowerBestFit.evaluate(100))
                worksheet.new_column()
                worksheet.currentRow = worksheet.headersRow

            # Select which best fit line is being used to calculate intercept
            # point
            if imdTone > 1:
                # Calculate Intercept points
                if measuredIPn.upperBestFit and measuredIPn.lowerBestFit:
                    # we got best fit lines for both
                    _, upperIPn = intercept_point(toneBestFit, measuredIPn.upperBestFit)
                    _, lowerIPn = intercept_point(toneBestFit, measuredIPn.lowerBestFit)
                    # Work out which has worse IPn as that is what we'll quote
                    # as the result
                    if lowerIPn < upperIPn:
                        measuredIPn.finalBestFit = measuredIPn.lowerBestFit
                        bestFitColumn = worksheet.currentColumn - 1
                    else:
                        measuredIPn.finalBestFit = measuredIPn.upperBestFit
                        bestFitColumn = worksheet.currentColumn - 3
                elif measuredIPn.upperBestFit:
                    measuredIPn.finalBestFit = measuredIPn.upperBestFit
                    bestFitColumn = worksheet.currentColumn - 2
                elif measuredIPn.lowerBestFit:
                    # There's a lower best fit and no upper best fit
                    measuredIPn.finalBestFit = measuredIPn.lowerBestFit
                    bestFitColumn = worksheet.currentColumn - 1
                else:
                    continue

                if measuredIPn.finalBestFit:
                    measuredIPn.iipn, measuredIPn.oipn = intercept_point(
                        measuredIPn.finalBestFit, toneBestFit
                    )
            else:
                # For the tone, always use the upper
                bestFitColumn = worksheet.currentColumn - 3
                measuredIPn.finalBestFit = measuredIPn.upperBestFit

            column = chr(bestFitColumn + ord("A"))
            startRow = worksheet.headersRow + 2
            chart.add_series(
                {
                    "name": f"{toneName} - Best Fit",
                    "categories": f"='{worksheet.name}'"
                    f"!${worksheet.headersColumn}${startRow}:"
                    f"${worksheet.headersColumn}{worksheet.maxRow + 1}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{worksheet.maxRow + 1}",
                    "line": {"dash_type": "round_dot"},
                }
            )

            freqResults[imdTone] = measuredIPn
        results[freq] = freqResults

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
                        f"OIP3 = {round(x.oipn, 1)}dBm"
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

    # We now have all the data plotted so add a final sheet
    # with the overall results
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
            column = chr(worksheet.currentColumn + ord("A"))
            startRow = worksheet.headersRow + 2
            chart.add_series(
                {
                    "name": f"IIP{imd}",
                    "categories": f"='{worksheet.name}'!${worksheet.headersColumn}${startRow}:"
                    f"${worksheet.headersColumn}{worksheet.maxRow + 1}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{worksheet.maxRow + 1}",
                    "line": {"dash_type": "round_dot"},
                }
            )

        worksheet.new_column()
        worksheet.write_and_move_down(f"OIP{imd} (dBm)")
        gotResults = False
        for freq in results:
            try:
                x = results[freq][imd].oipn
                worksheet.write_and_move_down(round(x, 2) if x else "")
                gotResults = True
            except KeyError:
                worksheet.write_and_move_down("")
        if gotResults:
            column = chr(worksheet.currentColumn + ord("A"))
            startRow = worksheet.headersRow + 2
            chart.add_series(
                {
                    "name": f"OIP{imd}",
                    "categories": f"='{worksheet.name}'!${worksheet.headersColumn}${startRow}:"
                    f"${worksheet.headersColumn}{worksheet.maxRow + 1}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{worksheet.maxRow + 1}",
                    "line": {"dash_type": "round_dot"},
                }
            )
        worksheet.new_column()

    if not excelWorkbook:
        workbook.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freqs", nargs="*", type=int)
    parser.add_argument("--toneSpacing", type=int, default=0)

    args = parser.parse_args()
    assert args.freqs is not None
    assert args.toneSpacing != 0
    try:
        main(
            freqList=[x * 1e6 for x in args.freqs],
            toneSpacing=args.toneSpacing * 1e6,
            spectrumAnalyser=e4407b,
            signalGenerator=sdg2122x,
            signalGeneratorChannels=[1, 2],
            intermodTerms=[3, 5, 7],
            lowerPowerLimit=-40,
            upperPowerLimit=-10,
            refLevel=25,
            #pickleFile="imdTest.P",
        )
    except KeyboardInterrupt:
        pass
