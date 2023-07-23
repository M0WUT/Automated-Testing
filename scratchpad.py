import math
import sys
from time import sleep

from numpy import logspace

from AutomatedTesting.Instruments.InstrumentConfig import dmm, smb100a, ssa3032x
from AutomatedTesting.Tests.GainFlatnessPAE import run_gain_flatness_test

with smb100a, ssa3032x, dmm:
    test_tone = smb100a.reserve_channel(1, "Test Tone")
    test_tone.set_soft_power_limits(test_tone.absolute_min_power, 0)
    dmm.reserve("Current Measurement")
    ssa3032x.reserve("Power Measurement")
    run_gain_flatness_test(
        freq_list=[20e6, 28e6, 30e6],
        input_power_list=range(-40, 0, 1),
        sig_gen=test_tone,
        power_meter=ssa3032x,
        dmm=dmm,
    )

# with ssa3032x, sdg2122x:
#     lower_channel = sdg2122x.reserve_channel(1, "Lower Tone")
#     upper_channel = sdg2122x.reserve_channel(2, "Upper Tone")

#     run_imd_test(
#         freqList=[20e6],
#         toneSpacing=1e6,
#         channel1=lower_channel,
#         channel2=upper_channel,
#         spectrumAnalyser=ssa3032x,
#         lowerPowerLimit=-40,
#         upperPowerLimit=3,
#         refLevel=25,
#         intermodTerms=[3, 5],
#         resolutionBandWidth=10e3
#         # pickleFile="imdTest.P",
#     )
