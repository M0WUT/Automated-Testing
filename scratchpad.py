from AutomatedTesting.TestDefinitions.TestSupervisor import \
    TestSupervisor
import logging
from AutomatedTesting.TopLevel.config import tests_to_perform, testSetup


with TestSupervisor(loggingLevel=logging.INFO, setup=testSetup) as supervisor:
    for test in tests_to_perform:
        supervisor.request_measurements(
            test.generate_measurement_points()
        )

    supervisor.run_measurements()

    for test in tests_to_perform:
        test.process_results(
            supervisor.results
        )
