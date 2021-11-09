import KPU
import sensor, lcd, image
from board import Button, LED, Motor,Ultrasonic
from display import *



""" 
-------------------------------------------------------------------------------------------------------
- 板载资源初始化
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
lcd.direction(0x28)
# lcd.mirror(True)
# lcd.direction(0x20) # 交换lcd, width/height; (320,240)=>(240,320)
# lcd.write_reg(0x36, 0x48)   # 设置lcd方向和颜色
try:
    background = image.Image('/flash/startup.jpg', copy_to_fb=True)
    lcd.display(background)
    del background
except:
    lcd.clear(lcd.BLUE)
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "labplus classroom kit", lcd.WHITE, lcd.BLUE) 
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
try:
    sensor.reset()  
except Exception as e:
    lcd.clear((0, 0, 255))
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "Camera: " + str(e), lcd.WHITE, lcd.BLUE) 

sensor.set_framesize(sensor.QVGA)
sensor.set_pixformat(sensor.RGB565)
sensor.run(1)

# Image
img = image.Image()

light = LED(25, invert=False)
light.off()

# motors
# m1 = Motor(0)
# m2 = Motor(1)
# m3 = Motor(2)
# m4 = Motor(3)
m1 = Motor(0,(21,20))

# PMU
# pmu = axp192()

# button
# btn = Button(25)
btn_left = Button(12)
btn_right = Button(13)
btn_up = Button(14)
btn_down = Button(15)
btn_ok = Button(24)

# Ultrasonic Sensor
ultrasonic = Ultrasonic(18, 19) 
