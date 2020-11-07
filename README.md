***
# Automated Testing
***

## Requirements
* udev rule is required to give access to any USB devices without use of `sudo`
* Pyvisa needs usb.py overwriting as it asks for an attribute that doesn't exist... just to make sure it doesn't exist which then throws an Attribute Error. Fix is to find usb.py in pyvisa-py and comment out:
```
supress_end_en, _ = self.get_attribute(ResourceAttribute.suppress_end_enabled)
        
if supress_end_en:
    raise ValueError(
        "VI_ATTR_SUPPRESS_END_EN == True is currently unsupported by pyvisa-py"
    )
```
and replace with
```
supress_end_en = False
```