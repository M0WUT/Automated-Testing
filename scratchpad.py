import sys
from time import sleep

from AutomatedTesting.Instruments.InstrumentConfig import sdg2122x, ssa3032x
from AutomatedTesting.Tests.IMD import run_imd_test

with sdg2122x, ssa3032x:
    lower_tone = sdg2122x.reserve_channel(1, "Lower Tone")
    upper_tone = sdg2122x.reserve_channel(2, "Upper Tone")
    ssa3032x.reserve("Spectrum Analyser")
    run_imd_test(
        freqList=[(10e6 * x) for x in range(1, 12)],
        toneSpacing=100e3,
        channel1=lower_tone,
        channel2=upper_tone,
        spectrumAnalyser=ssa3032x,
        lowerPowerLimit=-40,
        upperPowerLimit=-5,
        refLevel=20,
        intermodTerms=[3, 5],
        pickleFile="imdTest.P",
    )
