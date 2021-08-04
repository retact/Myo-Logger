# 
# Licensed under the MIT license. See the LICENSE file for details.
#

import sys
import time
from myoraw import MyoRaw, DataCategory, EMGMode

def proc_emg(timestamp, emg, moving, characteristic_num, times=[]):
    print(emg)
    print(time.time())

m = MyoRaw(sys.argv[1] if len(sys.argv) >= 2 else None)
m.add_handler(DataCategory.EMG, proc_emg)
m.subscribe(EMGMode.RAW)

m.set_sleep_mode(1)
m.vibrate(1)

try:
    while True:
        m.run(1)

except KeyboardInterrupt:
    pass
finally:
    # print("Power off")
    m.disconnect()
    print("Disconnected")
