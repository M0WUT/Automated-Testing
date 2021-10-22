from AutomatedTesting.PSU.Tenma_72_2535 import Tenma_72_2535
from AutomatedTesting.SignalGenerator.RandS_SMB100A import RandS_SMB100A
from AutomatedTesting.PowerMeter.Agilent_U2001A import Agilent_U2001A
from AutomatedTesting.SpectrumAnalyser.Agilent_E4407B import Agilent_E4407B
from AutomatedTesting.SignalGenerator.Siglent_SDG2122X import Siglent_SDG2122X

tenmaSingleChannel = Tenma_72_2535("ASRL/dev/ttyACM0::INSTR")
smb100a = RandS_SMB100A("TCPIP::192.168.0.23::INSTR")
u2001a = Agilent_U2001A("USB0::2391::11032::MY53150007::0::INSTR")
e4407b = Agilent_E4407B("GPIB0::18::INSTR", enableDisplay=False)
sdg2122X = Siglent_SDG2122X("USB::0xf4ec::0x1102::SDG2XCAX5R0800::INSTR")
