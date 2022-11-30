import time
import KPU as kpu
import sensor, lcd, image
from machine import I2C
from machine import UART
from Maix import GPIO, FPIOA
from board import button, LED
from display import *
from speech_recognizition import speech_recognize
from face_recognization import Face_recognization
from self_learning_classifier import Self_learning_classifier
from qrcode import QRCode_recognization
from color import color_recognization
from fpioa_manager import fm
from xgo import XGO
from modules import ws2812
class Button():
    def __init__(self):
        fm.register(16, fm.fpioa.GPIOHS16, force=True)
        fm.register(17, fm.fpioa.GPIOHS17, force=True)
        self.key_a=GPIO(GPIO.GPIOHS16, GPIO.IN, GPIO.PULL_UP)
        self.key_b=GPIO(GPIO.GPIOHS17, GPIO.IN, GPIO.PULL_UP)

    def irq_key_a(self, func):
        self.func_a = func
        self.key_a.irq(self.irq_event_a, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)

    def irq_key_b(self, func):
        self.func_b = func
        self.key_b.irq(self.irq_event_b, GPIO.IRQ_BOTH, GPIO.WAKEUP_NOT_SUPPORT, 7)

    def irq_event_a(self, pin_num):
        if(pin_num.value()==0):
            time.sleep_ms(30)
            if(pin_num.value()==0):
                self.func_a()
    
    def irq_event_b(self, pin_num):
        if(pin_num.value()==0):
            time.sleep_ms(30)
            if(pin_num.value()==0):
                self.func_b()

""" 
-------------------------------------------------------------------------------------------------------
- 盛思OWL 掌控GO初始化
-------------------------------------------------------------------------------------------------------
"""

# LCD
lcd.init(freq=15000000, invert=1)
try:
    background = image.Image('/flash/startup.jpg', copy_to_fb=True)
    lcd.display(background)
    del background
except:
    lcd.clear(lcd.BLUE)
    lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "labplus AI Camera", lcd.WHITE, lcd.BLUE) 

class AI_Camera_GO(object):
    def __init__(self):
        try:
            self.rgb_led = ws2812(34,2)
            self.sensor = sensor
            self.lcd = lcd
            self.kpu = kpu

            # LCD
            # self.lcd.init(freq=15000000, invert=1)
            try:
                background = image.Image('/flash/startup.jpg', copy_to_fb=True)
                self.lcd.display(background)
                del background
            except:
                self.lcd.clear(self.lcd.BLUE)
                self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "labplus AI Camera", self.lcd.WHITE, self.lcd.BLUE) 

            # Camera
            try:
                self.sensor.reset(choice=1)  
                # self.sensor.reset(choice=2)  
            except Exception as e:
                self.lcd.clear((0, 0, 255))
                self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_vflip(1)
            self.sensor.set_hmirror(1)
            self.sensor.run(1)

            # button
            self.btn = Button()
            # self.btn_A = button(16)
            # self.btn_B = button(17)
            #XGO 
            
            # fm.register(33, fm.fpioa.UARTHS_RX, force=True)
            # fm.register(32, fm.fpioa.UARTHS_TX, force=True)
            # self.uart_DOG = UART(UART.UARTHS, 115200, 8, 0, 0, timeout=1000, read_buf_len=4096)
            # self.dog = XGO(UART.UARTHS) 

            fm.register(33, fm.fpioa.UART2_RX, force=True)
            fm.register(32, fm.fpioa.UART2_TX, force=True)
            self.uart_DOG = UART(UART.UART2, 115200, 8, 0, 0, timeout=1000, read_buf_len=4096)
            self.dog = XGO(UART.UART2) 
            
        except:
            raise('init error')
    
    def DispChar(self, s, x, y, img, color):
        Draw_CJK_String(s,x,y,img,color)

    def show_expression(self, num):
        try:
            background = image.Image('/flash/dog/dog{}.jpg'.format(num), copy_to_fb=True)
            self.lcd.display(background)
            del background
        except:
            background = image.Image('/flash/startup.jpg', copy_to_fb=True)
            self.lcd.display(background)
            del background 

    def rgb_display(self, num, color):
        self.rgb_led.set_led(num, color)
        self.rgb_led.display()

    def rgb_clear(self):
        self.rgb_display(0, (0,0,0))
        self.rgb_display(1, (0,0,0))

    def image_init(self):
        # 图像
        self.image = image.Image()

    def image_del(self):
        """销毁image对象"""
        del self.image
    
    def change_camera(self, choice):
        '''
            切换摄像头
        '''
        try:
            self.sensor.reset(choice=choice)  
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        self.sensor.set_framesize(self.sensor.QVGA)
        self.sensor.set_pixformat(self.sensor.RGB565)
        if(choice==1):
            self.sensor.set_vflip(1)
        else:
            self.sensor.set_vflip(0)
        self.sensor.set_hmirror(1)
        self.sensor.run(1)

    def asr_init(self):
        self.asr = speech_recognize()

    def asr_release(self):
        if self.asr != None:
            self.asr.asr_release()

    def face_recognize_init(self, choice=1, face_num=3, accuracy=80, names=["ID.1", "ID.2", "ID.3"]):
        self.fcr = Face_recognization(kpu=self.kpu, lcd=self.lcd, sensor=self.sensor, choice=choice, face_num=face_num, accuracy=accuracy, names=names)

    def self_learning_classifier_init(self, choice=1, class_num=3, sample_num=15, class_names=["class.1", "class.2", "class.3"]):
        self.slc = Self_learning_classifier(sensor=self.sensor, choice=choice, class_num=class_num, sample_num=sample_num, class_names=class_names)

    def qrcode_recognization_init(self, choice=1):
        self.qrcode  = QRCode_recognization(choice=choice)

    def color_recognization_init(self, choice=1):
        self.color_r = color_recognization(choice=choice)


