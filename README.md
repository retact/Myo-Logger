# Myo-Logger
Communicate with Myo at Thalmic Lab and record EMG raw data and IMU data in a csv files.
Compatible with Myo-firmware-v1.0 or later.

# Usage
 ```
 git clone https://github.com/retact/Myo-Logger.git
 cd Myo-Logger
 ```
 ### Insert the included BluegigaBLED112 dongle into the USB port.  
  
 To use the Myo-Logger, you might need to know the name of the device
corresponding to the Myo dongle. The programs will attempt to detect it
automatically, but if that doesn't work, here's how to find it out manually:  
  
- Linux: Run the command ``ls /dev/ttyACM*``. One of the names it prints (there
  will probably only be one) is the device. Try them each if there are multiple,
  or unplug the dongle and see which one disappears if you run the command
  again. If you get a permissions error, running ``sudo usermod -aG dialout
  $USER`` will probably fix it.  
 
- Windows: Open Device Manager (run ``devmgmt.msc``) and look under "Ports (COM &
  LPT)". Find a device whose name includes "Bluegiga". The name you need is in
  parentheses at the end of the line (it will be "COM" followed by a number).  
 
- Mac: Same as Linux, replacing ``ttyACM`` with ``tty.usb``.  

### exmample
-mac  
 ```
 python myo-logger.py --tty /dev/tty.usb*
 ```
-linux  
 ```
 python myo-logger.py --tty /dev/ttyACM*
 ```


