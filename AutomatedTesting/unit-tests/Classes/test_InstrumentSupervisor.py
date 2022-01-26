import pytest
from AutomatedTesting.Instruments.TopLevel.config import tenmaSingleChannel as psu
from AutomatedTesting.Instruments.TopLevel.InstrumentSupervisor import (
    InstrumentSupervisor,
)


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
