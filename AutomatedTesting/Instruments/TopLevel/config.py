from AutomatedTesting.Instruments.NoiseSource.Noisecom_NC346B import Noisecom_NC346
from AutomatedTesting.Instruments.PowerMeter.Agilent_U2001A import Agilent_U2001A
from AutomatedTesting.Instruments.PSU.Tenma_72_2535 import Tenma_72_2535
from AutomatedTesting.Instruments.SignalGenerator.RandS_SMB100A import RandS_SMB100A
from AutomatedTesting.Instruments.SignalGenerator.Siglent_SDG2122X import (
    Siglent_SDG2122X,
)
from AutomatedTesting.Instruments.SpectrumAnalyser.Agilent_E4407B import Agilent_E4407B

tenmaSingleChannel = Tenma_72_2535("ASRL/dev/ttyACM1::INSTR")
smb100a = RandS_SMB100A("TCPIP::smb100a.secure::INSTR")
u2001a = Agilent_U2001A("USB0::2391::11032::MY53150007::0::INSTR")
e4407b = Agilent_E4407B(
    "USB0::1003::8293::Hewlett-Packard__E4407B__SG44210622__A.14.01::0::INSTR",
    enableDisplay=True,
)
# e4407b = Agilent_E4407B("GPIB0::18::INSTR", enableDisplay=True)
# sdg2122x = Siglent_SDG2122X("USB::0xf4ec::0x1102::SDG2XCAX5R0800::INSTR")
sdg2122x = Siglent_SDG2122X("TCPIP::sdg2042x.secure::INSTR")
noiseSource = Noisecom_NC346()
