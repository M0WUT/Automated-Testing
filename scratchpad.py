from AutomatedTesting.TopLevel.config import smb100a as sigGen
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from time import sleep
import logging
import pyvisa
import usb.core


with InstrumentSupervisor(loggingLevel=logging.INFO) as supervisor:
    supervisor.request_resources([sigGen])
    channel = sigGen.reserve_channel(1, "test")
