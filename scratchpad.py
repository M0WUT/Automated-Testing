import math
import sys
from time import sleep

from numpy import logspace

from AutomatedTesting.Instruments.InstrumentConfig import scope, sdg2122x

results = []

with scope, sdg2122x, open("results.csv", "w") as results_file:

    SIGNAL_VPP = 10
    FREQ_LIST = logspace(2, 8, 100)

    test_signal = sdg2122x.reserve_channel(1, "Test Signal")
    input_voltage_channel = scope.reserve_channel(1, "Input Voltage")
    input_voltage_channel.set_voltage_range(2 * SIGNAL_VPP)
    output_voltage_channel = scope.reserve_channel(2, "Output Voltage")
    output_scale = 1
    output_voltage_channel.set_voltage_range(2 * SIGNAL_VPP)

    test_signal.set_load_impedance(float("inf"))
    test_signal.set_vpp(SIGNAL_VPP)
    test_signal.enable_output()

    for f in FREQ_LIST:
        freq = round(f)
        test_signal.set_freq(round(freq))
        achieved_timebase = 10 ** math.floor(math.log10(2 / freq))
        scope.set_timebase_scale(achieved_timebase)
        vin = input_voltage_channel.measure_rms()
        vout = output_voltage_channel.measure_rms()
        while (
            vout < 0.1 * output_voltage_channel.get_voltage_range()
            and output_scale > output_voltage_channel.allowed_volts_per_div[0]
        ):
            output_scale = output_voltage_channel.allowed_volts_per_div[
                output_voltage_channel.allowed_volts_per_div.index(output_scale) - 1
            ]
            output_voltage_channel.set_voltage_scale(output_scale)
            vout = output_voltage_channel.measure_rms()

        while vout > 0.25 * output_voltage_channel.get_voltage_range():
            output_scale = output_voltage_channel.allowed_volts_per_div[
                output_voltage_channel.allowed_volts_per_div.index(output_scale) + 1
            ]
            output_voltage_channel.set_voltage_scale(output_scale)
            vout = output_voltage_channel.measure_rms()

        gain = vout / vin
        print(gain)
        results.append((freq, gain))
        results_file.write(f"{freq},{gain}\n")
