import time
import machine
from machine import I2C, PWM, SPI, Timer, UART
from Maix import GPIO, FPIOA
import KPU as kpu
import sensor, lcd, image
from board import button, LED
from display import *
from modules import ws2812
import gc

from fpioa_manager import fm
# rgb_led = ws2812(34,2)
from self_learning_classifier import *
from face_recognization import *
from mnist import *
from yolo_detect import *
from face_detect import *
from speech_recognizition import speech_recognize
from color import *
from qrcode import *
from guidepost import *
from kpu_kmodel import *
from track import *


""" 
-------------------------------------------------------------------------------------------------------
- 盛思OWL初始化
-------------------------------------------------------------------------------------------------------
"""

Order ={
    'lcd':['clear'],

}

DEFAULT_MODE = 1
MNIST_MODE = 2 #
OBJECT_RECOGNIZATION_MODE = 3 #
FACE_DETECTION_MODE = 4
FACE_RECOGNIZATION_MODE = 5
SELF_LEARNING_CLASSIFIER_MODE = 6 #
COLOE_MODE = 7
QRCODE_MODE = 8
SPEECH_RECOGNIZATION_MODE = 9
GUIDEPOST_MODE = 10 #清华教材交通标志识别
KPU_MODEL_MODE = 11 #自定义模型
TRACK_MODE= 12


class AICamera(object):
    class K210:
        def __init__(self):
            #k210模式及默认值
            self.cmd = []
            self.mode = DEFAULT_MODE
            self.sensor_choice = 1
            self.flag_mnist_recognize = 0 #mnist
            self.flag_add = 0
            self.flag_fac_recognize = 0
            self.flag_yolo_recognize = 0
            self.flag_face_detection = 0
            self.flag_asr_recognize = 0
            self.flag_slc_recognize = 0
            self.flag_slc_add = 0
            self.slc_mode_name = ''
            self.flag_slc_mode_save = 0
            self.flag_slc_mode_load = 0
            #
            self.flag_color_add = 0
            self.flag_color_recognize = 0
            #
            self.flag_qrcode_add = 0
            self.flag_qrcode_recognize = 0
            #
            self.flag_guidepost_recognize = 0
            #KPU
            self.kpu_kmodel_name = ''
            self.flag_kpu_kmodel_init = 0
            self.flag_kpu_recognize=0
            #
            self.flag_track_recognize=0
            

    def __init__(self):
        fm.register(32, fm.fpioa.UART2_TX, force=True)
        fm.register(33, fm.fpioa.UART2_RX, force=True)
        # self.uart = UART(UART.UART2, 115200, 8, 0, 0, timeout=1000, read_buf_len=4096)
        self.uart = UART(UART.UART2)
        self.uart.init(1152000, 8, None, 1, timeout=1000, read_buf_len=4096)
        time.sleep(0.1)
        
        # RGB
        self.rgb_led = ws2812(34,2)
        try:
            self.sensor = sensor
        except:
            self.lcd.clear(lcd.BLUE)
            self.lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "init sensor err!", lcd.WHITE, lcd.BLUE) 
        self.lcd = lcd
        self.kpu = kpu
        self.lcd.init(freq=15000000, invert=1)
        try:
            background = image.Image('/flash/startup.jpg', copy_to_fb=True)
            self.lcd.display(background)
            del background
        except:
            self.lcd.clear(lcd.BLUE)
            self.lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "labplus AI Camera", lcd.WHITE, lcd.BLUE) 
        
        # Camera
        self.change_camera(1)

        # Image
        # self.img = image.Image()

        # button
        self.btn_A = button(16)
        self.btn_B = button(17)
        time.sleep(0.2)

        # new
        self.k210 = self.K210()
        self.slc = None
        self.asr = None
        self.yolo_detect = None
        self.face_detect = None
        self.color = None
        self.mnist = None
        self.guidepost = None
        self.track = None
      
        #开始串口监听
        self.uart_listen()

    def CheckCode(self, tmp):
        ''' 校验和 取低8位'''
        sum = 0
        for i in range(len(tmp)):
            sum += tmp[i]
        return sum & 0xFF    

    def AI_Uart_CMD(self, data_type, cmd, cmd_type, cmd_data=[0, 0, 0, 0, 0, 0]):
        check_sum = 0
        CMD_TEMP = [0xBB, 0xAA, data_type, cmd, cmd_type]
        CMD_TEMP.extend(cmd_data)
        for i in range(6-len(cmd_data)):
            CMD_TEMP.append(0)
        for i in range(len(CMD_TEMP)):
            check_sum = check_sum+CMD_TEMP[i]
        #print_x16(CMD_TEMP)
        # lcd.draw_string(0,200, 'send:'+str(CMD_TEMP), lcd.WHITE, lcd.BLUE)
        self.uart.write(bytes(CMD_TEMP))
        self.uart.write(bytes([check_sum & 0xFF]))
        
    def AI_Uart_CMD_String(self,cmd=0x00, cmd_type=0x00, cmd_data=[0, 0, 0], str_len=0, str_buf=''):
        check_sum = 0
        CMD = [0xBB, 0xAA, 0x02, cmd, cmd_type]
        CMD.extend(cmd_data)
        for i in range(3-len(cmd_data)):
            CMD.append(0)
        for i in range(len(CMD)):
            check_sum = check_sum+CMD[i]
        # print_x16(CMD)
        self.uart.write(bytes(CMD))
        str_temp = bytes(str_buf, 'utf-8')
        str_len = len(str_temp)
        self.uart.write(bytes([str_len]))
        self.uart.write(str_temp)
        # lcd.draw_string(0,50, 'str:'+str(str_temp), lcd.WHITE, lcd.BLUE)
        for i in range(len(str_temp)):
            check_sum = check_sum + str_temp[i]
        self.uart.write(bytes([check_sum & 0xFF]))   
    
    def print_x16(self,date):
        for i in range(len(date)):
            print('{:2x}'.format(date[i]),end=' ')
        print('')

    def send_to_zkb_init(self): #tx
        while True:
            time.sleep_ms(10)
            if(self.uart.any()):
                head=self.uart.read(2)
                # lcd.draw_string(0,50, 'head:'+str(head), lcd.WHITE, lcd.BLUE)
                if(head and head[0]==0xAA and head[1]==0xBB):
                    cmd_type = self.uart.read(1)
                    if(cmd_type[0]==0x01):
                        res=self.uart.read(9)
                        if(res and res[0]==0x01 and res[1]==0x00):
                            self.AI_Uart_CMD(0x01,0x01,0x00)
                        elif(res and res[0]==0x01 and res[1]==0x01):
                            self.AI_Uart_CMD(0x01,0x01,0x01)
                            time.sleep_ms(100)
                            break
                        elif(res and res[0]==0x01 and res[1]==0xFF):
                            self.reset()
                else:
                    _cmd = self.uart.read()
                    del _cmd
                    gc.collect()

    
    def uart_handle(self):
        CMD_TEMP = []
        checksum = 0
        if(self.uart.any()):
            head = self.uart.read(2)
            # self.lcd.draw_string(0,190, 'head:'+str(head), lcd.WHITE, lcd.BLUE)
            if(head and head[0] == 0xAA and head[1]==0xBB):
                CMD_TEMP.extend([0xAA,0xBB])
                cmd_type = self.uart.read(1)
                CMD_TEMP.append(cmd_type[0])
                if(CMD_TEMP[2]==0x01):
                    res = self.uart.read(11)
                    for i in range(11):
                        CMD_TEMP.append(res[i])                  
                    checksum = self.CheckCode(CMD_TEMP[:13])
                    if(res and checksum == CMD_TEMP[13]):
                        # self.lcd.draw_string(0,215, 'cmd:'+str(CMD_TEMP[2:]), lcd.WHITE, lcd.BLUE)
                        self.process_cmd(CMD_TEMP)
                elif(CMD_TEMP[2]==0x02):
                    res = self.uart.read(6)
                    str_len = res[5]
                    str_temp = self.uart.read(str_len)
                    checksum  = self.uart.read(1)
                    for i in range(6):
                        CMD_TEMP.append(res[i]) 
                    for i in range(str_len):
                        CMD_TEMP.append(str_temp[i])
                    CMD_TEMP.append(checksum[0]) 
                    self.process_cmd(CMD_TEMP)  
                    # self.lcd.draw_string(0,65, 's:'+str(str_temp.decode('UTF-8','ignore')), lcd.WHITE, lcd.BLUE)
            else:
                _cmd = self.uart.read()
                del _cmd
                gc.collect()

    def process_cmd(self,cmd):
        CMD = cmd
        if(len(CMD)>0):
            if(CMD[2]==0x01):
                if(CMD[3]==0x01 and CMD[4]==0xFF):
                    self.reset()
                if(CMD[3]==0x01 and CMD[4]==0xFE):
                    self.switcherMode(CMD[5])
                elif(CMD[3]==MNIST_MODE and CMD[4]==0x01):
                    self.k210.mode = MNIST_MODE
                    self.mnist = MNIST(choice=CMD[5],sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==MNIST_MODE and CMD[4]==0x02):
                    self.k210.flag_mnist_recognize = 1
                elif(CMD[3]==OBJECT_RECOGNIZATION_MODE and CMD[4]==0x01):
                    self.k210.mode = OBJECT_RECOGNIZATION_MODE
                    self.yolo_detect = YOLO_DETECT(choice=CMD[5],sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==OBJECT_RECOGNIZATION_MODE and CMD[4]==0x02):
                    self.k210.flag_yolo_recognize = 1
                elif(CMD[3]==FACE_DETECTION_MODE and CMD[4]==0x01 and self.face_detect!=None):
                    self.k210.mode = FACE_DETECTION_MODE
                    self.face_detect = FACE_DETECT(choice=CMD[5],sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==FACE_DETECTION_MODE and CMD[4]==0x02):
                    self.k210.flag_face_detection = 1
                elif(CMD[3]==FACE_RECOGNIZATION_MODE and CMD[4]==0x01):
                    self.k210.mode = FACE_RECOGNIZATION_MODE
                    _choice=CMD[7]
                    _face_num=CMD[5]
                    _accuracy=CMD[6]
                    self.fac=Face_recognization(choice=_choice, sensor=self.sensor, kpu=self.kpu, lcd=self.lcd, face_num=_face_num, accuracy=_accuracy)
                elif(CMD[3]==0x05 and CMD[4]==0x02):#add_face
                    self.k210.flag_add = 1
                    self.fac.tmp_num = 0
                    self.fac.clear_data()
                elif(CMD[3]==0x05 and CMD[4]==0x03):
                    if(self.fac.flag_add!=1):
                        self.k210.flag_add = 0
                        self.k210.flag_fac_recognize = 1
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x01):
                    self.k210.mode = SELF_LEARNING_CLASSIFIER_MODE
                    _choice=CMD[7];_class_num=CMD[5];_sample_num=CMD[6]
                    self.slc=Self_learning_classifier(choice=_choice, sensor=self.sensor, kpu=self.kpu, lcd=self.lcd, class_num=_class_num, sample_num=_sample_num)
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x02):
                    self.slc.flag_add_class = 1
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x03):
                    if(self.slc.flag_add_class==0 and self.slc.flag_add_sample==0 and self.slc.flag_train==0 and self.k210.flag_slc_mode_load==0):
                        self.k210.flag_slc_recognize = 1
                elif(CMD[3]==SPEECH_RECOGNIZATION_MODE and CMD[4]==0x01):
                    self.k210.mode = SPEECH_RECOGNIZATION_MODE
                    self.asr = speech_recognize()
                elif(CMD[3]==SPEECH_RECOGNIZATION_MODE and CMD[4]==0x03):
                    self.k210.flag_asr_recognize=1
                elif(CMD[3]==COLOE_MODE and CMD[4]==0x01):
                    self.k210.mode = COLOE_MODE
                    self.color = Color(choice=CMD[5],sensor=self.sensor,lcd=self.lcd)
                elif(CMD[3]==COLOE_MODE and CMD[4]==0x02):
                    self.k210.flag_color_add = CMD[5]
                    self.color.flag_add = 1
                    self.color.clear_data()
                elif(CMD[3]==COLOE_MODE and CMD[4]==0x03):
                    if(self.color.flag_add==0):
                        self.k210.flag_color_recognize = 1
                elif(CMD[3]==QRCODE_MODE and CMD[4]==0x01):
                    self.k210.mode = QRCODE_MODE
                    self.qrcode = QRCode(choice=CMD[5],sensor=self.sensor,lcd=self.lcd)
                elif(CMD[3]==QRCODE_MODE and CMD[4]==0x02):
                    self.k210.flag_qrcode_add = CMD[5]
                    self.qrcode.flag_add = 1
                    self.qrcode.clear_data()
                elif(CMD[3]==QRCODE_MODE and CMD[4]==0x03):
                    if(self.qrcode.flag_add==0):
                        self.k210.flag_qrcode_recognize = 1
                elif(CMD[3]==GUIDEPOST_MODE and CMD[4]==0x01):
                    self.k210.mode = GUIDEPOST_MODE
                    self.guidepost = Guidepost(choice=CMD[5],sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==GUIDEPOST_MODE and CMD[4]==0x02):
                    self.k210.flag_guidepost_recognize = 1
                elif(CMD[3]==KPU_MODEL_MODE and CMD[4]==0x01):
                    # self.k210.mode = KPU_MODEL_MODE
                    # self.guidepost = Guidepost(choice=CMD[5],sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                    pass
                elif(CMD[3]==KPU_MODEL_MODE and CMD[4]==0x03):
                    self.k210.flag_kpu_recognize = 1
                elif(CMD[3]==TRACK_MODE and CMD[4]==0x01):
                    self.k210.mode = TRACK_MODE
                    self.track = Track(lcd=self.lcd,sensor=self.sensor,choice=CMD[5],threshold=[CMD[6],CMD[7],CMD[8],CMD[9],CMD[10],CMD[11]])
                elif(CMD[3]==TRACK_MODE and CMD[4]==0x03):
                    self.track.threshold = [CMD[5],CMD[6],CMD[7],CMD[8],CMD[9],CMD[10]]
                    self.track.area_threshold = CMD[11]
                elif(CMD[3]==TRACK_MODE and CMD[4]==0x02):
                    self.k210.flag_track_recognize = 1
            elif(CMD[2]==0x02):
                if(CMD[3]==SPEECH_RECOGNIZATION_MODE and CMD[4]==0x02):
                    _config ={}
                    str_temp = bytes(CMD[9:-1])
                    str_config = str(str_temp.decode('UTF-8','ignore')).split(',')
                    for i in range(len(str_config)):
                        _config[str_config[i]]=[0.25,i]
                    self.asr.config(_config)
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x04):
                    str_temp = bytes(CMD[9:-1])
                    mode_name = str(str_temp.decode('UTF-8','ignore'))
                    # self.lcd.draw_string(50,225, 's:'+str(mode_name), lcd.WHITE, lcd.BLUE)
                    self.k210.slc_mode_name = mode_name
                    self.k210.flag_slc_mode_save = 1
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x05):
                    str_temp = bytes(CMD[9:-1])
                    mode_name = str(str_temp.decode('UTF-8','ignore'))
                    self.k210.slc_mode_name = mode_name
                    self.k210.flag_slc_mode_load = 1
                elif(CMD[3]==KPU_MODEL_MODE and CMD[4]==0x02):
                    str_temp = bytes(CMD[9:-1])
                    mode_name = str(str_temp.decode('UTF-8','ignore'))
                    # self.k210.kpu_kmodel_name = mode_name
                    # self.lcd.draw_string(50,225, 's:'+str(str_temp.decode('UTF-8','ignore')), lcd.WHITE, lcd.BLUE)
                    # self.lcd.draw_string(50,205, 'ss:'+str(CMD[5]), lcd.WHITE, lcd.BLUE)
                    self.k210.mode = KPU_MODEL_MODE
                    self.kpu_model = KPU_KMODEL(choice=CMD[5],sensor=self.sensor,kpu=self.kpu,lcd=self.lcd,model=mode_name)
                
    def uart_listen(self):
        self.send_to_zkb_init()
        num = 0
        while True:
            gc.collect()
            time.sleep_ms(1)
            # num+=1
            # lcd.draw_string(200,0, 'listen:'+str(num), lcd.WHITE, lcd.BLUE)
            # lcd.draw_string(0,0, 'mode:'+str(self.k210.mode), lcd.WHITE, lcd.BLUE)
            self.uart_handle()
            try:
                if(self.k210.mode==DEFAULT_MODE):
                    pass
                elif(self.k210.mode==MNIST_MODE):
                    if(self.k210.flag_mnist_recognize):
                        classid,value = self.mnist.recognize()
                        self.AI_Uart_CMD(0x01,0x02,0x02,cmd_data=[classid,value])
                        self.k210.flag_mnist_recognize = 0
                elif(self.k210.mode==OBJECT_RECOGNIZATION_MODE and self.yolo_detect!=None):
                    if(self.k210.flag_yolo_recognize):
                        classid,value = self.yolo_detect.recognize()
                        if(classid==None):
                            self.AI_Uart_CMD(0x01,0x03,0x02,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x03,0x02,cmd_data=[classid,value])
                        self.k210.flag_yolo_recognize = 0
                elif(self.k210.mode==FACE_DETECTION_MODE):
                    if(self.k210.flag_face_detection):
                        face_num,value = self.face_detect.recognize()
                        if(face_num==None):
                            self.AI_Uart_CMD(0x01,0x04,0x02,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x04,0x02,cmd_data=[face_num,value])
                        self.k210.flag_face_detection = 0
                elif(self.k210.mode==FACE_RECOGNIZATION_MODE):
                    if(self.fac.flag_add==2):
                        self.k210.flag_add = 0
                    if(self.k210.flag_add):
                        self.fac.add_face()
                    if(self.k210.flag_fac_recognize):
                        res,max_score = self.fac.face_recognize()
                        if(res==None):
                            self.AI_Uart_CMD(0x01,0x05,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x05,0x03,cmd_data=[int(res),int(max_score)])
                        self.k210.flag_fac_recognize = 0
                elif(self.k210.mode==SELF_LEARNING_CLASSIFIER_MODE):
                    if(self.k210.flag_slc_mode_load):
                        if(self.slc!=None):
                            self.slc.load_classifier(self.k210.slc_mode_name)
                            self.k210.flag_slc_mode_load = 0
                    if(self.slc.flag_add_class):
                        self.slc.add_class_img()
                    elif(self.slc.flag_add_sample):
                        self.slc.add_sample_img()
                    elif(self.slc.flag_train):
                        self.slc.train()
                        if(self.k210.flag_slc_mode_save):
                             self.slc.save_classifier(self.k210.slc_mode_name)
                             self.k210.flag_slc_mode_save = 0
                    elif(self.k210.flag_slc_recognize):
                        id,value = self.slc.predict()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x06,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x06,0x03,cmd_data=[id,int(value*10)])
                        self.k210.flag_slc_recognize = 0
                elif(self.k210.mode==COLOE_MODE):
                    if(self.color.flag_add):
                        self.color.add_color(self.k210.flag_color_add)
                    elif(self.k210.flag_color_recognize):
                        id = self.color.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x07,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x07,0x03,cmd_data=[id])
                        self.k210.flag_color_recognize=0
                elif(self.k210.mode==QRCODE_MODE):
                    if(self.qrcode.flag_add):
                        self.qrcode.add_qrcode(self.k210.flag_qrcode_add)
                    elif(self.k210.flag_qrcode_recognize):
                        id,info = self.qrcode.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x08,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x08,0x03,cmd_data=[id])
                        self.k210.flag_qrcode_recognize=0
                elif(self.k210.mode==SPEECH_RECOGNIZATION_MODE):
                    if(self.k210.flag_asr_recognize):
                        id = self.asr.recognize()
                        if(id==None):
                             self.AI_Uart_CMD(0x01,0x09,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x09,0x03,cmd_data=[int(id)])
                        self.k210.flag_asr_recognize=0
                elif(self.k210.mode==GUIDEPOST_MODE and self.guidepost!=None):
                    if(self.k210.flag_guidepost_recognize):
                        id,value = self.guidepost.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x0a,0x02,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x0a,0x02,cmd_data=[id,value])
                        self.k210.flag_guidepost_recognize = 0
                elif(self.k210.mode==KPU_MODEL_MODE and self.kpu_model!=None):
                    if(self.k210.flag_kpu_recognize):
                        id,value = self.kpu_model.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x0b,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x0b,0x03,cmd_data=[id,value])
                        self.k210.flag_kpu_recognize = 0
                elif(self.k210.mode==TRACK_MODE and self.track!=None):
                    if(self.k210.flag_track_recognize):
                        x,y,cx,cy,w,h,pixels,count= self.track.recognize()
                        if(x==None):
                            self.AI_Uart_CMD(0x01,0x0c,0x02,cmd_data=[0xff])
                        else:
                            # self.AI_Uart_CMD(0x01,0x0c,0x02,cmd_data=[x,y,cx,cy,w,h])
                            _str=str(x)+'|'+str(y)+'|'+str(cx)+'|'+str(cy)+'|'+str(w)+'|'+str(h)+'|'+str(pixels)+'|'+str(count)
                            self.AI_Uart_CMD_String(cmd=0x0c,cmd_type=0x02,str_buf=_str)
                        self.k210.flag_track_recognize = 0
            except Exception as e:
                lcd.draw_string(0,180, 'err:'+str(e), lcd.WHITE, lcd.BLUE)

    def reset(self):
        self.AI_Uart_CMD(0x01,0x01,0xFF)
        time.sleep(0.1)
        machine.reset()
    
    def switcherMode(self, mode):
        if(self.k210.mode==GUIDEPOST_MODE):
            self.guidepost.__del__()
            del self.guidepost
        elif(self.k210.mode==TRACK_MODE):
            self.track.__del__()
            del self.track
        
        _cmd = self.uart.read()
        del _cmd
        time.sleep(0.2)
        self.AI_Uart_CMD(0x01,0x01,0xFE)
        self.k210.mode = DEFAULT_MODE
        self.lcd.draw_string(0,215, 'mode:'+str(self.k210.mode), lcd.WHITE, lcd.BLUE)
        
        gc.collect()

    def change_camera(self, choice):
        try:
            self.sensor.reset(choice=choice)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_hmirror(1)
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        
        if(choice==1):
            self.sensor.set_vflip(1)
        else:
            self.sensor.set_vflip(0)
            self.sensor.set_hmirror(0)
        
        self.sensor.skip_frames(30)
        self.sensor.run(1)
    
try:
    aiCamera=AICamera()
except Exception as e:
    lcd.clear((0, 0, 255))
    lcd.draw_string(0,200, 'err:'+str(e), lcd.WHITE, lcd.BLUE)