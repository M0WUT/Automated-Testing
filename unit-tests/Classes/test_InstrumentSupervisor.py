from AutomatedTesting.TopLevel.InstrumentSupervisor import InstrumentSupervisor
from AutomatedTesting.TopLevel.config import tenmaSingleChannel as psu
import pytest


@pytest.mark.psu
def test_entry_exit():
    with InstrumentSupervisor() as x:
        x.request_resources([psu])
    pass


@pytest.mark.psu
def test_free_invalid_resource():
    with InstrumentSupervisor() as x:
        with pytest.raises(ValueError):
            x.free_resource(psu)
    pass
