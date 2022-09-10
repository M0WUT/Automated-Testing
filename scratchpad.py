from AutomatedTesting.Instruments.InstrumentConfig import sdg2122x

with sdg2122x as siggen:
    test = siggen.reserve_channel(1, "test")
    test.set_freq(2e6)
