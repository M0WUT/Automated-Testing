import sys
from time import sleep

from AutomatedTesting.Instruments.InstrumentConfig import sdg2122x, ssa3032x
from AutomatedTesting.Tests.IMD import run_imd_test

with sdg2122x, ssa3032x:
    lower_tone = sdg2122x.reserve_channel(1, "Lower Tone")
    upper_tone = sdg2122x.reserve_channel(2, "Upper Tone")
    ssa3032x.reserve("Spectrum Analyser")
    run_imd_test(
        freqList=[50e6, 100e6],
        toneSpacing=1e6,
        channel1=lower_tone,
        channel2=upper_tone,
        spectrumAnalyser=ssa3032x,
        lowerPowerLimit=-40,
        upperPowerLimit=-5,
        refLevel=25,
        intermodTerms=[3, 5],
        pickleFile="imdTest.P",
    )
