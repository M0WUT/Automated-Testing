import logging
import sys
import time
import signal

from pyvisa import ResourceManager
from pyvisa.constants import StopBits


from AutomatedTesting.Instruments.DigitalMultimeter.Agilent_34401A import Agilent34401A
from AutomatedTesting.Instruments.Oscilloscope.Keysight_MSOX2024A import (
    KeysightMSOX2024A,
)
from AutomatedTesting.Instruments.PowerMeter.Agilent_U2001A import AgilentU2001A
from AutomatedTesting.Instruments.PowerSupply.Siglent_SPD3303X import SiglentSPD3303X
from AutomatedTesting.Instruments.PowerSupply.TenmaPSU import Tenma722535, Tenma722940
from AutomatedTesting.Instruments.SignalGenerator.Agilent_E4433B import AgilentE4433B
from AutomatedTesting.Instruments.SignalGenerator.RohdeAndSchwarz_SMB100A import (
    RohdeAndSchwarzSMB100A,
)
from AutomatedTesting.Instruments.SignalGenerator.Siglent_SDG2122X import (
    SiglentSDG2122X,
)
from AutomatedTesting.Instruments.SpectrumAnalyser.Siglent_SSA3032XPlus import (
    SiglentSSA3032XPlus,
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

sdg2122x = SiglentSDG2122X(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.11::INSTR",
    name="Siglent SDG2122X",
    expected_idn_response="Siglent Technologies,SDG2122X,SDG2XCAX5R0800,2.01.01.35R3B2",  # noqa E501
    verify=True,
    logger=logger,
)

u2001a = AgilentU2001A(
    resource_manager=resource_manager,
    visa_address="USB0::2391::11032::MY53150007::0::INSTR",
    name="Agilent U2001A",
    expected_idn_response="Agilent Technologies,U2001A,MY53150007,A1.03.05",  # noqa E501
    verify=True,
    logger=logger,
)

e4433b = AgilentE4433B(
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

psu2 = Tenma722535(
    resource_manager=resource_manager,
    visa_address="ASRL/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_A02014090305-if00::INSTR",  # noqa E501
    name="Tenma 72-2535",
    expected_idn_response="TENMA 72-2535 V2.1",
    verify=True,
    logger=logger,
)

psu3 = Tenma722940(
    resource_manager=resource_manager,
    visa_address="ASRL/dev/serial/by-id/usb-Nuvoton_USB_Virtual_COM_001461000452-if00::INSTR",  # noqa E501
    name="Tenma 72-2940",
    expected_idn_response="TENMA 72-2940 V5.7 SN:39846080",
    verify=True,
    logger=logger,
)

psu4 = SiglentSPD3303X(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.57::INSTR",
    name="Siglent SPD3303X",
    expected_idn_response="Siglent Technologies,SPD3303X,SPD3XIEX6R2056,1.01.01.02.07R2,V3.0",  # noqa E501
    verify=True,
    logger=logger,
)

ssa3032x = SiglentSSA3032XPlus(
    resource_manager=resource_manager,
    visa_address="TCPIP::ssa3021x.secure.shack.m0wut.com::INSTR",
    name="Siglent SSA3032X+",
    expected_idn_response="Siglent Technologies, ,XXXXXXXXXX,3.2.2.6.3R2.r2",  # noqa E501
    verify=True,
    logger=logger,
)

scope = KeysightMSOX2024A(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.194::INSTR",
    name="Keysight MSOX2024A",
    expected_idn_response="AGILENT TECHNOLOGIES,MSO-X 2024A,MY56040858,02.41.2015102200",  # noqa E501
    verify=True,
    logger=logger,
)

smb100a = RohdeAndSchwarzSMB100A(
    resource_manager=resource_manager,
    visa_address="TCPIP::10.59.73.10::INSTR",
    name="R&S SMB100A",
    expected_idn_response="Rohde&Schwarz,SMB100A,1406.6000k03/180437,3.1.19.15-3.20.390.24",  # noqa E501
    verify=True,
    logger=logger,
)


# Attach handler to signal thrown by any error monitoring thread
def panic(*args, **kwargs):
    logger.error("Panicking, halting program")
    sys.exit(1)


signal.signal(signal.SIGTERM, panic)


def main():
    with scope:
        time.sleep(1)
    # instrument_list = [sdg2122x, u2001a, e4433b, dmm, psu2, psu3]
    # while True:
    #     print(check_online_instruments(instrument_list))
    #     time.sleep(2)


if __name__ == "__main__":
    main()
