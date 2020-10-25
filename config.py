from psu_tenma_72_2535 import Tenma_72_2535
import pyvisa

# PyVisa Resource Manager
rm = pyvisa.ResourceManager('@py')

psu1 = Tenma_72_2535(rm, "ASRL/dev/ttyACM0::INSTR")