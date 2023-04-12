import sys
from time import sleep

from AutomatedTesting.Instruments.InstrumentConfig import psu4

psu4.verify = False
with psu4:
    pass
