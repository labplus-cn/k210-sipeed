
# The MIT License (MIT)
# Copyright (c) 2019, Labplus@Development
# History:
# - Untitled - By: ZKH - 周五 7月 19 2019
# - 增加基础的lcd、sensor操作和K210模型应用、视觉功能 by tangliufeng 2019/09/4

import sensor
import image
import time
import lcd
import KPU as kpu
import json
from machine import UART,Timer,PWM
import gc
import time
import ubinascii
import _thread

#----------------------------------------------------------
def get_buttons_value():
    global btn
    btns = 0
    if (btn.value() == 0):
        btns |= 0x01
    return btns


def builtin_model_init(index):
    """内置模型初始化"""
    global task, builtin, classes, labels
    builtin = index
    gc.collect()

    # yolo
    if model_dict[index].get('type') == 'yolo':
        # camera config
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.run(1)
        # model load
        try:
            task = kpu.load(model_dict[index]['path'])
        except ValueError as e:
            print(e)
            while task.model_addr() != model_dict[index]['addr']:
                gc.collect()
                task = kpu.load(model_dict[index]['path'])
        kpu.init_yolo2(task, 0.5, 0.3, 5, model_dict[index]['anchor'])
        classes = model_dict[index]['classes']
    # MobileNet
    elif model_dict[index].get('type') == 'mobilenet':
        # model load
        try:
            task = kpu.load(model_dict[index]['path'])
        except ValueError as e:
            while task.model_addr() != model_dict[index]['addr']:
                gc.collect()
                task = kpu.load(model_dict[index]['path'])
    # mnist camera config
    if builtin == 3:
        sensor.reset()
        sensor.set_auto_whitebal(False)
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.set_windowing((224, 224))
        sensor.set_hmirror(0)
        sensor.run(1)
    elif builtin == 4:
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)
        sensor.set_windowing((224, 224))
        sensor.run(1)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
# UART2 config:
#   IO11 = UART2.Tx
#   IO10 = UART2.Rx
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
lcd.direction(0x28)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.run(1)

# led on
led.value(0)
light.value(1)
print('system running')

mode = 0
img = image.Image()
cmd = {}
cmd_str, task, builtin, labels = None, None, None, None
classes = []
t1=time.ticks_ms()

def memory_collect():
    gc.collect()
    print('[Memory - free: {}   allocated: {}]'.format(gc.mem_free(), gc.mem_alloc())) 

#----------------------------------------------------------
# 内置模型的参数
builtin_models = {
    # face model
    1: {
        'type': 'yolo',
        "classes": ['face'],
        'path': 0x280000,
        'addr': 2621440,
        'anchor': (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025),

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    },
    # 20classes model
    2: {
        'type': 'yolo',
        "classes": ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'],
        'path': 0x300000,
        'addr': 3145728,
        'anchor': (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52),

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    },
    # mnist model
    3: {
        'type': 'mobilenet',
        'path': 0x200000,
        'addr': 2097152,

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    },
    # 1000classes model
    4: {
        'type': 'mobilenet',
        'path': 0x500000,
        'addr': 5242880,

        'pixformat':sensor.RGB565,
        'framesize':sensor.QVGA,
        'hmirror':1,
        'windows': (320, 240),
    }
}

#------------------------------------------------------------------------------------------------------------
AI_STATE_IDLE = const(0)
AI_STATE_INIT = const(1)
AI_STATE_RUN = const(2)
AI_STATE_DEINIT = const(3)
AI_STATE_MAX = const(3)
AI_MODEL_INDEX_MAX = const(3)

class config():
    state = AI_STATE_IDLE
    model_index = 0
    task = None

#----------------------------------------------------------
def kpu_init_model(new_model):
    global config
    if (config.model_index != new_model):
        if config.task != None:
            kpu.deinit(config.task)
            config.task = None
        # 配置摄像头
        config.model_index = new_model
        sensor.reset()
        model = builtin_models[config.model_index]
        sensor.set_pixformat(model['pixformat'])
        sensor.set_framesize(model['framesize'])
        sensor.set_hmirror(model['hmirror'])
        sensor.set_windowing(model['windows'])
        sensor.run(1)
        sensor.skip_frames(10)
        # 加载模型
        config.task = kpu.load(model['path'])
        if model['type'] == 'yolo':
            kpu.init_yolo2(config.task, 0.5, 0.3, 5, model['anchor'])
        config.state = AI_STATE_IDLE        
        return True
    return False

#---------------------------------------------------
def kpu_run_model():
    global config
    if config.task == None:
        return None
    # 拍照
    img = sensor.snapshot()
    # AI运算
    if builtin_models[config.model_index]['type'] == 'yolo':
        result = kpu.run_yolo2(config.task, img)
    else:
        result = kpu.forward(config.task, img)
    return result

#--------------------------------------------------------
def kpu_deinit_model():
    if config.task == None:
        return False
    kpu.deinit(config.task)
    config.task = None

## do_camera_wrok
def do_camera_wrok():
    '''
    摄像头AI运算
    '''
    global is_camera_thread_alive
    global config
    model = None
    kpu_task = None
    while is_camera_thread_alive:
        # 判断是否切换了模型
        if config.model_sel != config.model_index:
            config.state = AI_STATE_INIT
            config.model_index = config.model_sel
        # 根据模型的需要配置sensor并初始化KPU
        if config.state == AI_STATE_INIT:
            # 卸载已经装载的模型
            if (kpu_task != None):
                kpu.deinit(kpu_task)
                kpu_task = None
                gc.collect()
            # 配置摄像头
            sensor.reset()
            model = builtin_models[config.model_index]
            sensor.set_pixformat(model['pixformat'])
            sensor.set_framesize(model['framesize'])
            sensor.set_hmirror(model['hmirror'])
            sensor.set_windowing(model['windows'])
            sensor.run(1)
            sensor.skip_frames(10)
            # 加载模型
            kpu_task = kpu.load(model['path'])
            if model['type'] == 'yolo':
                kpu.init_yolo2(kpu_task, 0.5, 0.3, 5, model['anchor'])
            config.state = AI_STATE_IDLE
        # 执行KPU AI运算
        if config.state == AI_STATE_RUN:
            # 拍照
            img = sensor.snapshot()
            # AI运算
            if model['type'] == 'yolo':
                result = kpu.run_yolo2(kpu_task, img)
            else:
                result = kpu.forward(kpu_task, img)
            config.ret = result
        
        # 不执行任何动作
        if config.state == AI_STATE_IDLE:
            pass
            # time.sleep_ms(100)
        # 卸载模型
        if config.state == AI_STATE_DEINIT:
            kpu.deinit(kpu_task)
            kpu_task = None
            model = None
            config.state = AI_STATE_IDLE
            config.model_sel = 0
            config.model_index = -1
    print('thread ending')

'''
def exec_cmd(c):
    global config
    # default returns
    ret = {'ret':False,'msg':'invalid setting','code':-1}
    # get command and parameters
    cmd = None
    value = None
    for k, v in c.items():
        if k == 'set':
            cmd = v
        if k == 'value':
            value = v
    # valid command
    if cmd != None and value != None:
        if cmd == 'NEW_STATE':
            ret['ret'] = False
            ret['msg'] = 'value error'
            ret['code'] = -2
            if isinstance(value, int):
                if value in range(0, AI_STATE_MAX + 1):
                    config.state = value
                    ret['ret'] = True
                    ret['msg'] = 'state = %d' % config.state
                    ret['code'] = 0;
        if cmd == 'NEW_MODEL':
            ret['ret'] = False
            ret['msg'] = 'value error'
            ret['code'] = -2
            if isinstance(value, int):
                if value in range(0, AI_MODEL_INDEX_MAX + 1):
                    config.model_sel = value
                    ret['ret'] = True
                    ret['msg'] = 'model = %d' % config.model_sel
                    ret['code'] = 0;            
        if cmd == 'GET_RESULT':
            if config.state == AI_STATE_RUN:
                ret['ret'] = True
                ret['msg'] = config.ret
                ret['code'] = config.model_index
    
    return ret
'''

def exec_cmd(c):
    global config
    # default returns
    ret = {'ret':False,'msg':'invalid setting','code':-1}
    # get command and parameters
    cmd = None
    value = None
    for k, v in c.items():
        if k == 'set':
            cmd = v
        if k == 'value':
            value = v
    # valid command
    if cmd != None and value != None:
        if cmd == 'INIT':
            ret['ret'] = False
            ret['msg'] = 'value error'
            ret['code'] = -2
            if isinstance(value, int):
                if value in range(1, 5):
                    if kpu_init_model(value) == True:
                        ret['ret'] = True
                        ret['msg'] = config.task
                        ret['code'] = value;
        if cmd == 'RUN':
            ret['ret'] = True
            ret['msg'] = kpu_run_model()
            ret['code'] = 0;            
        if cmd == 'DEINIT':
            ret['ret'] = True
            ret['msg'] = kpu_deinit_model()
            ret['code'] = 0;              
    return ret
##-------------------------------------------------------------------------------------
def rpc(type, args):
    '''
    响应串口调用
    '''
    global config
    # call functions
    if type == ord('0'):
        try:
            expression = json.loads(args)     # 解析命令
            func = expression['func']
            g = expression['globals']
            l = expression['locals']
            ret = eval(func, g, l)
            return '0' + json.dumps({'ret':True, 'msg':ret, 'code':0})
        except Exception as e:
            return '0' + json.dumps({'ret':False, 'msg':e, 'code':-3})        # 如果json解析失败/eval运行失败,则返回异常
    # AI 运算
    if type == ord('@'):
        try:
            cmd = json.loads(args)
            return '@' + json.dumps(exec_cmd(cmd))
        except Exception as e:
            return '@' + json.dumps({'ret':False, 'msg':e, 'code':-3})

def do_uart_work():
    '''
    '''
    if uart.any() > 0:
        req = uart.readline()
        t1 = time.ticks_ms()
        print("{0: 8d} uart recieve:\n{1}".format(t1, req))
        rsp = rpc(req[0], req[1:])
        t2 = time.ticks_ms()
        print("{0: 8d} uart respose:\n{1}".format(t2, rsp))

        if rsp != None:
            uart.write(rsp + '\n')
        else:
            uart.write('\n')
##-------------------------------------------------------------------------------------------------------------

is_camera_thread_alive = True
is_uart_thread_alive = True
# 图像处理线程
# _thread.start_new_thread(do_camera_wrok, ())

# 串口处理线程
while True:
    do_uart_work()
    

# _thread.start_new_thread(do_uart_work, ())



def stop():
    global is_camera_thread_alive, is_uart_thread_alive
    is_camera_thread_alive = False
    is_uart_thread_alive = False

