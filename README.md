# Myo-Logger
Thalmic LabのMyoと通信し,EMG raw dataとIMU dataをcsvに記録する。
Myo-firmware-v1.0以降に対応

# Usage
 ```
 git clone https://github.com/retact/Myo-Logger.git
 cd Myo-Logger
 ```
 ### 付属のBluegigaBLED112ドングルをUSBポートに挿入する。  
  
 ### プログラムを使用する際にMyoドングルに対応するデバイスの名を確認し、コマンドライン引数に入力する。  
 ```
 <!-- mac -->
 python myo-logger.py /dev/tty.usb*
 <!-- linux -->
 python myo-logger.py /dev/ttyACM*
 ```
 ### コマンドライン引数入力がなくてもプログラムはそれを自動的に検出する。  




