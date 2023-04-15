import logging
import signal
import sys
import time
from typing import Dict

from pyvisa import ResourceManager
from pyvisa.constants import StopBits

from AutomatedTesting.Instruments.BaseInstrument import BaseInstrument
from AutomatedTesting.Instruments.DigitalMultimeter.Agilent_34401A import Agilent34401A
from AutomatedTesting.Instruments.PowerMeter.Agilent_U2001A import Agilent_U2001A
from AutomatedTesting.Instruments.PowerSupply.Siglent_SPD3303X import Siglent_SPD3303X
from AutomatedTesting.Instruments.PowerSupply.TenmaPSU import (
    Tenma_72_2535,
    Tenma_72_2940,
)
from AutomatedTesting.Instruments.SignalGenerator.Agilent_E4433B import Agilent_E4433B
from AutomatedTesting.Instruments.SignalGenerator.Siglent_SDG2122X import (
    Siglent_SDG2122X,
)
from AutomatedTesting.Instruments.SpectrumAnalyser.Siglent_SSA3032XPlus import (
    Siglent_SSA3032XPlus,
)

resource_manager = ResourceManager("@py")

logger = logging.getLogger("m0wut_automated_testing")
logging_format = logging.Formatter("%(levelname)s: %(asctime)s %(message)s")
logger.setLevel(logging.DEBUG)

# Console Logging
logging_handler = logging.StreamHandler()
logging_handler.setLevel(logging.DEBUG)
logging_handler.setFormatter(logging_format)
logger.addHandler(logging_handler)

# File logging
# loggingFileHandler = logging.FileHandler('warnings.log')
# loggingFileHandler.setLevel(logging.WARNING)
# loggingFileHandler.setFormatter(loggingFormat)
# logger.addHandler(loggingFileHandler)

sdg2122x = Siglent_SDG2122X(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.11::INSTR",
    name="Siglent SDG2122X",
    expected_idn_response="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",  # noqa E501
    verify=True,
    logger=logger,
)

u2001a = Agilent_U2001A(
    resource_manager=resource_manager,
    visa_address="USB0::2391::11032::MY53150007::0::INSTR",
    name="Agilent U2001A",
    expected_idn_response="Agilent Technologies,U2001A,MY53150007,A1.03.05",
    verify=True,
    logger=logger,
)

e4433b = Agilent_E4433B(
    resource_manager=resource_manager,
    visa_address="ASRL/dev/serial/by-id/usb-FTDI_USB-RS232_Cable_FT4WIYQP-if00-port0::INSTR",  # noqa E501
    name="Agilent E4433B",
    expected_idn_response="Hewlett-Packard, ESG-D4000B, GB38320196, B.03.86",
    verify=True,
    logger=logger,
    timeout=5000,
)

dmm = Agilent34401A(
    resource_manager=resource_manager,
    visa_address="ASRL/dev/serial/by-id/usb-Prolific_Technology_Inc._USB-Serial_Controller_D-if00-port0::INSTR",  # noqa E501
    name="Agilent 34401A",
    expected_idn_response="HEWLETT-PACKARD,34401A,0,10-5-2",
    verify=True,
    logger=logger,
    stop_bits=StopBits.two,
)

psu2 = Tenma_72_2535(
    resource_manager=resource_manager,
    visa_address="ASRL/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_A02014090305-if00::INSTR",  # noqa E501
    name="Tenma 72-2535",
    expected_idn_response="TENMA 72-2535 V2.1",
    verify=True,
    logger=logger,
)

psu3 = Tenma_72_2940(
    resource_manager=resource_manager,
    visa_address="ASRL/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_001461000452-if00::INSTR",  # noqa E501
    name="Tenma 72-2940",
    expected_idn_response="TENMA 72-2940 V5.7 SN:39846080",
    verify=True,
    logger=logger,
)

psu4 = Siglent_SPD3303X(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.57::INSTR",
    name="Siglent SPD3303X",
    expected_idn_response="Siglent Technologies,SPD3303X,SPD3XIEX6R2056,1.01.01.02.07R2,V3.0",
    verify=True,
    logger=logger,
)

ssa3032x = Siglent_SSA3032XPlus(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.133::INSTR",
    name="Siglent SSA3032X+",
    expected_idn_response="Siglent Technologies, ,XXXXXXXXXX,3.2.2.5.1R1.r5",
    verify=True,
    logger=logger,
)


def check_online_instruments(instrument_list: list[BaseInstrument]) -> Dict[str, bool]:
    """
    Returns a dictionary of instrument name to status
    (True means responding to connections)
    """
    status_dict = {}
    for instrument in instrument_list:
        status_dict[instrument.name] = instrument.test_connection()

    return status_dict


# Attach handler to signal thrown by any error monitoring thread
def panic(*args, **kwargs):
    logger.error("Panicking, halting program")
    sys.exit(1)


signal.signal(signal.SIGUSR1, panic)


def main():
    with ssa3032x:
        pass
    instrument_list = [sdg2122x, u2001a, e4433b, dmm, psu2, psu3]
    while True:
        print(check_online_instruments(instrument_list))
        time.sleep(2)


if __name__ == "__main__":
    main()
