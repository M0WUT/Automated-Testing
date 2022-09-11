from pyvisa import ResourceManager

rm = ResourceManager("@py")

my_instrument = rm.open_resource("USB0::1003::8293::GPIB_19_95936323834351215181::0::INSTR")
print(my_instrument.query("*IDN?"))
