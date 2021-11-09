# -*- encoding:utf-8 -*-
'''
@文件    : boot.py
@说明    :
@作者    :
@版本    :
'''

from machine import UART,Timer
import sensor,lcd
#-----------------------------------------------
# board init
#-----------------------------------------------
led = None
light = None
btn = None
uart = None
lcd = None

# 
def board_init():
    """board_init :硬件初始化
    """
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
    sensor.run(1)
    # led on
    led.value(0)
    # light.value(1)

    uart.write(json.dumps({'return':True, 'msg':'Ready', 'code':0}))
    print('system running')
#-----------------------------------------------
# 根据不同的状态显示LED
#   IDLE: 
#   RUN:    
def show_led():
    pass

def is_btn_pressed():
    """is_btn_pressed :判断按键是否按下
    
    :return: True-按键按下;False-按键松开
    :rtype: bool
    """
    global btn
    if btn.value() == 0:
        return True
    else:
        return False

def led_on(en = True):
    global led
    if en == True:
        led.vlaue(0)
    else:
        led.value(1)

#### entry ###
try:
    board_init()
except Exception as e:
    # 错误状态
    while True:
        led_on(True)
        time.sleep_ms(100)
        led_on(False)
        time.sleep_ms(900)
    
if btn.value() == 1:
    UART.set_repl_uart(uart)
    print('hello')