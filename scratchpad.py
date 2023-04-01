import sys
from time import sleep

from AutomatedTesting.Instruments.InstrumentConfig import dmm

with dmm:
    dmm.configure_resistance()
    while True:
        print(dmm._query("READ?"))
