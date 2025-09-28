# Standard imports
from typing import Callable
from dataclasses import dataclass

# Third party imports

# Local imports
from AutomatedTesting.Misc.Units import Units


@dataclass
class Transducer:
    """
    Base class for anything that converts the signal
    being measured from one unit to another. e.g. an antenna
    (converts from field strength to power). Given it is likely
    that we measure the output of the transducer and want to know
    what was present at the input, this is how the conversion_func is defined.
    It takes 2 arguments <frequency-in-Hz> and <value-in-output-units>
    returns <value-in-input-units>
    """

    input_units: Units
    output_units: Units
    conversion_func_output_to_input: Callable[[float, float], float]
