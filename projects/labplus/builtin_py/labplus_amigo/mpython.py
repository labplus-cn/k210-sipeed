# import time
from Maix import GPIO
from fpioa_manager import fm
from board import board_info
from es8374 import *
from msa301 import *
from face_recognization import Face_recognization
from self_learning_classifier import self_learning_classfier
from maix_asr import Asr
import sensor
import lcd
import KPU as kpu
import image
from time import sleep_ms
from micropython import const
from machine import Timer, UART, I2C, PWM
# import framebuf
import ubinascii
import ustruct

# import utime

i2c = I2C(I2C.I2C3, freq=400000, sda=20, scl=23)# amigo

class LED():
    def __init__(self):
        # 三色LED
        fm.register(board_info.LED_R, fm.fpioa.GPIO0, force=True)
        fm.register(board_info.LED_G, fm.fpioa.GPIO3, force=True)
        fm.register(board_info.LED_B, fm.fpioa.GPIO2, force=True)
        self.led_r = GPIO(GPIO.GPIO0, GPIO.OUT)
        self.led_g = GPIO(GPIO.GPIO3, GPIO.OUT)
        self.led_b = GPIO(GPIO.GPIO2, GPIO.OUT)
        self.led_r.value(1)
        self.led_g.value(1)
        self.led_b.value(1)
    
    def SwitchLED(self, mode=0, color=0):
        if(color==0 and mode==1):
            self.led_r.value(0)
            self.led_g.value(1)
            self.led_b.value(1)
        elif(color==1 and mode==1):
            self.led_r.value(1)
            self.led_g.value(0)
            self.led_b.value(1)
        elif(color==2 and mode==1):
            self.led_r.value(1)
            self.led_g.value(1)
            self.led_b.value(0)
        elif(mode==0):
            self.led_r.value(1)
            self.led_g.value(1)
            self.led_b.value(1)
    def releaseResource(self):
        pass

class FlashLight():
    def __init__(self):
        #闪光灯
        fm.register(board_info.LED_W, fm.fpioa.GPIO4, force=True)
        self.led_w = GPIO(GPIO.GPIO4, GPIO.OUT)
        self.led_w.value(1)

    def Switch(self, mode=0):
        if(mode==1):
            self.led_w.value(0)
        elif(mode==0):
            self.led_w.value(1)

    def releaseResource(self):
        fm.unregister(board_info.LED_W)

'''
boot按钮
'''
# boot按钮
class BootButton():
    def __init__(self, func):
        self.func = func
        fm.register(board_info.BOOT_KEY, fm.fpioa.GPIOHS0, force=True)
        self.key=GPIO(GPIO.GPIOHS0, GPIO.IN, GPIO.PULL_NONE)
        self.key.irq(self.irq_event, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)

    def irq_event(self, pin_num):
        if(pin_num.value()==0):
            self.func()


""" 
Amigo驱动
"""
class Plus1956(object):
    def __init__(self):
        try:
            self.led = LED()
            self.flashLight = FlashLight()
            self.sensor = sensor
            self.lcd = lcd
            self.kpu = kpu
            self.lcd.init()
            self.msa301()
        except:
            raise('init error')

    def key_init(self, func):
        # 按钮
        self.boot_key = BootButton(func)
    
    def msa301(self):
        try:
            self.accel = MSA301()
        except:
            raise('init MSA301 error')

    def image_init(self):
        # 图像
        self.image = image.Image()

    def image_del(self):
        """销毁image对象"""
        del self.image

    def asr_init(self):
        self.asr = Asr()

    def asr_release(self):
        if self.asr != None:
            self.asr.asr_release()

    def face_recognize_init(self, face_num, accuracy, names):
        self.fcr = Face_recognization(face_num=face_num, accuracy=accuracy, names=names)

    def self_learning_classifier_init(self, class_num, sample_num, class_names=["class.1", "class.2", "class.3"]):
        self.slc = self_learning_classfier(class_num=class_num, sample_num=sample_num, class_names=class_names)
    

class PinMode(object):
    IN = 1
    OUT = 2
    PWM = 3
    ANALOG = 4
    OUT_DRAIN = 5

# 7,9,17,19,20,23
pins_amigo = (0, 0, 0, 0, 0, 0, 0, 63, 0, 33, 0, 0, 0, 0, 0, 0, 0, 41, 0, 43, 44, 0, 0, 47)


'''
class GPIO(ID, MODE, PULL, VALUE)

ID： 使用的 GPIO 引脚(一定要使用 GPIO 里带的常量来指定)

MODE： GPIO模式

• GPIO.IN就是输入模式

• GPIO.OUT就是输出模式

PULL： GPIO上下拉模式

• GPIO.PULL_UP 上拉

​• GPIO.PULL_DOWN 下拉

​• GPIO.PULL_NONE 即不上拉也不下拉
'''

class MPythonPin():
    def __init__(self, pin, mode=PinMode.IN, pull=GPIO.PULL_NONE):
        if mode not in [PinMode.IN, PinMode.OUT, PinMode.PWM]:
            raise TypeError("mode must be 'IN, OUT, PWM, ANALOG,OUT_DRAIN'")
        if pin == 4:
            raise TypeError("P4 is used for light sensor")
        if pin == 10:
            raise TypeError("P10 is used for sound sensor")
        try:
            self.fm = fm
            self.fm.register(pin, pins_amigo[pin])
        except IndexError:
            raise IndexError("Out of Pin range")
        if mode == PinMode.IN:
            self.Pin = GPIO(pin, GPIO.IN, pull)
            # self.Pin=GPIO(GPIO.GPIOHS23,GPIO.IN)
        if mode == PinMode.OUT:
            # if pin in [2, 3]:
            #     raise TypeError('OUT not supported on P%d' % pin)
            self.Pin = GPIO(pin, GPIO.OUT, pull)
        # if mode == PinMode.OUT_DRAIN:
        #     if pin in [2, 3]:
        #         raise TypeError('OUT_DRAIN not supported on P%d' % pin)
        #     self.Pin = GPIO(pin, Pin.OPEN_DRAIN, pull)
        if mode == PinMode.PWM:
            # if pin not in [7, 9, 20, 23, 17, 19]:
            #     raise TypeError('PWM not supported on P%d' % pin)
            # self.pwm = PWM(Pin(self.id), duty=0)
            tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PWM)
            self.pwm = PWM(tim, freq=1000, duty=0, pin=pin, enable=True)

        # if mode == PinMode.ANALOG:
        #     if pin not in [0, 1, 2, 3, 4, 10]:
        #         raise TypeError('ANALOG not supported on P%d' % pin)
        #     self.adc = ADC(Pin(self.id))
        #     self.adc.atten(ADC.ATTN_11DB)
        self.mode = mode

    def irq(self, handler=None, trigger=GPIO.IRQ_RISING):
        if not self.mode == PinMode.IN:
            raise TypeError('the pin is not in IN mode')
        return self.Pin.irq(handler, trigger)

    def read_digital(self):
        if not self.mode == PinMode.IN:
            raise TypeError('the pin is not in IN mode')
        return self.Pin.value()

    def write_digital(self, value):
        if self.mode not in [PinMode.OUT, PinMode.OUT_DRAIN]:
            raise TypeError('the pin is not in OUT or OUT_DRAIN mode')
        self.Pin.value(value)

    # def read_analog(self):
    #     if not self.mode == PinMode.ANALOG:
    #         raise TypeError('the pin is not in ANALOG mode')
    #     return self.adc.read()
        
    def write_analog(self, duty=0, freq=1000):
        if not self.mode == PinMode.PWM:
            raise TypeError('the pin is not in PWM mode')
        self.pwm.freq(freq)
        self.pwm.duty(duty)
        print('pwm.duty:')
        print(self.pwm.duty())

def numberMap(inputNum, bMin, bMax, cMin, cMax):
    outputNum = 0
    outputNum = ((cMax - cMin) / (bMax - bMin)) * (inputNum - bMin) + cMin
    return outputNum