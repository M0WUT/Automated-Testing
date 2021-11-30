import logging
from AutomatedTesting.SignalGenerator.SignalGenerator import SignalGenerator, SignalGeneratorChannel
from AutomatedTesting.SpectrumAnalyser.SpectrumAnalyser import SpectrumAnalyser
from AutomatedTesting.TestDefinitions.TestSupervisor import TestSupervisor
from AutomatedTesting.TopLevel.config import sdg2122x, e4407b
import argparse
from typing import List


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
        loggingLevel=logging.DEBUG,
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
            f1 = freq - 0.5 * toneSpacing
            f2 = freq + 0.5 * toneSpacing
            channel1.set_freq(f1)
            channel2.set_freq(f2)

            # Get Noise Floor with no tones
            # This allows for faster sweeping by ignoring points
            # with negligible IMD
            noiseFloor = sa.measure_power_marker(f1)

            channel1.enable_output()
            channel2.enable_output()

            power = lowerPowerLimit
            while(power < upperPowerLimit):
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
    
    main(
        freqList=[x * 1e6 for x in args.freqs],
        toneSpacing=args.toneSpacing,
        spectrumAnalyser=e4407b,
        signalGenerator=sdg2122x,
        signalGeneratorChannels=[1, 2],
        lowerPowerLimit=-40,
        upperPowerLimit=-10,
        refLevel=25
    )
