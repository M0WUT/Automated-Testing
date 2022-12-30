# Automated-Testing
Code for automating of my RF test equipment

Folder Structure:
* AutomatedTesting: Python module that can be imported - all instrument control code is in here
* unit-tests: Unit tests
* ProperTests : Tests designed to measure some parameter of RF circuitry utilising the AutomatedTesting module for instrument control
* scratchpad.py: Test file used for developing tests - contents in this file should not be treated as anything important. Once a test is working, it will be moved to the ProperTests folder

# Required Install
* Install dependency of numpy
`sudo apt install libatlas-base-dev`

* Install module as editable (must be run from this folder)
`pip3 install -e .`

# Sidenote - Install of VNC for spectrum analyser viewing
Install
`sudo apt install realvnc-vnc-viewer`

Add the following to 
`sudo nano /lib/systemd/system/name-of-service.service`

```
[Unit]
Description=Start VNC Viewer for Siglent Spectrum Analyser

[Service]
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
ExecStart=vncviewer 10.59.73.133 -WarnUnencrypted=0 -Fullscreen -HideCloseAlert=1 -KeepAliveResponseTimeout=1 -KeepAliveInterval=10
Restart=always
RestartSec=10s
KillMode=process
TimeoutSec=infinity

[Install]
WantedBy=graphical.target
```
