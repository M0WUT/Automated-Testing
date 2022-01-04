import argparse
import enum
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
    upperTone: float
    lowerTone: float
    # Save all IMD tone power in dictionary
    # Key is the IMDn product with 0.1 added to indicate the upper tone
    # i.e. the value at index '3' corresponds to IMD3 (lower tone)
    # the value at index 5.1 corresponds to IMD5 (upper tone)
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


@dataclass
class SingleFreqResults:
    ipn: "dict[int, SingleFreqSingleIMDPoint]"


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
    results: "dict[float, SingleFreqResults]"
    worksheet: ExcelWorksheetWrapper

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
                    resolutionBandWidth if resolutionBandWidth is not None else 1000
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
                spectrumAnalyser.set_span(toneSpacing * (max(intermodTerms) + 1))
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

                    newDatapoint = IMDMeasurementPoint(
                        toneSetpoint=power,
                        upperTone=measure_power(f2),
                        lowerTone=measure_power(f1),
                    )

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

    # Have to rediscover details about the sweep as we may have loaded the results
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

        datapoints = imdSweeps[freq]

        # @ TODO Add equipment information

        # Add section headings
        worksheet.new_row()
        worksheet.new_row()
        worksheet.save_headers_row()
        # Leave left column blank for the chart
        worksheet.currentColumn += 1

        # Attempt to linearise all of the curves and add headings for measurements
        # and best fit lines (if we could find one)

        # Ensure datapoints are sorted in increasing tone power
        datapoints.sort(key=lambda x: x.toneSetpoint)

        # Write setpoint
        worksheet.write_and_move_down("Tone Setpoint")
        for x in datapoints:
            worksheet.write_and_move_down(x.toneSetpoint)
        worksheet.new_column()
        worksheet.currentRow = worksheet.headersRow

        # Write test tones

        # Sanity check test tones are very close in value
        for upper, lower in [(x.upperTone, x.lowerTone) for x in datapoints]:
            if abs(upper - lower) > 0.1:
                logging.warning("IMD test tones are different by >0.1dB")

        worksheet.write_and_move_down("Tone - Upper")
        for x in datapoints:
            worksheet.write_and_move_down(x.upperTone)
        worksheet.new_column()
        worksheet.currentRow = worksheet.headersRow

        toneBestFit = best_fit_line_with_known_gradient(
            [x.toneSetpoint for x in datapoints], [x.upperTone for x in datapoints], 1
        )

        if toneBestFit:
            worksheet.hide_current_column()
            toneBestFitColumn = worksheet.currentColumn
            worksheet.write_and_move_down("Tone - Upper (Best Fit)")
            for x in datapoints:
                worksheet.write_and_move_down(toneBestFit.evaluate(x.toneSetpoint))
            worksheet.new_column()
            worksheet.currentRow = worksheet.headersRow

        else:
            logging.critical("Upper test tone isn't linear")

        worksheet.write_and_move_down("Tone - Lower")
        for x in datapoints:
            worksheet.write_and_move_down(x.lowerTone)
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
            worksheet.write_and_move_down(f"IMD{imdTone} - Upper")
            for x in datapoints:
                worksheet.write_and_move_down(x.imdPoints[imdTone + 0.1])
            worksheet.new_column()
            worksheet.currentRow = worksheet.headersRow

            # Upper tone - best fit
            measuredIPn.upperBestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.imdPoints[imdTone + 0.1] for x in datapoints],
                expectedGradient=imdTone,
            )

            if measuredIPn.upperBestFit:
                worksheet.hide_current_column()
                worksheet.write_and_move_down(f"IMD{imdTone} - Upper (Best Fit)")
                for x in datapoints:
                    worksheet.write_and_move_down(
                        measuredIPn.upperBestFit.evaluate(x.toneSetpoint)
                    )
                worksheet.new_column()
                worksheet.currentRow = worksheet.headersRow

            # Lower tone
            worksheet.write_and_move_down(f"IMD{imdTone} - Lower")
            for x in datapoints:
                worksheet.write_and_move_down(x.imdPoints[imdTone])
            worksheet.new_column()
            worksheet.currentRow = worksheet.headersRow

            # Lower tone - best fit
            measuredIPn.lowerBestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.imdPoints[imdTone] for x in datapoints],
                expectedGradient=imdTone,
            )

            print([x.toneSetpoint for x in datapoints])
            print([x.imdPoints[imdTone] for x in datapoints])
            print(f"{imdTone=}")
            print(f"{measuredIPn.upperBestFit=}")
            print(f"{measuredIPn.lowerBestFit=}")

            if measuredIPn.lowerBestFit:
                worksheet.hide_current_column()
                worksheet.write_and_move_down(f"IMD{imdTone} - Lower (Best Fit)")
                for x in datapoints:
                    worksheet.write_and_move_down(
                        measuredIPn.lowerBestFit.evaluate(x.toneSetpoint)
                    )
                worksheet.new_column()
                worksheet.currentRow = worksheet.headersRow

            # Select which best fit line is being used to calculate intercept
            # point
            if measuredIPn.upperBestFit and measuredIPn.lowerBestFit:
                # we got best fit lines for both
                _, upperIPn = intercept_point(toneBestFit, measuredIPn.upperBestFit)
                _, lowerIPn = intercept_point(toneBestFit, measuredIPn.lowerBestFit)
                # Work out which has worse IPn as that is what we'll quote
                # as the result
                if lowerIPn < upperIPn:
                    measuredIPn.finalBestFit = measuredIPn.lowerBestFit
                else:
                    measuredIPn.finalBestFit = measuredIPn.upperBestFit
            elif measuredIPn.upperBestFit:
                measuredIPn.finalBestFit = measuredIPn.upperBestFit
            elif measuredIPn.lowerBestFit:
                measuredIPn.finalBestFit = measuredIPn.lowerBestFit

            # Calculate Intercept points
            if measuredIPn.finalBestFit:
                measuredIPn.iipn, measuredIPn.oipn = intercept_point(
                    measuredIPn.finalBestFit, toneBestFit
                )

        workbook.close()  # @DEBUG
        return

        # IMD3
        if measuredIMD3:
            worksheet.write_and_move_right("IMD3 - Upper")
            upperIMD3BestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.upperIMD3 for x in datapoints],
                3,
            )
            if upperIMD3BestFit:
                worksheet.hide_current_column()
                IMD3BestFitColumn = worksheet.currentColumn
                IIP3, OIP3 = intercept_point(upperToneBestFit, upperIMD3BestFit)
                worksheet.write_and_move_right("IMD3 - Upper (Best Fit)")

            worksheet.write_and_move_right("IMD3 - Lower")
            lowerIMD3BestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.lowerIMD3 for x in datapoints],
                3,
            )
            if lowerIMD3BestFit:
                worksheet.hide_current_column()
                if IMD3BestFitColumn:
                    # Both best fit lines look valid
                    _, upperIP3 = intercept_point(upperToneBestFit, upperIMD3BestFit)
                    _, lowerIP3 = intercept_point(upperToneBestFit, lowerIMD3BestFit)
                    # If IP3 with this best fit is worse than with the upper trace
                    # then overwrite with the worse value (be a pessimist)
                    if lowerIP3 < upperIP3:
                        IIP3, OIP3 = intercept_point(upperToneBestFit, lowerIMD3BestFit)
                        IMD3BestFitColumn = worksheet.currentColumn
                else:
                    IMD3BestFitColumn = worksheet.currentColumn
                    IIP3, OIP3 = intercept_point(upperToneBestFit, lowerIMD3BestFit)
                worksheet.write_and_move_right("IMD3 - Lower (Best Fit)")

        # IMD5
        if measuredIMD5:
            worksheet.write_and_move_right("IMD5 - Upper")
            upperIMD5BestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.upperIMD5 for x in datapoints],
                5,
            )
            if upperIMD5BestFit:
                worksheet.hide_current_column()
                IMD5BestFitColumn = worksheet.currentColumn
                IIP5, OIP5 = intercept_point(upperToneBestFit, upperIMD5BestFit)
                worksheet.write_and_move_right("IMD5 - Upper (Best Fit)")

            worksheet.write_and_move_right("IMD5 - Lower")
            lowerIMD5BestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.lowerIMD5 for x in datapoints],
                5,
            )
            if lowerIMD5BestFit:
                worksheet.hide_current_column()
                if upperIMD5BestFit:
                    # Both best fit lines look valid
                    _, upperIP5 = intercept_point(upperToneBestFit, upperIMD5BestFit)
                    _, lowerIP5 = intercept_point(upperToneBestFit, lowerIMD5BestFit)
                    # If IP3 with this best fit is worse than with the upper trace
                    # then overwrite with the worse value (be a pessimist)
                    if lowerIP5 < upperIP5:
                        IMD5BestFitColumn = worksheet.currentColumn
                        IIP5, OIP5 = intercept_point(upperToneBestFit, lowerIMD5BestFit)
                else:
                    IMD5BestFitColumn = worksheet.currentColumn
                    IIP5, OIP5 = intercept_point(upperToneBestFit, lowerIMD5BestFit)
                worksheet.write_and_move_right("IMD5 - Lower (Best Fit)")

        # IMD7
        if measuredIMD7:
            worksheet.write_and_move_right("IMD7 - Upper")
            upperIMD7BestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.upperIMD7 for x in datapoints],
                7,
            )
            if upperIMD7BestFit:
                worksheet.hide_current_column()
                IMD7BestFitColumn = worksheet.currentColumn
                IIP7, OIP7 = intercept_point(upperToneBestFit, upperIMD7BestFit)
                worksheet.write_and_move_right("IMD7 - Upper (Best Fit)")

            worksheet.write_and_move_right("IMD7 - Lower")
            lowerIMD7BestFit = best_fit_line_with_known_gradient(
                [x.toneSetpoint for x in datapoints],
                [x.lowerIMD7 for x in datapoints],
                7,
            )
            if lowerIMD7BestFit:
                worksheet.hide_current_column()
                if upperIMD7BestFit:
                    # Both best fit lines look valid
                    _, upperIP7 = intercept_point(upperToneBestFit, upperIMD7BestFit)
                    _, lowerIP7 = intercept_point(upperToneBestFit, lowerIMD7BestFit)
                    # If IP3 with this best fit is worse than with the upper trace
                    # then overwrite with the worse value (be a pessimist)
                    if lowerIP7 < upperIP7:
                        IMD7BestFitColumn = worksheet.currentColumn
                        IIP7, OIP7 = intercept_point(upperToneBestFit, lowerIMD7BestFit)
                else:
                    IMD7BestFitColumn = worksheet.currentColumn
                    IIP7, OIP7 = intercept_point(upperToneBestFit, lowerIMD7BestFit)
                worksheet.write_and_move_right("IMD7 - Lower (Best Fit)")

        # Sort datapoints by increasing setpoint (just in case they're not
        # already sorted)

        worksheet.new_row()
        worksheet.currentColumn += 1

        # Write out all the data
        for x in datapoints:
            worksheet.write_and_move_right(x.toneSetpoint)
            worksheet.write_and_move_right(x.upperTone)
            worksheet.write_and_move_right(upperToneBestFit.evaluate(x.toneSetpoint))
            worksheet.write_and_move_right(x.lowerTone)

            # IMD3
            if measuredIMD3:
                worksheet.write_and_move_right(x.upperIMD3)
                if upperIMD3BestFit:
                    worksheet.write_and_move_right(
                        upperIMD3BestFit.evaluate(x.toneSetpoint)
                    )
                worksheet.write_and_move_right(x.lowerIMD3)

                if lowerIMD3BestFit:
                    worksheet.write_and_move_right(
                        lowerIMD3BestFit.evaluate(x.toneSetpoint)
                    )

            # IMD5
            if measuredIMD5:
                worksheet.write_and_move_right(x.upperIMD5)
                if upperIMD5BestFit:
                    worksheet.write_and_move_right(
                        upperIMD5BestFit.evaluate(x.toneSetpoint)
                    )
                worksheet.write_and_move_right(x.lowerIMD5)

                if lowerIMD5BestFit:
                    worksheet.write_and_move_right(
                        lowerIMD5BestFit.evaluate(x.toneSetpoint)
                    )

            # IMD7
            if measuredIMD7:
                worksheet.write_and_move_right(x.upperIMD7)
                if upperIMD7BestFit:
                    worksheet.write_and_move_right(
                        upperIMD7BestFit.evaluate(x.toneSetpoint)
                    )

                worksheet.write_and_move_right(x.lowerIMD7)
                if lowerIMD7BestFit:
                    worksheet.write_and_move_right(
                        lowerIMD7BestFit.evaluate(x.toneSetpoint)
                    )

            worksheet.new_row()
            worksheet.currentColumn += 1

        # Add extra datapoint at very high power for best fit lines
        finalDatapoint = 100
        worksheet.hide_current_row()
        worksheet.write_and_move_right(finalDatapoint)
        worksheet.currentColumn += 1  # Skip Upper Tone measurement
        worksheet.write_and_move_right(upperToneBestFit.evaluate(finalDatapoint))
        worksheet.currentColumn += 1  # Skip Lower Tone measurement
        if measuredIMD3:
            worksheet.currentColumn += 1  # Skip Upper IMD3
            if upperIMD3BestFit:
                worksheet.write_and_move_right(
                    upperIMD3BestFit.evaluate(finalDatapoint)
                )
            worksheet.currentColumn += 1  # Skip Lower IMD3
            if lowerIMD3BestFit:
                worksheet.write_and_move_right(
                    lowerIMD3BestFit.evaluate(finalDatapoint)
                )

        if measuredIMD5:
            worksheet.currentColumn += 1  # Skip Upper IMD5
            if upperIMD5BestFit:
                worksheet.write_and_move_right(
                    upperIMD5BestFit.evaluate(finalDatapoint)
                )
            worksheet.currentColumn += 1  # Skip Lower IMD5
            if lowerIMD5BestFit:
                worksheet.write_and_move_right(
                    lowerIMD5BestFit.evaluate(finalDatapoint)
                )

        if measuredIMD7:
            worksheet.currentColumn += 1  # Skip Upper IMD7
            if upperIMD7BestFit:
                worksheet.write_and_move_right(
                    upperIMD7BestFit.evaluate(finalDatapoint)
                )
            worksheet.currentColumn += 1  # Skip Lower IMD7
            if lowerIMD7BestFit:
                worksheet.write_and_move_right(
                    lowerIMD7BestFit.evaluate(finalDatapoint)
                )

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
        chart.set_title({"name": f"IMD - {readable_freq(freq)}"})
        chart.set_size({"x_scale": 2, "y_scale": 2})

        for x in range(2, worksheet.maxColumn + 1):
            if x not in worksheet.hiddenColumns:
                column = chr(x + ord("A"))
                # +1 for data being one row lower, +1 for stupid 0/1 indexing
                startRow = worksheet.headersRow + 2
                chart.add_series(
                    {
                        "name": f"='{worksheet.name}'!${column}${worksheet.headersRow + 1}",
                        "categories": f"='{worksheet.name}'!$B${startRow}:"
                        f"$B{ startRow + len(datapoints) - 1}",
                        "values": f"='{worksheet.name}'!${column}${startRow}:"
                        f"${column}{startRow + len(datapoints) - 1}",
                    }
                )

        # Add linear interpolation to IPn
        if toneBestFitColumn:
            column = chr(toneBestFitColumn + ord("A"))
            chart.add_series(
                {
                    "name": "Tone - Best Fit",
                    "categories": f"='{worksheet.name}'!$B${startRow}:"
                    f"$B{startRow + len(datapoints)}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{startRow + len(datapoints)}",
                    "line": {"dash_type": "round_dot"},
                }
            )

        if IMD3BestFitColumn:
            column = chr(IMD3BestFitColumn + ord("A"))
            chart.add_series(
                {
                    "name": "IMD3 - Best Fit",
                    "categories": f"='{worksheet.name}'!$B${startRow}:"
                    f"$B{startRow + len(datapoints)}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{startRow + len(datapoints)}",
                    "line": {"dash_type": "round_dot"},
                }
            )

        if IMD5BestFitColumn:
            column = chr(IMD5BestFitColumn + ord("A"))
            chart.add_series(
                {
                    "name": "IMD5 - Best Fit",
                    "categories": f"='{worksheet.name}'!$B${startRow}:"
                    f"$B{startRow + len(datapoints)}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{startRow + len(datapoints)}",
                    "line": {"dash_type": "round_dot"},
                }
            )
        if IMD7BestFitColumn:
            column = chr(IMD7BestFitColumn + ord("A"))
            chart.add_series(
                {
                    "name": "IMD7 - Best Fit",
                    "categories": f"='{worksheet.name}'!$B${startRow}:"
                    f"$B{startRow + len(datapoints) - 1}",
                    "values": f"='{worksheet.name}'!${column}${startRow}:"
                    f"${column}{startRow + len(datapoints)}",
                    "line": {"dash_type": "round_dot"},
                }
            )

        chart.show_hidden_data()

        # Plot markers for each of the IPn points
        # Bearing in mind, there might not be any
        categoryString = "={"
        valueString = "={"

        ipnLabels = []

        if IIP3:
            categoryString += f"{IIP3},"
            valueString += f"{OIP3},"
            ipnLabels.append(
                {"value": f"IIP3 = {round(IIP3, 1)}dBm\nOIP3 = {round(OIP3, 1)}dBm"}
            )
        if IIP5:
            categoryString += f"{IIP5},"
            valueString += f"{OIP5},"
            ipnLabels.append(
                {"value": f"IIP5 = {round(IIP5, 1)}dBm\nOIP5 = {round(OIP5, 1)}dBm"}
            )
        if IIP7:
            categoryString += f"{IIP7},"
            valueString += f"{OIP7},"
            ipnLabels.append(
                {"value": f"IIP7 = {round(IIP7, 1)}dBm\nOIP3 = {round(OIP7, 1)}dBm"}
            )

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

            # Have to manually delete this series from the legend
            # Unfortunately, this wants to be the last series plotted
            # so the markers end up on top

            # Following measurements all generate 2 traces
            ipnSeriesNumber = 1
            ipnSeriesNumber += measuredIMD3 is True
            ipnSeriesNumber += measuredIMD5 is True
            ipnSeriesNumber += measuredIMD7 is True

            ipnSeriesNumber *= 2

            # Following measurements all generate 1 trace
            ipnSeriesNumber += upperToneBestFit is not None
            ipnSeriesNumber += IMD3BestFitColumn is not None
            ipnSeriesNumber += IMD5BestFitColumn is not None
            ipnSeriesNumber += IMD7BestFitColumn is not None

            chart.set_legend({"delete_series": [ipnSeriesNumber]})

        # Work out axis limits
        maxX = datapoints[-1].toneSetpoint
        if IIP3:
            maxX = max(maxX, IIP3)
        if IIP5:
            maxX = max(maxX, IIP5)
        if IIP7:
            maxX = max(maxX, IIP7)

        maxY = max(datapoints[-1].upperTone, datapoints[-1].lowerTone)
        if OIP3:
            maxY = max(maxY, OIP3)
        if OIP5:
            maxY = max(maxY, OIP5)
        if OIP7:
            maxY = max(maxY, OIP7)

        minY = float("inf")
        if datapoints[0].upperIMD3:
            minY = min(minY, datapoints[0].upperIMD3)
        if datapoints[0].upperIMD5:
            minY = min(minY, datapoints[0].upperIMD5)
        if datapoints[0].upperIMD7:
            minY = min(minY, datapoints[0].upperIMD7)

        chart.set_x_axis(
            {
                "name": "Tone Setpoint (dBm)",
                "min": 5 * math.floor(datapoints[0].toneSetpoint / 5),
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

        worksheet.insert_chart(0, 0, chart)

    # Close the workbook only if we created it,
    # otherwise something else might be expecting
    # to use it later
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
            intermodTerms=[3, 5],
            lowerPowerLimit=-40,
            upperPowerLimit=-10,
            refLevel=25,
            pickleFile="imdTest.P",
        )
    except KeyboardInterrupt:
        pass
