import logging
from AutomatedTesting.SignalGenerator.SignalGenerator import SignalGenerator, SignalGeneratorChannel
from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser
from AutomatedTesting.TestDefinitions.TestSupervisor import TestSupervisor
from AutomatedTesting.TopLevel.config import sdg2122x, e4407b
import argparse
from typing import List, Tuple
from copy import copy
import numpy


def main(
    freqList: List[int],
    toneSpacing: int,
    spectrumAnalyser: SpectrumAnalyser,
    signalGenerator: SignalGenerator,
    signalGeneratorChannels: List[int],
    lowerPowerLimit: float,
    upperPowerLimit: float,
    refLevel: float,
    measureIMD3: bool = True,
    measureIMD5: bool = False,
    measureIMD7: bool = False
):
    assert len(signalGeneratorChannels) == 2, \
        "Exactly 2 channel numbers must be specified"
    sa = spectrumAnalyser
    with TestSupervisor(
        loggingLevel=logging.INFO,
        instruments=[sa, signalGenerator],
        calibrationPower=0,
        saveResults=False
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
        sa.set_ref_level(refLevel)
        sa.set_rbw(1000)

        # Sanity check measurement
        assert measureIMD3 or measureIMD5 or measureIMD7, \
            "No Measurement Requested"

        # Setup Headings
        print(
            "Power per Tone Setpoint(dBm),Tone-Upper (dBm),Tone-Lower (dBm),",
            end=''
        )
        if measureIMD3:
            print("IMD3-Upper (dBm),IMD3-Lower (dBm),", end='')
            sa.set_span(4 * toneSpacing)
        if measureIMD5:
            print("IMD5-Upper (dBm),IMD5-Lower (dBm),", end='')
            sa.set_span(6 * toneSpacing)
        if measureIMD7:
            print("IMD7-Upper (dBm),IMD7-Lower (dBm),", end='')
            sa.set_span(8 * toneSpacing)
        print("")

        for freq in freqList:
            channel1.disable_output()
            channel2.disable_output()

            f1 = freq - 0.5 * toneSpacing
            f2 = freq + 0.5 * toneSpacing
            channel1.set_power(lowerPowerLimit)
            channel1.set_freq(f1)
            channel2.set_power(lowerPowerLimit)
            channel2.set_freq(f2)

            sa.set_centre_freq(freq)

            # Get Noise Floor with no tones
            # This allows for faster sweeping by ignoring points
            # with negligible IMD
            sa.trigger_measurement()
            noiseFloor = sa.measure_power_marker(f1)

            channel1.enable_output()
            channel2.enable_output()

            power = lowerPowerLimit
            while(power <= upperPowerLimit):
                channel1.set_power(power + 3.3)
                channel2.set_power(power + 3.3)
                sa.trigger_measurement()
                print(f"{power},", end='')
                print(f"{sa.measure_power_marker(f2)},", end='')
                print(f"{sa.measure_power_marker(f1)},", end='')
                if measureIMD3:
                    print(f"{sa.measure_power_marker(2*f2 - f1)},", end='')
                    print(f"{sa.measure_power_marker(2*f1 - f2)},", end='')
                if measureIMD5:
                    print(f"{sa.measure_power_marker(3*f2 - 2*f1)},", end='')
                    print(f"{sa.measure_power_marker(3*f1 - 2*f2)},", end='')
                if measureIMD7:
                    print(f"{sa.measure_power_marker(4*f2 - 3*f1)},", end='')
                    print(f"{sa.measure_power_marker(4*f1 - 3*f2)},", end='')
                print("")

                # Go in 5dB steps if negligible IMD, in 1dB steps if significant
                if sa.measure_power_marker(2*f2 - f1) - noiseFloor < 5:
                    power += 5
                else:
                    power += 1


def best_fit_imd_line(
    xValues: List[float],
    yValues: List[float],
    expectedGradient: float = 3
) -> Tuple[float, float]:
    """
    Takes a list of y and x values, finds best fit line by
    removing smallest x values until gradient is close to expected
    Remove smallest for IMD as likely limited by noise
    """
    x = copy(xValues)
    y = copy(yValues)
    while x:
        gradient, intercept = best_fit_line(x, y)
        if 0.985 * expectedGradient <= gradient <= 1.015 * expectedGradient:
            print(gradient, intercept)
            return gradient, intercept
        x = x[1:]
        y = y[1:]

    raise Exception("Failed to fit IMD datapoints")


def best_fit_fundamental_line(
    xValues: List[float],
    yValues: List[float],
) -> Tuple[float, float]:
    """
    Takes a list of y and x values, finds best fit line by
    removing largest x values until gradient is close to expected
    Remove largest for fundamental is to remove any terms where the DUT
    is in compression
    """
    x = copy(xValues)
    y = copy(yValues)
    while x:
        gradient, intercept = best_fit_line(x, y)
        if 0.985 <= gradient <= 1.015:
            print(gradient, intercept)
            return gradient, intercept
        x = x[:-1]
        y = y[:-1]

    raise Exception("Failed to fit datapoints to line with gradient of 1")


def best_fit_line(
    xValues: List[float],
    yValues: List[float],
) -> Tuple[float, float]:
    assert len(xValues) == len(yValues)
    x = numpy.array(xValues)
    y = numpy.array(yValues)
    gradient, intercept = numpy.polyfit(x, y, 1)
    return gradient, intercept  


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--freqs",
        nargs="*",
        type=int
    )
    parser.add_argument(
        "--toneSpacing",
        type=int,
        default=0
    )

    args = parser.parse_args()
    assert args.freqs is not None
    assert args.toneSpacing != 0

    xValues = [-40, -35, -30, -25, -20, -19, -18, -17, -16, -15, -14, -13, -12, -11]
    fundamentalValues = [-17.842, -12.887, -7.897, -2.885, 2.056, 2.938, 3.934, 4.91, 5.874, 6.854, 7.809, 8.724, 9.62, 10.503]
    imdValues = [-64.15, -64.163, -65.031, -64.165, -54.828, -50.97, -48.366, -45.523, -42.122, -39.074, -35.536, -31.929, -27.112, -19.61]

    #best_fit_fundamental_line(xValues, fundamentalValues)

    best_fit_imd_line(xValues, imdValues)

    """
    main(
        freqList=[x * 1e6 for x in args.freqs],
        toneSpacing=args.toneSpacing * 1e6,
        spectrumAnalyser=e4407b,
        signalGenerator=sdg2122x,
        signalGeneratorChannels=[1, 2],
        lowerPowerLimit=-40,
        upperPowerLimit=-10,
        refLevel=25
    )
    """
