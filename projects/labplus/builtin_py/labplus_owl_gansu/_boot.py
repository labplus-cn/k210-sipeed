import os, sys, time
import utime
from Maix import GPIO
from fpioa_manager import fm
# import lcd,image
from machine import UART

sys.path.append('')
sys.path.append('.')

# chdir to "/sd" or "/flash"
devices = os.listdir("/")
if "sd" in devices:
    # os.chdir("/sd")
    sys.path.append('/sd')
else:
    os.chdir("/flash")
os.chdir('/flash')
sys.path.append('/flash')

for i in range(200):
    time.sleep_ms(1) # wait for key interrupt(for maixpy ide)

fm.register(34,fm.fpioa.GPIO0,force=True)
d=GPIO(GPIO.GPIO0,GPIO.OUT)
fm.register(33,fm.fpioa.GPIO1,force=True)
ckl=GPIO(GPIO.GPIO1,GPIO.OUT)
ckl.value(1)
fm.register(32,fm.fpioa.GPIO2,force=True)
clear=GPIO(GPIO.GPIO2,GPIO.OUT)
ckl.value(0)
fm.register(12, fm.fpioa.GPIOHS1, force=True)
s1 = GPIO(GPIO.GPIOHS1, GPIO.IN)
fm.register(13, fm.fpioa.GPIOHS2, force=True)
s2 = GPIO(GPIO.GPIOHS2, GPIO.IN)
utime.sleep_ms(10)

start = utime.ticks_ms()
while True:
    if utime.ticks_ms() - start > 200:
        break
    if s1.value() == 0: # 等待按键按下
        # print("s1")
        # d.value(1)
        d.value(0)
        clear.value(1)
        utime.sleep_ms(2)
        ckl.value(0)
        utime.sleep_ms(5)
        ckl.value(1) 
        utime.sleep_ms(2)
        clear.value(0)
        import lcd,image
        img = image.Image()
        img.draw_string(80, 120, "In download mode.", scale=1.5)
        lcd.init(freq=15000000, invert=1)
        lcd.rotation(2) 
        lcd.display(img) 
        lcd.deinit()
        while True:
            utime.sleep_ms(50)
        
# 进入串口通信状态
# d.value(0)
d.value(1)
clear.value(1)
utime.sleep_ms(2)
ckl.value(0)
utime.sleep_ms(5)
ckl.value(1) 

print('# 进入串口通信状态')

from labplus import *
