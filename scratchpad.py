import sys
from time import sleep

from AutomatedTesting.Instruments.InstrumentConfig import scope
from AutomatedTesting.Tests.IMD_Full import run_imd_test

with scope:
    input_voltage_channel = scope.reserve_channel(1, "Input Voltage")
    output_voltage_channel = scope.reserve_channel(2, "Output Voltage")
