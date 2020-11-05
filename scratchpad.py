from AutomatedTesting.TopLevel.config import tenmaSingleChannel as psu
from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from time import sleep

with InstrumentSupervisor() as supervisor:
    supervisor.request_resources([psu])
    x = psu.reserve_channel(1, "test")
    x.set_voltage(1)
    x.set_current(0.01)
    x.enable_output(True)
    sleep(1)
    x.measure_voltage()
    sleep(2)
    print("Done")
