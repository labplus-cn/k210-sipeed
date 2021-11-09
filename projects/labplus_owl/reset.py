import serial
import time

s = serial.Serial('/dev/ttyUSB0')

# rts = 0, dtr = 0 ---> k210.nRST = 1, k210.boot = 1
s.rts = True
s.dtr = True
time.sleep(0.01)
# rts = 0, dtr = 1 ---> k210.nRST = 0, k210.boot = 1
s.dtr = False
time.sleep(0.01)
# rts = 0, dtr = 0 ---> k210.nRST = 1, k210.boot = 1
s.dtr = True
s.close()

import os
os.system('python3 -m serial.tools.miniterm /dev/ttyUSB0 115200')