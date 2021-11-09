
# The MIT License (MIT)
# Copyright (c) 2019, Labplus@Development
# History:
# - Untitled - By: ZKH - 周五 7月 19 2019
# - 增加基础的lcd、sensor操作和K210模型应用、视觉功能 by tangliufeng 2019/09/4
from machine import UART,Timer
import sensor,lcd
import time
import json
import _thread
from ai import app
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

# AI操作相关接口
def ai_set_mode(new_mode):
    return app.set_mode(new_mode)
    
def ai_start(oneshot=False):
    return app.start(oneshot)

def ai_stop():
    return app.stop()

def ai_get_result():
    return app.get_result()

def ai_get_state():
    return app.get_state()

##-------------------------------------------------------------------------------------
def rpc(args):
    '''
    响应串口调用
    '''
    global config

    ret = {'return':True, 'msg':None, 'code':0}

    # 解析json字符串
    try:
        expression = json.loads(args)     # 解析命令
    except Exception as e:
        ret['return'] = False
        ret['msg'] = 'invalid commands'
        ret['code'] = -1
        return ret
    
    # call functions
    if isinstance(expression, dict):
        if 'f' in expression.keys():
            func = expression['f']
            if 'g' in expression.keys():
                globals  = expression['g']
            else:
                globals = None
            if 'l' in expression.keys():
                locals = expression['l']
            else:
                locals = None
        try:
            msg = eval(func, globals, locals)
            ret['return'] = True
            ret['msg'] = msg
            ret['code'] = type(msg) 
            return ret         
        except Exception as e:
            ret['return'] = False
            ret['msg'] = e
            ret['code'] = -2
            return ret
    else:
        ret['return'] = False
        ret['msg'] = 'not functions'
        ret['code'] = -3
        return ret 
#---------------------------------------------      
# 串口线程:接收串口数据并解析命令
def do_uart_work():
    '''
    '''
    global uart
    if uart.any() > 0:
        # 接收串口指令
        try:
            req = uart.readline()
            t1 = time.ticks_ms()
            # 远程调用
            if req[0] == ord('@'):
                rsp = rpc(req[1:])
                uart.write(json.dumps(rsp))
                t2 = time.ticks_ms()
                print("{0: 8d} uart recieve:\n{1}".format(t1, req))
                print("{0: 8d} uart respose:\n{1}".format(t2, rsp))
            # 发送数据
            if req[0] == ord('<'):
                rsp = bytearray('\x01\x02\x03\x04\x05')
                uart.write(rsp)
            # 接收数据
            if req[1] == ord('>'):
                pass
        except Exception as e:      # 行接收超时
            print(e)

btn_hold_time = 0
def do_btn_work():
    global btn_hold_time
    if btn.value() == 0:
        btn_hold_time = btn_hold_time + 1
        # 按键超过5S:复位
        if (btn_hold_time > 5000):
            while btn.value() == 0:
                led.value(0)
                time.sleep_ms(100)
                led.value(1)
                time.sleep_ms(100)
            machine.reset()
    else:
        btn_hold_time = 0


def test_process():
    while True:
        print('1')
        time.sleep(1)

def main_process():
    while True:
        # do_uart_work()
        # do_btn_work()
        print('2')
        time.sleep_ms(10)

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

# 开机时按键按下:
#   退出运行,进入repl模式
debug = False
if btn.value() == 0:
    time.sleep_ms(100)
    if btn.value() == 0:
        led.value(1)    # led off
        debug = True

# 启动AI模块
# if debug == False:

#     # _thread.start_new_thread(test_process, ())
# #     _thread.stack_size(10*1024)
#     # _thread.start_new_thread(app.do_ai_work, ())
#     # _thread.start_new_thread(main_process, ())
#     # # 串口1处理
#     # do_uart_work()
#     # # 按键处理
#     # do_btn_work()
#     # # 延时1ms
#     # time.sleep_ms(10)

if debug == False:
    while True:
        # 串口1处理
        do_uart_work()
        # 按键处理
        do_btn_work()
        # ai处理
        app.do_ai_work()
        # 延时1ms
        # time.sleep_ms(10)    
        # time.sleep_ms(50)
        # print('main')