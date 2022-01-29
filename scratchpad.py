import logging
from time import sleep

import serial

from AutomatedTesting.Instruments.SignalGenerator.SignalGenerator import SignalGenerator
from AutomatedTesting.Instruments.TopLevel.config import (
    e4407b,
    noiseSource,
    sdg2122x,
    tenmaSingleChannel,
)
from AutomatedTesting.ProperTests.IMD import run_imd_test
from AutomatedTesting.ProperTests.NoiseFigure import run_noise_figure_test
from AutomatedTesting.PytestDefinitions.TestSupervisor import TestSupervisor

PORT = "/dev/ttyACM0"
BAUDRATE = 9600
TIMEOUT = 1


with TestSupervisor(
    loggingLevel=logging.DEBUG,
    instruments=[e4407b, noiseSource, tenmaSingleChannel],
    saveResults=False,
):
    psu = tenmaSingleChannel.reserve_channel(1, "Power Supply")

    run_noise_figure_test(
        10e6,
        6e9,
        e4407b,
        psu,
        noiseSource,
        1001,
        sweepTime=30,  # , pickleFile="noiseFigure.P"
    )
