import logging
import signal
import time
from typing import Dict

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.PowerMeter.Agilent_U2001A import (
    Agilent_U2001A,
)
from AutomatedTesting.Instruments.SignalGenerator.Agilent_E4433B import (
    Agilent_E4433B,
)
from AutomatedTesting.Instruments.SignalGenerator.Siglent_SDG2122X import (
    Siglent_SDG2122X,
)
from pyvisa import ResourceManager

resourceManager = ResourceManager("@py")

logger = logging.getLogger("m0wut_automated_testing")
loggingFormat = logging.Formatter("%(levelname)s: %(asctime)s %(message)s")
logger.setLevel(logging.DEBUG)

# Console Logging
loggingConsoleHandler = logging.StreamHandler()
loggingConsoleHandler.setLevel(logging.INFO)
loggingConsoleHandler.setFormatter(loggingFormat)
logger.addHandler(loggingConsoleHandler)

# File logging
# loggingFileHandler = logging.FileHandler('warnings.log')
# loggingFileHandler.setLevel(logging.WARNING)
# loggingFileHandler.setFormatter(loggingFormat)
# logger.addHandler(loggingFileHandler)

sdg2122x = Siglent_SDG2122X(
    resourceManager=resourceManager,
    visaAddress="TCPIP::10.59.73.11::INSTR",
    instrumentName="Siglent SDG2122X",
    expectedIdnResponse="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",
    verify=True,
    logger=logger,
)

u2001a = Agilent_U2001A(
    resourceManager=resourceManager,
    visaAddress="USB0::2391::11032::MY53150007::0::INSTR",
    instrumentName="Agilent U2001A",
    expectedIdnResponse="Agilent Technologies,U2001A,MY53150007,A1.03.05",
    verify=True,
    logger=logger,
)

e4433b = Agilent_E4433B(
    resourceManager=resourceManager,
    visaAddress="ASRL/dev/ttyUSB0::INSTR",
    instrumentName="Agilent E4433B",
    expectedIdnResponse="Hewlett-Packard, ESG-D4000B, GB38320196, B.03.86",
    verify=True,
    logger=logger,
    timeout=5000,
)

instrumentList = [sdg2122x, u2001a, e4433b]


def check_online_instruments() -> Dict[str, bool]:
    statusDict = {}
    for instrument in instrumentList:
        statusDict[instrument.instrumentName] = instrument.test_connection()

    return statusDict


# Attach handler to signal thrown by any error monitoring thread
def panic():
    raise Exception()


signal.signal(signal.SIGUSR1, panic)


def main():
    while True:
        print(check_online_instruments())
        time.sleep(2)


if __name__ == "__main__":
    main()
