from AutomatedTesting.Instruments.InstrumentConfig import psu2, psu3

with psu2, psu3:
    psu2_channel = psu2.reserve_channel(1, "Test")
    psu3_channel = psu3.reserve_channel(1, "Test2")
    
    psu2_channel.set_voltage(4)
    psu2_channel.set_current_limit(0.1)
    print("HELLO")
    print(psu2_channel.get_output_enabled_state())
    print(psu2_channel.get_voltage())
    print(psu2_channel.get_current_limit())
