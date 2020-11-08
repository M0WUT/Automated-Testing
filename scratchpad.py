from AutomatedTesting.TopLevel.config import smb100a as sigGen, tenmaSingleChannel as psu
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
import logging
from time import sleep


with InstrumentSupervisor(loggingLevel=logging.DEBUG) as supervisor:
    supervisor.request_resources([sigGen, psu])
    channel = sigGen.reserve_channel(1, "test")
    channel.set_freq(1e9)
    channel.set_power(-100)
    channel.enable_output(True)
    sleep(1)
    x = psu.reserve_channel(1, "test")
    x.set_voltage(3)
    x.set_current(0.01)
    x.enable_output()
    sleep(1)
    channel.disable_output()
    sleep(1)
    x.disable_output()
    sleep(1)
    x.enable_output()
    channel.enable_output()
    sleep(10)
