import logging
import signal
from typing import Dict

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


testInstrument = BaseInstrument(
    resourceManager,
    visaAddress="TCPIP::10.59.73.11::INSTR",
    instrumentName="SDG2122X",
    expectedIdnResponse="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",
    verify=False,
    logger=logger,
)


instrumentList = [testInstrument]


def check_online_instruments() -> Dict[str:bool]:
    statusDict = {}
    for instrument in instrumentList:
        statusDict[instrument.instrumentName] = instrument.test_connection()

    return statusDict


# Attach handler to signal thrown by any error monitoring thread
def panic():
    raise Exception()


signal.signal(signal.SIGUSR1, panic)


def main():
    print(check_online_instruments())


if __name__ == "__main__":
    main()
