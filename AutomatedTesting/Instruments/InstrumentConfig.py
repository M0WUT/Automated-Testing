import logging
from time import sleep

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from pyvisa import ResourceManager

resourceManager = ResourceManager("@py")

logger = logging.getLogger("m0wut_automated_testing")
loggingFormat = logging.Formatter("%(levelname)s: %(asctime)s %(message)s")
logger.setLevel(logging.DEBUG)

# Console Logging
loggingConsoleHandler = logging.StreamHandler()
loggingConsoleHandler.setLevel(logging.DEBUG)
loggingConsoleHandler.setFormatter(loggingFormat)
logger.addHandler(loggingConsoleHandler)

# File logging
# loggingFileHandler = logging.FileHandler('warnings.log')
# loggingFileHandler.setLevel(logging.WARNING)
# loggingFileHandler.setFormatter(loggingFormat)
# logger.addHandler(loggingFileHandler)


if __name__ == "__main__":
    testInstrument = BaseInstrument(
        resourceManager,
        visaAddress="TCPIP::10.59.73.11::INSTR",
        instrumentName="SDG2122X",
        expectedIdnResponse="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",
        verify=False,
        logger=logger,
    )

    while True:
        print(testInstrument.test_connection())
        sleep(2)
