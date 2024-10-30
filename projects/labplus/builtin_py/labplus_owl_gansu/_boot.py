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
        d.value(1)
        ckl.value(0)
        utime.sleep_ms(10)
        ckl.value(1) 
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
d.value(0)
ckl.value(0)
utime.sleep_ms(10)
ckl.value(1)

# lcd.clear(lcd.RED)
# try:
#     fm.register(11, fm.fpioa.UART2_TX, force=True)
#     fm.register(10, fm.fpioa.UART2_RX, force=True)
#     uart = UART(UART.UART2)
#     uart.init(1152000, 8, None, 1, read_buf_len=128)
# except Exception as e:
#     lcd.clear(lcd.BLUE)
#     lcd.draw_string(0,200, str(e), lcd.WHITE, lcd.BLUE) 

# while True:
#     try:
#         uart.write(bytes([0xBB,0x01,0x02]))
#         time.sleep_ms(20)
#         lcd.draw_string(10,20, 'UART DEMO{}'.format(time.time()), lcd.WHITE, lcd.BLUE) 
#         if(uart.any()):
#             tmp = uart.read()
#             lcd.clear(lcd.BLUE)
#             lcd.draw_string(10,50, str(tmp), lcd.WHITE, lcd.BLUE) 
#             lcd.draw_string(10,70, str(len(tmp)), lcd.WHITE, lcd.BLUE) 
#             print(tmp)
#     except Exception as e:
#             lcd.clear(lcd.BLUE)
#             lcd.draw_string(0,200, str(e), lcd.WHITE, lcd.BLUE) 

from labplus import *

