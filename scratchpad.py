from AutomatedTesting.TopLevel.config import smb100a as sigGen
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
import logging
from time import sleep


with InstrumentSupervisor(loggingLevel=logging.INFO) as supervisor:
    supervisor.request_resources([sigGen])
    channel = sigGen.reserve_channel(1, "test")
    channel.set_freq(1e9)
    channel.set_power(0)
    channel.enable_output(True)
    sleep(10)
