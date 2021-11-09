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
from modules import ws2812
rgb_led = ws2812(34,2)

# LCD
lcd.init(freq=15000000, invert=1)
try:
    background = image.Image('/flash/startup_dark.jpg', copy_to_fb=True)
    lcd.display(background)
    del background
except:
    lcd.clear(lcd.BLUE)
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "labplus AI+ Camera", lcd.WHITE, lcd.BLUE) 

# Camera
try:
    sensor.reset()  
except Exception as e:
    lcd.clear((0, 0, 255))
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "Camera: " + str(e), lcd.WHITE, lcd.BLUE) 
sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.RGB565)
sensor.set_vflip(1)
sensor.set_hmirror(1)
sensor.run(1)

# Image
# img = image.Image()

# button
btn_A = button(16)
btn_B = button(17)
