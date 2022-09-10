import logging
import pickle
from datetime import datetime
from math import log10
from time import sleep
from typing import Optional

from AutomatedTesting.Instruments.NoiseSource.NoiseSource import NoiseSource
from AutomatedTesting.Instruments.PSU.PSU import PowerSupplyChannel
from AutomatedTesting.Instruments.SpectrumAnalyser.Agilent_E4407B import Agilent_E4407B
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    DetectorMode,
    SpectrumAnalyser,
)
from AutomatedTesting.Instruments.TopLevel.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq
from numpy import linspace
from xlsxwriter import Workbook


def run_noise_figure_test(
    minFreq: int,
    maxFreq: int,
    spectrumAnalyser: SpectrumAnalyser,
    psu: PowerSupplyChannel,
    noiseSource: NoiseSource,
    numFreqPoints: int = 401,
    calRefLevel: int = -90,
    caldBPerDiv: int = 5,
    dutRefLevel: int = -80,
    dutdBPerDiv: int = 5,
    numAverages: int = 10,
    t0=290,
    resultsDirectory: str = "/mnt/Transit",
    pickleFile: Optional[str] = None,
):
    if not pickleFile:
        freqs = linspace(minFreq, maxFreq, numFreqPoints)

        # Ensure PSU output is off
        psu.disable_output()
        psu.set_current(2 * noiseSource.onCurrent)
        psu.set_voltage(noiseSource.onVoltage)

        # Setup spectrum analyser
        spectrumAnalyser.set_start_freq(minFreq)
        spectrumAnalyser.set_stop_freq(maxFreq)
        spectrumAnalyser.set_sweep_points(numFreqPoints)
        spectrumAnalyser.set_detector_mode(DetectorMode.RMS)
        spectrumAnalyser.set_rbw(30e3)
        spectrumAnalyser.set_vbw_rbw_ratio(0.1)
        if spectrumAnalyser.read_sweep_time() < 5000:
            spectrumAnalyser.set_sweep_time(5000)
        sleep(3)
        spectrumAnalyser.set_ref_level(0)
        spectrumAnalyser.set_ampl_scale(5)
        spectrumAnalyser.set_input_attenuator(0)
        if spectrumAnalyser.hasPreamp:
            spectrumAnalyser.enable_preamp()
        spectrumAnalyser.enable_averaging(numAverages)

        freqs = linspace(minFreq, maxFreq, numFreqPoints)

        # Get calibration trace
        input(
            f"Connect {noiseSource.name} directly to spectrum analyser input and press enter"
        )

        # Measure noise of spectrum analyser
        spectrumAnalyser.set_ref_level(calRefLevel)
        spectrumAnalyser.set_ampl_scale(caldBPerDiv)
        spectrumAnalyser.disable_averaging()
        spectrumAnalyser.enable_averaging(numAverages)
        for i in range(numAverages - 1):
            logging.debug(i)
            spectrumAnalyser.trigger_measurement()
        saOffList = spectrumAnalyser.get_trace_data()
        psu.enable_output()
        sleep(2)
        spectrumAnalyser.disable_averaging()
        spectrumAnalyser.enable_averaging(numAverages)
        for i in range(numAverages - 1):
            logging.debug(i)
            spectrumAnalyser.trigger_measurement()
        saOnList = spectrumAnalyser.get_trace_data()
        psu.disable_output()
        sleep(2)
        spectrumAnalyser.set_ref_level(dutRefLevel)
        spectrumAnalyser.set_ampl_scale(dutdBPerDiv)

        # Measure with DUT
        input(
            f"Connect DUT between {noiseSource.name} and the spectrum analyser input and press enter"
        )

        # Measure combined noise of spectrum analyser + DUT
        spectrumAnalyser.disable_averaging()
        spectrumAnalyser.enable_averaging(numAverages)
        for i in range(numAverages - 1):
            logging.debug(i)
            spectrumAnalyser.trigger_measurement()
        combinedOffList = spectrumAnalyser.get_trace_data()
        psu.enable_output()
        sleep(2)
        spectrumAnalyser.disable_averaging()
        spectrumAnalyser.enable_averaging(numAverages)
        for i in range(numAverages - 1):
            logging.debug(i)
            spectrumAnalyser.trigger_measurement()
        combinedOnList = spectrumAnalyser.get_trace_data()
        psu.disable_output()
        sleep(2)

        saNoiseFigures = []
        noiseFigures = []
        gains = []
        warnings = []

        for (freq, saOff, saOn, combinedOff, combinedOn) in zip(
            freqs, saOffList, saOnList, combinedOffList, combinedOnList
        ):
            enr = noiseSource.evaluate_enr(freq)
            sourceNoiseTemp = t0 * (1 + pow(10, enr / 10))
            warning = False

            # Calculate DUT Gain
            saOffWatts = pow(10, saOff / 10)
            saOnWatts = pow(10, saOn / 10)
            dutOffWatts = pow(10, combinedOff / 10)
            dutOnWatts = pow(10, combinedOn / 10)

            if (saOff > saOn) or (combinedOff > combinedOn):
                logging.warning(
                    f"Output power with Noise Source off was greater than with Noise Source on at {readable_freq(freq)}. Ignoring datapoint"
                )
                dutGainDb = None
                dutNoiseFigure = None
            else:
                dutGainLinear = (dutOnWatts - dutOffWatts) / (saOnWatts - saOffWatts)
                dutGainDb = 10 * log10(dutGainLinear)

                # Calculate Spectrum Analyser noise figure
                saYFactor = saOnWatts / saOffWatts
                saNoiseTemperature = (sourceNoiseTemp - saYFactor * t0) / (
                    saYFactor - 1
                )
                saNoiseFigure = enr - 10 * log10(saYFactor - 1)

                # Calculate DUT + SA noise temperature
                combinedYFactor = dutOnWatts / dutOffWatts
                combinedNoiseTemp = (sourceNoiseTemp - combinedYFactor * t0) / (
                    combinedYFactor - 1
                )
                # combinedNoiseFigure = 10 * log10(1 + combinedNoiseTemp / t0)

                # Calculate DUT Noise Figure
                dutNoiseTemp = combinedNoiseTemp - saNoiseTemperature / dutGainLinear
                if dutNoiseTemp < 0:
                    logging.warning(
                        f"Combined NF of DUT and {spectrumAnalyser.name} less than NF of {spectrumAnalyser.name}. Ignoring datapoint"
                    )
                    dutNoiseFigure = None
                else:
                    dutNoiseFigure = 10 * log10(1 + dutNoiseTemp / t0)

                    # Check SA noise figure is good enough for valid measurement
                    if enr < (saNoiseFigure + 3):
                        logging.warning(
                            f"Measurement at {readable_freq(freq)} may be invalid due to "
                            f"insufficiently low NF of {spectrumAnalyser.name}"
                        )
                        warning = True

                    # Check ENR is high enough for valid measurement
                    if enr < (dutNoiseFigure + 5):
                        logging.warning(
                            f"Measurement at {readable_freq(freq)} may be invalid due to "
                            f"insufficiently high ENR of {noiseSource.name}"
                        )
                        warning = True

                    # Check delta between calibration and measurement step are close enough to be valid
                    if (saNoiseFigure + 1) > (dutNoiseFigure + dutGainDb):
                        logging.warning(
                            f"Measurement at {readable_freq(freq)} may be invalid due to "
                            f"excess noise figure being too close to calibration"
                        )
                        warning = True

            gains.append(dutGainDb)
            saNoiseFigures.append(saNoiseFigure)
            noiseFigures.append(dutNoiseFigure)
            warnings.append(warning)

        # Save results
        with open("noiseFigure.P", "wb") as pickleFile:
            pickle.dump(
                (freqs, saNoiseFigures, noiseFigures, gains, warnings), pickleFile
            )

    else:
        # Load results from file
        with open(pickleFile, "rb") as savedData:
            freqs, saNoiseFigures, noiseFigures, gains, warnings = pickle.load(
                savedData
            )

    ###################
    # Process results #
    ###################

    now = datetime.now().strftime("%Y%m%d-%H%M%S")

    with Workbook(f"{resultsDirectory}/NoiseFigure_{now}.xlsx") as workbook:
        worksheet = workbook.add_worksheet("Noise Figure")
        worksheet.__class__ = ExcelWorksheetWrapper
        worksheet.initialise("Noise Figure")

        worksheet.write_and_move_right("Frequency (MHz)")
        worksheet.write_and_move_right("Spectrum Analyser Noise Figure (dB)")
        worksheet.write_and_move_right("Gain (dB)")
        worksheet.write_and_move_right("Noise Figure (dB)")
        worksheet.write_and_move_right("Warnings on measurement?")
        worksheet.new_row()
        worksheet.headersColumn = "A"

        for f, g, saNf, nf, w in zip(
            freqs, gains, saNoiseFigures, noiseFigures, warnings
        ):
            worksheet.write_and_move_right(f / 1e6)
            worksheet.write_and_move_right(saNf)
            worksheet.write_and_move_right(g)
            worksheet.write_and_move_right(nf)
            worksheet.write_and_move_right("Y" if w else "")
            worksheet.new_row()

        # Plot Noise Figure
        worksheet.currentColumn = 3
        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        worksheet.chart = chart
        chart.set_title({"name": "Noise Figure"})
        chart.set_size({"x_scale": 2, "y_scale": 2})
        chart.set_x_axis(
            {
                "name": "Frequency (MHz)",
                "crossing": -200,
                "major_gridlines": {"visible": True},
            }
        )
        chart.set_y_axis(
            {
                "name": "Noise Figure (dB)",
                "crossing": -200,
                "major_gridlines": {"visible": True},
            }
        )
        chart.set_legend({"none": True})

        worksheet.insert_chart(0, worksheet.maxColumn + 2, chart)
        worksheet.plot_current_column()

        # Plot Gain
        worksheet.currentColumn = 2
        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        worksheet.chart = chart
        chart.set_title({"name": f"Gain"})
        chart.set_size({"x_scale": 2, "y_scale": 2})
        chart.set_x_axis(
            {
                "name": "Frequency (MHz)",
                "crossing": -200,
                "major_gridlines": {"visible": True},
            }
        )
        chart.set_y_axis(
            {
                "name": "Gain (dB)",
                "crossing": -200,
                "major_gridlines": {"visible": True},
            }
        )
        chart.set_legend({"none": True})

        worksheet.insert_chart(30, worksheet.maxColumn + 2, chart)
        worksheet.plot_current_column()
