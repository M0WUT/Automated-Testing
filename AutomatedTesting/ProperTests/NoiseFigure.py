import logging
import pickle
import time
from datetime import datetime
from math import log10
from typing import Optional

from AutomatedTesting.Instruments.NoiseSource.NoiseSource import NoiseSource
from AutomatedTesting.Instruments.PSU.PSU import PowerSupplyChannel
from AutomatedTesting.Instruments.SpectrumAnalyser import SpectrumAnalyser
from AutomatedTesting.Instruments.SpectrumAnalyser.Agilent_E4407B import Agilent_E4407B
from AutomatedTesting.Instruments.TopLevel.ExcelHandler import ExcelWorksheetWrapper
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq
from numpy import linspace
from xlsxwriter import Workbook


def run_noise_figure_test(
    minFreq: int,
    maxFreq: int,
    spectrumAnalyser: Agilent_E4407B,
    psu: PowerSupplyChannel,
    noiseSource: NoiseSource,
    numFreqPoints: int = 401,
    t0=290,
    sweepTime: float = 10,
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
        spectrumAnalyser.set_rms_detector_mode()
        spectrumAnalyser.set_rbw(30e3)
        spectrumAnalyser.set_ref_level(-60)
        spectrumAnalyser.set_ampl_scale(5)
        spectrumAnalyser.set_input_attenuator(0)
        spectrumAnalyser.set_sweep_time(int(1000 * sweepTime))

        freqs = linspace(minFreq, maxFreq, numFreqPoints)

        # Get calibration trace
        input(
            f"Connect {noiseSource.name} directly to spectrum analyser input and press enter"
        )

        # Measure noise of spectrum analyser
        saOffList = spectrumAnalyser.get_trace_data()
        psu.enable_output()
        time.sleep(2)
        saOnList = spectrumAnalyser.get_trace_data()
        psu.disable_output()
        time.sleep(2)

        # Measure with DUT
        input(
            f"Connect DUT between {noiseSource.name} and the spectrum analyser input and press enter"
        )

        # Measure combined noise of spectrum analyser + DUT
        combinedOffList = spectrumAnalyser.get_trace_data()
        psu.enable_output()
        time.sleep(2)
        combinedOnList = spectrumAnalyser.get_trace_data()
        psu.disable_output()
        time.sleep(2)

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
            noiseFigures.append(dutNoiseFigure)
            warnings.append(warning)

        # Save results
        with open("noiseFigure.P", "wb") as pickleFile:
            pickle.dump((freqs, noiseFigures, gains, warnings), pickleFile)

    else:
        # Load results from file
        with open(pickleFile, "rb") as savedData:
            freqs, noiseFigures, gains, warnings = pickle.load(savedData)

    ###################
    # Process results #
    ###################

    now = datetime.now().strftime("%Y%m%d-%H%M%S")

    with Workbook(f"{resultsDirectory}/NoiseFigure_{now}.xlsx") as workbook:
        worksheet = workbook.add_worksheet("Noise Figure")
        worksheet.__class__ = ExcelWorksheetWrapper
        worksheet.initialise("Noise Figure")

        worksheet.write_and_move_right("Frequency (MHz)")
        worksheet.write_and_move_right("Gain (dB)")
        worksheet.write_and_move_right("Noise Figure (dB)")
        worksheet.write_and_move_right("Warnings on measurement?")
        worksheet.new_row()
        worksheet.headersColumn = "A"

        for f, g, nf, w in zip(freqs, gains, noiseFigures, warnings):
            worksheet.write_and_move_right(f / 1e6)
            worksheet.write_and_move_right(g)
            worksheet.write_and_move_right(nf)
            worksheet.write_and_move_right("Y" if w else "")
            worksheet.new_row()

        # Plot Noise Figure
        worksheet.currentColumn = 2
        chart = workbook.add_chart({"type": "scatter", "subtype": "straight"})
        worksheet.chart = chart
        chart.set_title({"name": f"Noise Figure"})
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
        worksheet.currentColumn = 1
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
