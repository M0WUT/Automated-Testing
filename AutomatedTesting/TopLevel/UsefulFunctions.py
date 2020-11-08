def readable_freq(freq):
    """
    Converts frequency in Hz to human readable
    form.

    Args:
        freq (float): Frequency in Hz

    Returns:
        str: Frequency as nicely formatted string

    Raises:
        None
    """
    if(freq >= 1e9):
        divider = 1e9
        units = "GHz"
    elif(freq >= 1e6):
        divider = 1e6
        units = "MHz"
    elif(freq >= 1e3):
        divider = 1e3
        units = "kHz"
    else:
        divider = 1
        units = "Hz"

    x = str(freq / divider)

    # See if we can trim annoying ".0" that
    # Python puts on integer floats
    if(x[-2:] == '.0'):
        return x[:-2] + units
    else:
        return x + units
