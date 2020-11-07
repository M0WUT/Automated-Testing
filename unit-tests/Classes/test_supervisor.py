from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor


def test_entry_exit():
    with InstrumentSupervisor() as _:
        pass
    pass
