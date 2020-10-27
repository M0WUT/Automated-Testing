from AutomatedTesting.PSU import psu_tenma_72_2535 as psu
import pyvisa

# PyVisa Resource Manager
rm = pyvisa.ResourceManager('@py')

tenmaSingleChannel = psu.Tenma_72_2535(rm, "ASRL/dev/ttyACM0::INSTR")
