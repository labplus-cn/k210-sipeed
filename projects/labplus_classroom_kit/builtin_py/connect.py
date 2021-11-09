
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
import machine
from machine import UART,Timer,PWM
from Maix import FPIOA, GPIO
import gc
import time
import ubinascii
from fpioa_manager import fm
gc.collect()

#UART2 config:
# IO6 = UART2.Tx
# IO7 = UART2.Rx
fm.register(6, fm.fpioa.UART2_TX)
fm.register(7, fm.fpioa.UART2_RX)
uart = machine.UART(machine.UART.UART2)
uart.init(1152000, 8, None, 1, timeout=1024, read_buf_len=2048)

# fm.register(20, fm.fpioa.GPIOHS7)
# fm.register(21, fm.fpioa.GPIOHS8)
motor_tim_P = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PWM)
motor_tim_N = Timer(Timer.TIMER0, Timer.CHANNEL1, mode=Timer.MODE_PWM)
pwm_mt_P = PWM(motor_tim_P, 1000, 0, 21, enable=False)
pwm_mt_N = PWM(motor_tim_N, 1000, 0, 20, enable=False)

#buttons:
# IO12(BTN_LEFT)    = GPIOHS0
# IO13(BTN_RIGHT)   = GPIOHS1
# IO14(BTN_UP)      = GPIOHS2
# IO15(BTN_DOWN)    = GPIOHS3
# IO24(BTN_OK)      = GPIOHS4
fm.register(12, fm.fpioa.GPIOHS0)
fm.register(13, fm.fpioa.GPIOHS1)
fm.register(14, fm.fpioa.GPIOHS2)
fm.register(15, fm.fpioa.GPIOHS3)
fm.register(24, fm.fpioa.GPIOHS4)
btn_left = GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_NONE)
btn_right = GPIO(GPIO.GPIOHS1, GPIO.IN, GPIO.PULL_NONE)
btn_up = GPIO(GPIO.GPIOHS2, GPIO.IN, GPIO.PULL_NONE)
btn_down = GPIO(GPIO.GPIOHS3, GPIO.IN, GPIO.PULL_NONE)
btn_ok = GPIO(GPIO.GPIOHS4, GPIO.IN, GPIO.PULL_NONE)
#----------------------------------------------------------
buttons_new_state = False
buttons = 0
#

# def buttons_irq_handler(GPIO, number):
#     buttons_new_state = True
#     if GPIO.value() == 1:
#         print('button_%d release\n' % number)
#     else:
#         print('button_%d pressed\n' % number)

def get_buttons_value():
    global btn_left, btn_right, btn_up, btn_down, btn_ok
    btns = 0
    if (btn_left.value() == 0):
        btns |= 0x01
    if (btn_right.value() == 0):
        btns |= 0x02
    if (btn_up.value() == 0):
        btns |= 0x04
    if (btn_down.value() == 0):
        btns |= 0x08
    if (btn_ok.value() == 0):
        btns |= 0x10
    return btns

#-------------------------------------------------------
# IO18(US.TRIG)     = GPIOHS5
# IO19(US.ECHO)     = GPIOHS6
fm.register(18, fm.fpioa.GPIOHS5)
fm.register(19, fm.fpioa.GPIOHS6)
us_trig = GPIO(GPIO.GPIOHS5, GPIO.OUT)
us_echo = GPIO(GPIO.GPIOHS6, GPIO.IN, GPIO.PULL_NONE)

us_echo_start = 0
us_distance = 0
# 定时器2回调函数,100mS周期
#   发送超声波传感器触发信号(10us高电平脉冲),已启动超声测量


def on_timer2(timer):
    global us_trig
    us_trig.value(1)
    us_trig.value(0)


us_trig_timer = Timer(Timer.TIMER1, Timer.CHANNEL0,
                      mode=Timer.MODE_PERIODIC, period=100, callback=on_timer2)
# 超声波回波信号IO中断处理(边沿触发)
#  上升沿:记录当前时刻
#  下降沿:计算高电平持续时间,转换为距离 d = (t * 340m/s)/2


def us_echo_irq_handler(GPIO):
    global us_is_busy, us_echo_start, us_distance, us_lock
    if GPIO.value() == 1:
        us_echo_start = time.ticks_us()
    else:
        us_distance = time.ticks_diff(time.ticks_us(), us_echo_start)
        us_distance = max(min(us_distance, 20*1000), 0)
        us_distance = us_distance / 1000 / 1000 * 340 / 2 * 100


us_echo.irq(us_echo_irq_handler, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)

model_dict = {
    # face model
    1: {
        'type': 'yolo',
        "classes": ['face'],
        'path': 0x280000,
        'addr': 2621440,
        'anchor': (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)
    },
    # 20classes model
    2: {
        'type': 'yolo',
        "classes": ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor'],
        'path': 0x300000,
        'addr': 3145728,
        'anchor': (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52)
    },
    # mnist model
    3: {
        'type': 'mobilenet',
        'path': 0x200000,
        'addr': 2097152,
    },
    # 1000classes model
    4: {
        'type': 'mobilenet',
        'path': 0x500000,
        'addr': 5242880,
    }
}


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
# 串口发送

def uart_write(js):
    uart.write(json.dumps(js) + '\n')

def Response(value=0):
    uart_write({'RESP': value})

# Power on lcd/camera config
lcd.init()
lcd.direction(0x28)
sensor.reset()
sensor.set_pixformat(sensor.RGB565)
sensor.set_framesize(sensor.QVGA)
sensor.run(1)
sensor.skip_frames(20)

mode = 0
img = image.Image()
cmd = {}
cmd_str, task, builtin, labels = None, None, None, None
classes = []
t1=time.ticks_ms()

def memory_collect():
    gc.collect()
    print('[Memory - free: {}   allocated: {}]'.format(gc.mem_free(), gc.mem_alloc())) 

while True:
    # 从串口接收控制指令
    if uart.any() > 0:
        try:
            r = None
            r = uart.readline()
            r = r.strip()
            # print("UART_Refv:%s" % r)
            while uart.readline():
                pass
            cmd = json.loads(r)
           
        except Exception as e:
            print(e, r)
            continue
        else:
            try:
                if cmd and isinstance(cmd, dict):
                    for key, value in cmd.items():
                        # 获取按键值
                        if key == 'GET_KEYS':
                            btns = get_buttons_value()
                            Response(btns)
                        # 获取超声波传感器测量值
                        elif key == 'GET_DISTANCE':
                            distance = us_distance
                            Response(distance)
                        # 控制马达
                        elif key == 'SET_MOTOR':
                            motor_speed = cmd['SET_MOTOR']
                            motor_speed = min(100, motor_speed)
                            motor_speed = max(-100, motor_speed)
                            if motor_speed == 0:
                                pwm_mt_P.disable()
                                pwm_mt_N.disable()
                            elif motor_speed < 0:
                                pwm_mt_P.enable()
                                pwm_mt_N.enable()
                                pwm_mt_P.duty(0)
                                pwm_mt_N.duty(-motor_speed)
                            elif motor_speed > 0:
                                pwm_mt_P.enable()
                                pwm_mt_N.enable()
                                pwm_mt_P.duty(motor_speed)
                                pwm_mt_N.duty(0)
                            Response(motor_speed)
                        elif key == 'FILE_OPEN':
                            file = open(*value)
                            Response(file.seek(0,2))
                            file.seek(0,0)
                        elif key == 'FILE_READ':
                            buf = file.read(value)
                            buf =ubinascii.b2a_base64(buf).strip()
                            Response(buf)
                            del buf
                        elif key == 'FILE_WRITE':
                            len = file.write(ubinascii.a2b_base64(value))
                            Response(len) 
                        elif key == 'FILE_CLOSE':
                            file.close()
                            Response(0)
                        # 重启K210
                        elif key == 'RESET':
                            machine.reset()
                        # 选择模型
                        elif key == 'SELE_MOD':
                            builtin_model_init(value)
                            Response()
                        # yolo探测
                        elif key == 'DET_YO':
                            img = sensor.snapshot()
                            if not task:
                                raise TypeError('Not load model!')
                            code = kpu.run_yolo2(task, img)
                            if code:
                                Response(code)
                                for i in code:
                                    img.draw_rectangle(i.rect())
                                    lcd.display(img)
                                    for i in code:
                                        lcd.draw_string(
                                            i.x(), i.y(), classes[i.classid()], lcd.RED, lcd.WHITE)
                                        lcd.draw_string(
                                            i.x(), i.y()+12, '%0.3f' % i.value(), lcd.RED, lcd.WHITE)
                            else:
                                lcd.display(img)
                        # MobileNet神经网络
                        elif key == 'PRE_NET':
                            if builtin == 4: 
                                f = open('/sd/labels.txt', 'r')
                                labels = f.readlines()
                                labels = [i.strip() for i in labels]
                                f.close()
                            if builtin == 0 or builtin == 4:
                                img = sensor.snapshot()
                                fmap = kpu.forward(task, img)
                                plist = fmap[:]
                                pmax = max(plist)
                                max_index = plist.index(pmax)
                                lcd.display(img, oft=(0, 0))
                                if builtin == 0:
                                    resp = {'RET_PRE_NET': plist}
                                elif builtin == 4:
                                    lcd.draw_string(0, 224, "%.2f:%s                            " % (
                                    pmax, labels[max_index]))
                                    resp = {'RET_PRE_NET': {
                                        'index': max_index, 'value': pmax}}
                                Response(resp)
                                if builtin ==4:
                                    del f,labels
                                del pmax, max_index,resp,fmap,plist
                                gc.collect()
                            # Mnist
                            elif builtin == 3:
                                img = sensor.snapshot()
                                img = img.copy(((224-28*2)//2, (224-28*2)//2, 28*2, 28*2))
                                img2 = img.resize(28, 28)
                                img2 = img2.to_grayscale(1)
                                img2.invert()
                                img2.strech_char(1)
                                img2.binary([(0, 65)], invert=1)
                                img_lcd = image.Image()
                                img_lcd.draw_image(img, 0, 0, x_scale=2.0, y_scale=2.0)
                                img_lcd.draw_image(img2, 28*4+20, 0, x_scale=2.0, y_scale=2.0)
                                img2.pix_to_ai()
                                fmap = kpu.forward(task, img2)
                                del img2 
                                gc.collect()
                                plist = fmap[:] 
                                pmax = max(plist)
                                max_index = plist.index(pmax)
                                for i in range(0, 10):
                                    cc = int(plist[i]*256)
                                    a = img_lcd.draw_rectangle(
                                        i*16, 28*2+102, 16, 16, color=(cc, cc, cc), thickness=1, fill=True)
                                    a = img_lcd.draw_string(
                                        i*16+5, 28*2+102+16, str(i), color=(255, 255, 255), scale=2, mono_space=False)
                                img_lcd.draw_cross(28*2, 28*2, size=42)
                                img_lcd.draw_rectangle(14, 14, 28*3, 28*3, color=(255, 255, 255))
                                img_lcd.draw_string(200, 28*2+102+16, "%d: %.3f" % (max_index, pmax),
                                                    color=(255, 0, 0), scale=2, mono_space=False)  
                                lcd.display(img_lcd)
                                Response(plist)
                                del img_lcd,img,plist,fmap
                                gc.collect()

                        # 自定义加载模型
                        elif key == 'LOD_MOD':
                            builtin = 0
                            classes = value.get('classes')
                            try:
                                task = kpu.load(value.get('path'))
                            except ValueError as e:
                                print(e)
                                gc.collect()
                                task = kpu.load(value.get('path'))
                            if value.get('model_type') == 1:
                                kpu.init_yolo2(task, 0.5, 0.3, 5,
                                                value.get('anchor'))
                            Response()
                        # yolo释放
                        elif key == 'DINT_YO':
                            kpu.deinit(task)
                            gc.collect()
                            Response()
                        # net释放
                        elif key == 'DINT_NET':
                            del task
                            gc.collect()
                            Response()
                        # 照相
                        elif key == 'SNAPSHOT':
                            img = sensor.snapshot()
                            Response()
                        # 重启camera
                        elif key == 'CAM_RST':
                            sensor.reset()
                            sensor.set_framesize(sensor.QVGA)
                            Response()
                        # 启动cameras
                        elif key == 'CAM_RUN':
                            sensor.run(value)
                            Response()
                        # sensor.set_pixformat
                        elif key == 'CAM_SET_PF':
                            sensor.set_pixformat(value)
                            Response()
                        # sensor.set_contrast
                        elif key == 'CAM_SET_CRA':
                            sensor.set_contrast(value)
                            Response()
                        # sensor.set_brightness
                        elif key == 'CAM_SET_BRG':
                            sensor.set_brightness(value)
                            Response()
                        # sensor.set_saturation
                        elif key == 'CAM_SET_SAT':
                            sensor.set_saturation(value)
                            Response()
                        # sensor.set_auto_gain
                        elif key == 'CAM_AUTO_GAIN':
                            sensor.set_auto_gain(*value[0], **value[1])
                            Response()
                        # sensor.set_auto_whitebal
                        elif key == 'CAM_AUTO_WBAL':
                            sensor.set_auto_whitebal(value)
                            Response()
                        # sensor.set_windowing
                        elif key == 'CAM_SET_WIN':
                            sensor.set_windowing(value)
                            Response()
                        # sensor.set_hmirror
                        elif key == 'CAM_SET_HM':
                            sensor.set_hmirror(value)
                            Response()
                        # sensor.set_vflip
                        elif key == 'CAM_SET_VF':
                            sensor.set_vflip(value)
                            Response()
                        elif key == 'CAM_SKIP_FRM':
                            sensor.skip_frames(*value[0], **value[1])
                            Response()
                        # lcd init
                        elif key == 'LCD_INT':
                            lcd.init(*value[0], **value[1])
                            lcd.direction(0x28)
                            Response()
                        # lcd显示
                        elif key == 'LCD_DISP':
                            lcd.display(img, **value)
                            Response()
                        # lcd clear
                        elif key == 'LCD_CLR':
                            lcd.clear(value.get('color'))
                            Response()
                        # lcd draw_string
                        elif key == 'LCD_STR':
                            lcd.draw_string(*value)
                            Response()
                        # load image
                        elif key == 'IMG_LOD':
                            img = image.Image(*value[0], **value[1])
                            Response()
                        # image width
                        elif key == 'IMG_WID':
                            uart_write({'RET_IMG_WID': str(img.width())})
                            Response()
                        # image hight
                        elif key == 'IMG_HIG':
                            uart_write({'RET_IMG_HIG': str(img.hight())})
                            Response()
                        # image format
                        elif key == 'IMG_FRM':
                            uart_write({'RET_IMG_FRM': str(img.format())})
                            Response()
                        # image size
                        elif key == 'IMG_SIZE':
                            uart_write({'RET_IMG_SIZE': str(img.size())})
                            Response()
                        # image.get_pixel
                        elif key == 'IMG_GET_PIX':
                            Response(img.get_pixel(*value[0], **value[1]))
                        # image.set_pixel
                        elif key == 'IMG_SET_PIX':
                            img.set_pixel(*value[0], **value[1])
                            Response()
                        # image.mean_pool
                        elif key == 'IMG_MEAN_P':
                            img.mean_pool(*value[0], **value[1])
                            Response()
                        # image.to_grayscale
                        elif key == 'IMG_TO_GRAY':
                            img = img.to_grayscale(1)
                            Response()
                        # image.to_rainbow
                        elif key == 'IMG_TO_RB':
                            img = img.to_rainbow(1)
                            Response()
                        # image.copy
                        elif key == 'IMG_CPY':
                            img = img.copy(*value[0], **value[1])
                            Response()
                        # image.save
                        elif key == 'IMG_SAVE':
                            img.save(*value[0], **value[1])
                            Response()
                        # image.clear
                        elif key == 'IMG_CLR':
                            img.clear()
                            Response()
                        # image.draw_line
                        elif key == 'IMG_DRW_LN':
                            img.draw_line(*value[0], **value[1])
                            Response()
                        # image.draw_rectangle
                        elif key == 'IMG_DRW_RECTANG':
                            img.draw_rectangle(*value[0], **value[1])
                            Response()
                        # image.draw_circle
                        elif key == 'IMG_DRW_CIR':
                            img.draw_circle(*value[0], **value[1])
                            Response()
                        # image.draw_string
                        elif key == 'IMG_DRW_STR':
                            img.draw_string(*value[0], **value[1])
                            Response()
                        # image.draw_cross
                        elif key == 'IMG_DRW_CRS':
                            img.draw_cross(*value[0], **value[1])
                            Response()
                        # image.draw_arrow
                        elif key == 'IMG_DRW_ARR':
                            img.draw_arrow(*value[0], **value[1]) 
                            Response()
                        # image.binary
                        elif key == 'IMG_BINARY':
                            img.binary(*value[0], **value[1])
                            Response()
                        # image.invert
                        elif key == 'IMG_INVERT':
                            img.invert()
                            Response()
                        # image.erode
                        elif key == 'IMG_ERODE':
                            img.erode(*value[0], **value[1])
                            Response()
                        # image.dilate
                        elif key == 'IMG_DIL':
                            img.dilate(*value[0], **value[1])
                            Response()
                        # image.negate
                        elif key == 'IMG_NEG':
                            img.negate(*value[0], **value[1])
                            Response()
                        # image.mean
                        elif key == 'IMG_MEAN':
                            img.mean(*value[0], **value[1])
                            Response()
                        # image.mode
                        elif key == 'IMG_MODE':
                            img.mode(*value[0], **value[1])
                            Response()
                        # image.median
                        elif key == 'IMG_MEDIAN':
                            img.median(*value[0], **value[1])
                            Response()
                        # image.midpoint
                        elif key == 'IMG_MIDP':
                            img.midpoint(*value[0], **value[1])
                            Response()
                        # image.cartoon
                        elif key == 'IMG_CART':
                            img.cartoon(*value[0], **value[1])
                            Response()
                        # image.conv3
                        elif key == 'IMG_CONV':
                            img.conv3(*value[0], **value[1])
                            Response()
                        # image.gaussian
                        elif key == 'IMG_GAUS':
                            img.gaussian(*value[0], **value[1])
                            Response()
                        # image.bilateral
                        elif key == 'IMG_BIL':
                            img.bilateral(*value[0], **value[1])
                            Response()
                        # image.linpolar
                        elif key == 'IMG_LINP':
                            img.linpolar(*value[0], **value[1])
                            Response()
                        # image.logpolar
                        elif key == 'IMG_LOGP':
                            img.logpolar(*value[0], **value[1])
                            Response()
                        # image.rotation_corr
                        elif key == 'IMG_ROT_COR':
                            img.rotation_corr(*value[0], **value[1])
                            Response()
                        # image.find_blobs
                        elif key == 'IMG_FID_BLOB':
                            blobs = img.find_blobs(*value[0], **value[1])
                            Response(blobs)
            except Exception as e:
                resp = {'ERROR': str(e)}
                print(resp)
                uart.write(json.dumps(resp) + '\n')
                continue

        time.sleep_ms(1)


