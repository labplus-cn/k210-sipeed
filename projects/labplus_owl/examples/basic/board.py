
# The MIT License (MIT)
# Copyright (c) 2019, Labplus@Development
# History:
# - Untitled - By: ZKH - 周五 7月 19 2019
# - 增加基础的lcd、sensor操作和K210模型应用、视觉功能 by tangliufeng 2019/09/4
from machine import UART,Timer
import sensor,lcd
import time
import json
import KPU
#-----------------------------------------------
# board init
#-----------------------------------------------
led = None
light = None
btn = None
uart = None
def board_init():
    # UART2 config:
    #   IO11 = UART2.Tx
    #   IO10 = UART2.Rx
    global led,light,btn, uart
    fm.register(11, fm.fpioa.UART2_TX)
    fm.register(10, fm.fpioa.UART2_RX)
    uart = machine.UART(machine.UART.UART2)
    uart.init(115200, 8, None, 1, timeout=100, read_buf_len=2048)

    # button:
    fm.register(25, fm.fpioa.GPIOHS25)
    btn = GPIO(GPIO.GPIOHS25, GPIO.IN, GPIO.PULL_NONE)

    # led:
    fm.register(24, fm.fpioa.GPIOHS24)
    led = GPIO(GPIO.GPIOHS24, GPIO.OUT)
    led.value(0)    # 默认开启

    # light:
    fm.register(26, fm.fpioa.GPIOHS26)
    light = GPIO(GPIO.GPIOHS26, GPIO.OUT)
    light.value(0)  # 默认关闭

    # Power on lcd/camera config
    lcd.init()
    # lcd.direction(0x28)
    lcd.clear((255, 0, 0))
    sensor.reset()
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_framesize(sensor.QVGA)
    sensor.set_vflip(1)
    sensor.run(1)
    # led on
    led.value(0)
    # light.value(1)
    print('system running')
#-----------------------------------------------
# 根据不同的状态显示LED
#   IDLE: 
#   RUN:    
def show_led():
    pass



#-----------------------------------------------------------------------
try:
    board_init()
except Exception as e:
    # 错误状态
    while True:
        led.value(0)
        time.sleep_ms(100)
        led.value(1)
        time.sleep_ms(900)
        if btn.value() == 0:
            break

# 开机时按键按下:
#   退出运行,进入repl模式
debug = False
if btn.value() == 0:
    time.sleep_ms(100)
    if btn.value() == 0:
        led.value(1)    # led off
        debug = True

sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.run(1)

task = KPU.load(0x300000)
anchor = (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52)
a = KPU.init_yolo2(task, 0.5, 0.3, 5, anchor)

while debug == False:
    img = sensor.snapshot()
    code = KPU.run_yolo2(task, img)
    print(code)
    # lcd.display(img)
