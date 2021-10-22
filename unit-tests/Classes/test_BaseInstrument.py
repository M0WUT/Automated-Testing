from AutomatedTesting.TopLevel.config import tenmaSingleChannel as psu
import pytest
import pyvisa


@pytest.mark.psu
def test_invalid_resource_manager():
    with pytest.raises(AssertionError):
        psu.initialise(None, None)


@pytest.mark.psu
def test_invalid_supervisor():
    rm = pyvisa.ResourceManager('@py')
    with pytest.raises(AssertionError):
        psu.initialise(rm, None)
