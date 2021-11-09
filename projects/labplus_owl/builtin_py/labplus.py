from machine import I2C, PWM, SPI, Timer, UART
from Maix import GPIO, FPIOA
import KPU
import sensor, lcd, image
from board import button, LED
from display import *

""" 
-------------------------------------------------------------------------------------------------------
- 盛思OWL初始化
-------------------------------------------------------------------------------------------------------
"""
# LED
led = LED(24)
led.on()

# 音频选择开关
# audio_enb = LED(17)
# audio_enb.off()

# LCD
lcd.init()
lcd.rotation(2)
# lcd.mirror(True)
# lcd.direction(0x20) # 交换lcd, width/height; (320,240)=>(240,320)
# lcd.write_reg(0x36, 0x48)   # 设置lcd方向和颜色
try:
    background = image.Image('/flash/startup_dark.jpg', copy_to_fb=True)
    lcd.display(background)
    del background
except:
    lcd.clear(lcd.BLUE)
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "labplus AI+ Camera", lcd.WHITE, lcd.BLUE) 
# lcd.clear((255, 0, 0))
# lcd.direction(0x48)
# lcd_bl = LED(25)
# lcd_bl.on()

# Play startup aduio
# try:
#     play('/flash/startup.wav')
# except:
#     pass

# Camera
sensor.reset()
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.RGB565)
sensor.set_vflip(1)
sensor.set_hmirror(0)
sensor.run(1)

# Image
img = image.Image()

light = LED(26, invert=False)
light.off()

# motors
# m1 = Motor(0)
# m2 = Motor(1)
# m3 = Motor(2)
# m4 = Motor(3)

# PMU
# pmu = axp192()

# button
btn = button(25)
