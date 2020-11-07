from AutomatedTesting.TopLevel.config import tenmaSingleChannel as psu
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from time import sleep
import logging

with InstrumentSupervisor(loggingLevel=logging.INFO) as supervisor:
    supervisor.request_resources([psu])
    channel = psu.reserve_channel(1, "test")
    channel.set_voltage(1)
    channel.set_current(0.01)
    channel.enable_output(True)
    assert channel.measure_voltage() == 1
    assert channel.measure_current() == 0
    sleep(2)
