***
# Automated Testing
***

## Requirements
```
* Install pre-requisites (Based on https://xdevs.com/guide/ni_gpib_rpi/)
```
sudo apt install fxload bc bison flex libssl-dev libncurses5-dev
```
*Get rpi-source
```
wget https://raw.githubusercontent.com/notro/rpi-source/master/rpi-source -O /usr/bin/rpi-source && sudo chmod +x /usr/bin/rpi-source && /usr/bin/rpi-source -q --tag-update
```

*Run rpi-source
```
rpi-source
```

* Install more things
```
sudo apt-get install tk-dev build-essential texinfo texi2html libcwidget-dev libncurses5-dev libx11-dev binutils-dev bison flex libusb-1.0-0 libusb-dev libmpfr-dev libexpat1-dev tofrodos subversion autoconf automake libtool mercurial
```

* Make directory for linux-gpib
```
mkdir linux-gpib
cd linux-gpib
```

* Get latest linux-gpib
```
svn checkout svn://svn.code.sf.net/p/linux-gpib/code/trunk linux-gpib-code
```

* Make Kernel modules
```cd linux-gpib-kernel
make 
sudo make install
```

* Make User modules
```
cd ../linux-gpib-user
./bootstrap
./configure
make -j4
sudo make install
```

* Copy gpib conf file
```
sudo cp util/templates/gpib.conf /etc/gpib.conf
```

* Relink libraries
```
sudo ldconfig
```

# Actually getting somewhere!

* Edit gpib.conf
```
interface {
    minor       = 0             /* board index, minor = 0 uses /dev/gpib0, mino$
    board_type  = "ni_usb_b"    /* type of interface board being used */
    name        = "violet"      /* optional name, allows you to get a board des$
    pad         = 0             /* primary address of interface             */
    sad         = 0             /* secondary address of interface           */
    timeout     = T30s          /* timeout for commands */
    eos         = 0x0a          /* EOS Byte, 0xa is newline and 0xd is carriage$
    set-reos    = yes           /* Terminate read if EOS */
    set-bin     = no            /* Compare EOS 8-bit */
    set-xeos    = no            /* Assert EOI whenever EOS byte is sent */
    set-eot     = yes           /* Assert EOI with last byte on writes */
    master      = yes           /* interface board is system controller */
}
```

* Get GPIB-USB-B firmware loader and copy to /lib/firmware
```
wget https://linux-gpib.sourceforge.io/firmware/gpib_firmware-2008-08-10.tar.gz
tar -xf gpib_firmware-2008-08-10.tar.gz
cd gpib_firmware-2008-08-10.tar.gz
sudo cp -r ni_gpib_usb_b /lib/firmware/ni_usb_gpib

```

* Create udev rules (assuming you're already a member of "usbtmc")
```
#gpib-usb-b without firmware
SUBSYSTEM=="usb", ACTION=="add", ATTR{idVendor}=="3923", ATTR{idProduct}=="702b", ENV{DEVICE}="$devnode", RUN+="/usr/local/lib/udev/gpib_udev_fxloader"
#device id 713b is a keithley kusb-488 before we load it with firmware
SUBSYSTEM=="usb", ACTION=="add", ATTR{idVendor}=="3923", ATTR{idProduct}=="713b", ENV{DEVICE}="$devnode", RUN+="/usr/local/lib/udev/gpib_udev_fxloader"

#automatically set the correct --board-type option
ACTION=="add|change", SUBSYSTEM=="usb", DRIVER=="ni_usb_gpib", ATTRS{serial}=="*", ENV{GPIB_CONFIG_OPTIONS}+="--board-type ni_usb_b", ENV{SERIAL}="$attr{serial}"
#devices ready to be configured with gpib_config
SUBSYSTEM=="usb", ACTION=="add|change", DRIVER=="ni_usb_gpib", ATTRS{idVendor}=="3923", ATTRS{idProduct}=="702a", RUN+="/usr/local/lib/udev/gpib_udev_config"
SUBSYSTEM=="usb", ACTION=="add|change", DRIVER=="ni_usb_gpib", ATTRS{idVendor}=="3923", ATTRS{idProduct}=="702a", MODE="660", GROUP="usbtmc"
SUBSYSTEM=="usb", ACTION=="add|change", DRIVER=="ni_usb_gpib", ATTRS{idVendor}=="3923", ATTRS{idProduct}=="709b", RUN+="/usr/local/lib/udev/gpib_udev_config"
SUBSYSTEM=="usb", ACTION=="add|change", DRIVER=="ni_usb_gpib", ATTRS{idVendor}=="3923", ATTRS{idProduct}=="7618", RUN+="/usr/local/lib/udev/gpib_udev_config"
SUBSYSTEM=="usb", ACTION=="add|change", DRIVER=="ni_usb_gpib", ATTRS{idVendor}=="3923", ATTRS{idProduct}=="725[cd]", RUN+="/usr/local/lib/udev/gpib_udev_config"

#this rule generates new "change" udev events for devices supported by the
#driver after the module is loaded.
#it is needed because if the driver is not already loaded when the hardware is plugged in,
#then the initial hardware "add" event will not be able to accomplish anything.
SUBSYSTEM=="module", ACTION=="add", DEVPATH=="/module/ni_usb_gpib", RUN+="/usr/local/lib/udev/gpib_udevadm_wrapper trigger --property-match DRIVER=ni_usb_gpib"
KERNEL=="gpib[0-9]*", ACTION=="add", MODE="660", GROUP="usbtmc"
```

* Edit firmware loader
```
sudo nano /usr/local/lib/udev/gpib_udev_fxloader
```

Change DATADIR to /lib/firmware
Change all instances of "$DATADIR/usb" to "$DATADIR"

* Reboot
```
sudo reboot
```

* Python stuff
Requires Python 3 - tested with Pyhton 3.7.2 (32 bit):

```
pip3 install pyvisa pyvisa-py Xlsxwriter pyusb pyserial
```

* Pyvisa needs usb.py overwriting as it asks for an attribute that doesn't exist... just to make sure it doesn't exist which then throws an Attribute Error. Fix is to find usb.py in pyvisa-py and comment out:
```
sudo nano .local/lib/python3.7/site-packages/pyvisa_py/usb.py
```

```
supress_end_en, _ = self.get_attribute(ResourceAttribute.suppress_end_enabled)        
```
and replace with
```
supress_end_en = False

