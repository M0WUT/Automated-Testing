from AutomatedTesting.Instruments.InstrumentConfig import dmm
from AutomatedTesting.UsefulFunctions import prefixify

with dmm:
    while True:
        print(prefixify(dmm.measure_voltage(), 3, "V"))
