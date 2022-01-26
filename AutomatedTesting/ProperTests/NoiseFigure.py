import logging
import time
from math import log10

from AutomatedTesting.Instruments.NoiseSource.NoiseSource import NoiseSource
from AutomatedTesting.Instruments.PSU.PSU import PowerSupplyChannel
from AutomatedTesting.Instruments.SpectrumAnalyser import SpectrumAnalyser
from AutomatedTesting.Instruments.SpectrumAnalyser.Agilent_E4407B import Agilent_E4407B
from AutomatedTesting.Instruments.TopLevel.UsefulFunctions import readable_freq
from numpy import linspace


def run_noise_figure_test(
    minFreq: int,
    maxFreq: int,
    spectrumAnalyser: Agilent_E4407B,
    psu: PowerSupplyChannel,
    noiseSource: NoiseSource,
    numFreqPoints: int = 401,
    t0=290,
):
    freqs = linspace(minFreq, maxFreq, numFreqPoints)

    # Ensure PSU output is off
    psu.disable_output()
    psu.set_current(2 * noiseSource.onCurrent)
    psu.enable_ocp()
    psu.set_voltage(noiseSource.onVoltage)

    # Setup spectrum analyser
    spectrumAnalyser.set_start_freq(minFreq)
    spectrumAnalyser.set_stop_freq(maxFreq)
    spectrumAnalyser.set_sweep_points(numFreqPoints)
    spectrumAnalyser.set_rms_detector_mode()
    spectrumAnalyser.set_rbw(30e3)
    spectrumAnalyser.set_ref_level(-60)

    freqs = linspace(minFreq, maxFreq, numFreqPoints)

    # Get calibration trace
    input(
        f"Connect {noiseSource.name} directly to spectrum analyser input and press enter"
    )

    # Measure noise of spectrum analyser
    saOffList = spectrumAnalyser.get_trace_data()
    psu.enable_output()
    saOnList = spectrumAnalyser.get_trace_data()
    psu.disable_output()

    # Measure with DUT
    input(
        f"Connect DUT between {noiseSource.name} and the spectrum analyser input and press enter"
    )

    # Measure combined noise of spectrum analyser + DUT
    combinedOffList = spectrumAnalyser.get_trace_data()
    psu.enable_output()
    combinedOnList = spectrumAnalyser.get_trace_data()
    psu.disable_output()

    results = []

    for (freq, saOff, saOn, combinedOff, combinedOn) in zip(
        freqs, saOffList, saOnList, combinedOffList, combinedOnList
    ):
        enr = noiseSource.evaluate_enr(freq)
        sourceNoiseTemp = t0 * (1 + pow(10, enr / 10))

        # Calculate Spectrum Analyser noise figure
        saYFactor = pow(10, (saOn - saOff) / 10)
        saNoiseTemperature = (sourceNoiseTemp - saYFactor * t0) / (saYFactor - 1)
        saNoiseFigure = enr - 10 * log10(saYFactor - 1)
        print(f"{freq}, {saNoiseFigure}")

        # Check SA noise figure is good enough for valid measurement
        if enr < (saNoiseFigure + 3):
            logging.warning(
                f"Measurement at {readable_freq(freq)} may be invalid due to "
                f"insufficiently low NF of {spectrumAnalyser.name}"
            )

        # Calculate DUT + SA noise temperature
        combinedYFactor = pow(10, (combinedOn - combinedOff) / 10)
        combinedNoiseTemp = (sourceNoiseTemp - combinedYFactor * t0) / (
            combinedYFactor - 1
        )

        # Calculate DUT Gain
        saOffWatts = pow(10, saOff / 10)
        saOnWatts = pow(10, saOn / 10)
        dutOffWatts = pow(10, combinedOff / 10)
        dutOnWatts = pow(10, combinedOn / 10)

        dutGainLinear = (dutOnWatts - dutOffWatts) / (saOnWatts - saOffWatts)
        dutGainDb = 10 * log10(dutGainLinear)

        # Calculate DUT Noise Figure
        dutNoiseTemp = combinedNoiseTemp - saNoiseTemperature / dutGainLinear
        dutNoiseFigure = 10 * log10(1 + dutNoiseTemp / t0)

        # Check ENR noise figure is high enough for valid measurement
        if enr < (dutNoiseFigure + 5):
            logging.warning(
                f"Measurement at {readable_freq(freq)} may be invalid due to "
                f"insufficiently high ENR of {noiseSource.name}"
            )

        # Check delta between calibration and measurement step are close enough to be valid
        if (saNoiseFigure + 1) < (dutNoiseFigure + dutGainDb):
            logging.warning(
                f"Measurement at {readable_freq(freq)} may be invalid due to "
                f"excess noise figure being too close to calibration"
            )

        results.append((freq, dutNoiseFigure))
    # print(results)
