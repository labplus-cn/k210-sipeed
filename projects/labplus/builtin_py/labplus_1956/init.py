import KPU
import sensor, lcd, image
from board import LED, Button, Motor
from pmu import axp192
from display import *
from player import play

""" 
-------------------------------------------------------------------------------------------------------
- 盛思1956初始化
-------------------------------------------------------------------------------------------------------
"""
# LED
led = LED(24)
led.on()

# 音频选择开关
audio_enb = LED(17)
audio_enb.off()

# LCD
lcd.init()
# lcd.mirror(True)
# lcd.rotation(1)
lcd.direction(0x20) # 交换lcd, width/height; (320,240)=>(240,320)
lcd.write_reg(0x36, 0x48)   # 设置lcd方向和颜色
try:
    background = image.Image('/flash/startup_dark.jpg', copy_to_fb=True)
    lcd.display(background)
    del background
except:
    lcd.clear((0, 0, 255))
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "Error: Cannot find start.jpg", lcd.WHITE, lcd.BLUE) 
# lcd.clear((255, 0, 0))
# lcd.direction(0x48)
lcd_bl = LED(25)
lcd_bl.on()

# Play startup aduio
try:
    play('/flash/startup.wav')
except:
    pass

# Camera
# import time
try:
    # print("{0:8d}:sensor reset".format(time.ticks_ms()))
    sensor.reset()  
    # print("{0:8d}:sensor set_framesize".format(time.ticks_ms()))
except Exception as e:
    lcd.clear((0, 0, 255))
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "Camera: " + str(e), lcd.WHITE, lcd.BLUE) 
    
sensor.set_framesize(sensor.QVGA)
# print("{0:8d}:sensor set_pixformat".format(time.ticks_ms()))
sensor.set_pixformat(sensor.RGB565)
# print("{0:8d}:sensor set_vflip".format(time.ticks_ms()))
sensor.set_vflip(1)
# sensor.set_hmirror(1)
# print("{0:8d}:sensor run".format(time.ticks_ms()))
sensor.run(1)

# Image
img = image.Image()

# motors
m1 = Motor(0)
m2 = Motor(1)
m3 = Motor(2)
m4 = Motor(3)
MR1 = m1
MR2 = m2
ML1 = m4
ML2 = m3

# PMU
pmu = axp192()
