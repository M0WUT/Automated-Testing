from AutomatedTesting.TestDefinitions.TestSupervisor import \
    TestSupervisor
import logging
from AutomatedTesting.TopLevel.config import tests_to_perform, testSetup
from time import sleep
import struct



with TestSupervisor(loggingLevel=logging.INFO, setup=testSetup, calibrationPower=0) as supervisor:
    for x in tests_to_perform:
        supervisor.request_measurements(x.generate_measurement_points())
    supervisor.run_measurements()
    for x in tests_to_perform:
        x.process_results(supervisor.results)
