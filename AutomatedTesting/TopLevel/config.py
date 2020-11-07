from AutomatedTesting.PSU.Tenma_72_2535 import Tenma_72_2535
from AutomatedTesting.SignalGenerator.RandS_SMB100A import RandS_SMB100A

tenmaSingleChannel = Tenma_72_2535("ASRL/dev/ttyACM0::INSTR")
smb100a = RandS_SMB100A("USB::0x0AAD::0x0054::180437::INSTR")
