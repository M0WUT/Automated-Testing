from time import sleep

from AutomatedTesting.Instruments.InstrumentConfig import e4433b, u2001a

with e4433b as sigGen, u2001a as powerMeter:
    testSource = sigGen.reserve_channel(1, "Test Source")
    powerMeter.reserve("Power Meter")
    testSource.set_soft_power_limits(-60, 0)
    for freq in [1e9]:
        print(freq)
        testSource.set_freq(freq)
        powerMeter.set_freq(freq)
        for power in range(-60, 0):
            print(power)
            testSource.set_power(power)
            sleep(1)
            print(f"{power}, {powerMeter.measure_power()}")
