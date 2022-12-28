import logging
import signal
import sys
import time
from typing import Dict

from pyvisa import ResourceManager

from AutomatedTesting.Instruments.DigitalMultimeter.Agilent_34401A import Agilent34401A
from AutomatedTesting.Instruments.PowerMeter.Agilent_U2001A import Agilent_U2001A
from AutomatedTesting.Instruments.SignalGenerator.Agilent_E4433B import Agilent_E4433B
from AutomatedTesting.Instruments.SignalGenerator.Siglent_SDG2122X import (
    Siglent_SDG2122X,
)

resource_manager = ResourceManager("@py")

logger = logging.getLogger("m0wut_automated_testing")
logging_format = logging.Formatter("%(levelname)s: %(asctime)s %(message)s")
logger.setLevel(logging.DEBUG)

# Console Logging
logging_handler = logging.StreamHandler()
logging_handler.setLevel(logging.INFO)
logging_handler.setFormatter(logging_format)
logger.addHandler(logging_handler)

# File logging
# loggingFileHandler = logging.FileHandler('warnings.log')
# loggingFileHandler.setLevel(logging.WARNING)
# loggingFileHandler.setFormatter(loggingFormat)
# logger.addHandler(loggingFileHandler)

sdg2122x = Siglent_SDG2122X(
    resource_manager=resource_manager,
    visaAddress="TCPIP::10.59.73.11::INSTR",
    instrumentName="Siglent SDG2122X",
    expectedIdnResponse="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",  # noqa E501
    verify=True,
    logger=logger,
)

u2001a = Agilent_U2001A(
    resource_manager=resource_manager,
    visaAddress="USB0::2391::11032::MY53150007::0::INSTR",
    instrumentName="Agilent U2001A",
    expectedIdnResponse="Agilent Technologies,U2001A,MY53150007,A1.03.05",
    verify=True,
    logger=logger,
)

e4433b = Agilent_E4433B(
    resource_manager=resource_manager,
    visaAddress="ASRL/dev/serial/by-id/usb-FTDI_USB-RS232_Cable_FT4WIYQP-if00-port0::INSTR",  # noqa E501
    instrumentName="Agilent E4433B",
    expectedIdnResponse="Hewlett-Packard, ESG-D4000B, GB38320196, B.03.86",
    verify=True,
    logger=logger,
    timeout=5000,
)

dmm = Agilent34401A(
    resource_manager=resource_manager,
    visaAddress="ASRL/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0::INSTR",  # noqa E501
    instrumentName="Agilent 34401A",
    expectedIdnResponse="HEWLETT-PACKARD,34401A,0,10-5-2",
    verify=True,
    logger=logger,
)

instrument_list = [sdg2122x, u2001a, e4433b, dmm]


def check_online_instruments() -> Dict[str, bool]:
    """
    Returns a dictionary of instrument name to status
    (True means responding to connections)
    """
    status_dict = {}
    for instrument in instrument_list:
        status_dict[instrument.instrumentName] = instrument.test_connection()

    return status_dict


# Attach handler to signal thrown by any error monitoring thread
def panic(*args, **kwargs):
    logger.error("Panicking, halting program")
    sys.exit(1)


signal.signal(signal.SIGUSR1, panic)


def main():
    while True:
        print(check_online_instruments())
        time.sleep(2)


if __name__ == "__main__":
    main()
