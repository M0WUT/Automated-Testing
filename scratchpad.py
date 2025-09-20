# flake8: noqa

import math
import sys
from time import sleep

from numpy import logspace

from AutomatedTesting.Instruments.InstrumentConfig import (
    dmm,
    e4433b,
    sdg2122x,
    smb100a,
    ssa3032x,
)
from AutomatedTesting.Instruments.SpectrumAnalyser.SpectrumAnalyser import (
    SpectrumAnalyser,
)


# with smb100a, ssa3032x, dmm:
#     test_tone = smb100a.reserve_channel(1, "Test Tone")
#     test_tone.set_soft_power_limits(test_tone.absolute_min_power, 5)
#     dmm.reserve("Current Measurement")
#     ssa3032x.reserve("Power Measurement")
#     run_gain_flatness_test(
#         freq_list=[20e6, 28e6, 30e6],
#         input_power_list=range(-40, 5, 1),
#         sig_gen=test_tone,
#         power_meter=ssa3032x,
#         dmm=dmm,
#         loss_before_dut=0,
#         loss_after_dut=0,
#         ref_level=30,
#     )


with ssa3032x:
    ssa3032x.set_rbw(9000, SpectrumAnalyser.FilterType.EMI)
