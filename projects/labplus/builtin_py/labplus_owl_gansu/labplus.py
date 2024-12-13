import time
import machine
from machine import UART
from Maix import GPIO, FPIOA, utils
import KPU as kpu
import sensor, lcd, image
from board import button, LED, RGB
from display import *
# from modules import ws2812
import gc
from fpioa_manager import fm
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

from display import Draw_CJK_String
import video
utils.gc_heap_size(0x60000) 
""" 
-------------------------------------------------------------------------------------------------------
盛思OWL初始化
-------------------------------------------------------------------------------------------------------
"""
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
TRACK_MODE= 12 #色块识别
COLOR_STATISTICS_MODE=13 # 颜色的统计信息
COLOR_EXTRACTO_MODE=14 # LAB颜色提取器
APRILTAG_MODE=15
KPU_YOLO_MODEL_MODE = 16 #自定义YOLO模型
VIDEO_MODE = 20
FACTORY_MODE = 99

class AICamera(object):
    class K210:
        def __init__(self):
            '''k210模式及默认值'''
            self.cmd = []
            self.mode = DEFAULT_MODE
            self.sensor_choice = 1
            self.flag_mnist_recognize = 0 
            self.flag_add = 0
            self.flag_fac_recognize = 0
            self.flag_yolo_recognize = 0
            self.flag_face_detection = 0
            self.flag_asr_recognize = 0
            self.flag_slc_recognize = 0
            self.flag_slc_add = 0
            self.slc_mode_name = ''
            self.slc_lode_mode_name = ''
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
            self.flag_kpu_recognize = 0
            #
            self.flag_track_recognize = 0
            self.flag_color_statistics_recognize = 0
            self.flag_color_ex_recognize = 0     
            #
            self.flag_apriltag_recognize = 0
            #
            self.flag_kpu_yolol_recognize = 0
            #工厂测试
            self.lcd_test = False
            self.sensor_test = False
            self.button_test = False
            self.light_test = False
            # self.sd_test = False

            #切换模式
            self.sw_lock = False
            
    def __init__(self):
        fm.register(11, fm.fpioa.UART2_TX, force=True)
        fm.register(10, fm.fpioa.UART2_RX, force=True)
        self.uart = UART(UART.UART2)
        # self.uart.init(1152000, 8, None, 1, read_buf_len=128)
        self.uart.init(1152000, 8, None, read_buf_len=4096)
        time.sleep(0.1)
        self.lcd = lcd
        self.kpu = kpu
        self.sensor = sensor
        self.led = LED(25,False)
          
        self.lcd.init(freq=15000000, invert=1)
        self.lcd.rotation(2)
        try:
            background = image.Image('/flash/gansu.jpg', copy_to_fb=True)
            self.lcd.display(background)
            del background
        except Exception as e:
            self.lcd.clear(lcd.BLUE)
            self.lcd.draw_string(lcd.width()//2-100,lcd.height()//2-4, "labplus AI Camera gansu", lcd.WHITE, lcd.BLUE) 
            time.sleep(1)

        self.change_camera()

        # button
        self.btn_A = button(12,False)
        self.btn_B = button(13,False)
        self.btn_A_status = 0
        self.btn_B_status = 0
        time.sleep(0.1)

        # TF卡状态
        self.tf_status = 0
        self.tf_sn =  ''

        # k210 flag
        self.k210 = self.K210()
        self.slc = None
        self.asr = None
        self.yolo_detect = None
        self.face_detect = None
        self.fac= None
        self.color = None
        self.mnist = None
        self.guidepost = None
        self.track = None
        self.color_statistics=None
        self.color_ex=None
        self.apriltag=None
        self.kpu_model=None
        self.qrcode = None
        self.kpu_yolo_model=None

        # sensor config
        self._choice=1
        self._framesize=sensor.QVGA
        self._pixformat=sensor.RGB565
        self._w=320
        self._h=240
        self._vflip=1
        self._hmirror=1
        self._brightness=0
        self._contrast=0
        self._saturation=0
        self._gain=0
        self._whitebal=0
        self._freq=24000000
        self._dual_buff=False
      
        # 开始串口监听程序
        time.sleep(0.5)
        self.send_to_zkb_init()
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
        
        CMD_TEMP.append(check_sum & 0xFF)
        self.uart.write(bytes(CMD_TEMP))
        del CMD_TEMP
        # self.print_x16(CMD_TEMP)
        
    def AI_Uart_CMD_String(self,cmd=0x00, cmd_type=0x00, cmd_data=[0x00], str_len=0, str_buf=''):
        # check_sum = 0
        CMD = [0xBB, 0xAA, 0x02, cmd, cmd_type]
        CMD.extend(cmd_data)
        for i in range(15-len(cmd_data)):
            CMD.append(0)
    
        # self.uart.write(bytes(CMD))
        str_temp = bytes(str_buf, 'utf-8')
        str_len = len(str_temp)

        CMD = bytes(CMD) + bytes([str_len]) + str_temp + bytes([0xAB])
        self.uart.write(CMD)   
        # self.print_x16(CMD)
        # print('='*5)
    
    def print_x16(self,date):
        for i in range(len(date)):
            print('{:2x}'.format(date[i]),end=' ')
        print('')

    def send_to_zkb_init(self): 
        while True:
            gc.collect()
            time.sleep_ms(10)
            if(self.uart.any()):
                head=self.uart.read(2)
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
                    # print(head)
                    # print('==head==')
                    # print('**^**')
                    _cmd = self.uart.read()
                    del _cmd
                    gc.collect()
    
    def uart_handle(self):
        CMD_TEMP = []
        checksum = 0
        if(self.uart.any()):
            head = self.uart.read(2)
            if(head and head[0] == 0xAA and head[1]==0xBB):
                CMD_TEMP.extend([0xAA,0xBB])
                time.sleep_ms(1)
                cmd_type = self.uart.read(1)
                if(cmd_type==None or len(cmd_type)==0):
                    print('@')
                    return
                CMD_TEMP.append(cmd_type[0])
                if(CMD_TEMP[2]==0x01):
                    time.sleep_ms(2)
                    res = self.uart.read(11)
                    if(res==None or len(res)!=11):
                        print(res)
                        print('#')
                        return
                    for i in range(11):
                        CMD_TEMP.append(res[i])                  
                    checksum = self.CheckCode(CMD_TEMP[:13])
                    if(res and checksum == CMD_TEMP[13]):
                        self.process_cmd(CMD_TEMP)
                    # else:
                    #     print(CMD_TEMP)
                    #     print('===CMD_TEMP====')
                elif(CMD_TEMP[2]==0x02):
                    time.sleep_ms(5)
                    res = self.uart.read(6)
                    if(res==None or len(res)!=6):
                        print('&')
                        return
                    time.sleep_ms(20)
                    str_len = res[5]
                    str_temp = self.uart.read(str_len)
                    if(str_temp==None or len(str_temp)!=str_len):
                        print('&&')
                        return
                    time.sleep_ms(5)
                    checksum  = self.uart.read(1)
                    if(checksum==None or len(checksum)!=1):
                        print('&&&')
                        return
                    for i in range(6):
                        CMD_TEMP.append(res[i]) 
                    for i in range(str_len):
                        CMD_TEMP.append(str_temp[i])
                    CMD_TEMP.append(checksum[0]) 
                    self.process_cmd(CMD_TEMP)  
                    # print(str(str_temp.decode('UTF-8','ignore')))
            else:
                # print(head)
                # print('==head==')
                # print('**^**')
                # del _cmd
                gc.collect()

    def process_cmd(self,cmd):
        CMD = cmd
        if(len(CMD)>0):
            if(CMD[2]==0x01):
                if(CMD[3]==0x01 and CMD[4]==0x01):
                    self.AI_Uart_CMD(0x01,0x01,0x01)
                    time.sleep_ms(200)
                elif(CMD[3]==0x01 and CMD[4]==0xFF):
                    self.reset()
                elif(CMD[3]==0x01 and CMD[4]==0xFA and CMD[5]==0x01):
                    self.init_canvas()
                elif(CMD[3]==0x01 and CMD[4]==0xFA and CMD[5]==0x02):
                    self.clear_canvas()
                elif(CMD[3]==0x01 and CMD[4]==99 and CMD[5]==0x01):
                    self.k210.mode = FACTORY_MODE
                    if self.sd_test():
                        self.tf_status = 1
                    else:
                        self.tf_status = 0
                elif(CMD[3]==0x01 and CMD[4]==99 and CMD[5]==0x02):
                    self.k210.lcd_test = True
                elif(CMD[3]==0x01 and CMD[4]==99 and CMD[5]==0x03):
                    self.k210.sensor_test = True
                # elif(CMD[3]==0x01 and CMD[4]==99 and CMD[5]==0x04):
                #     self.rgb_test()
                elif(CMD[3]==0x01 and CMD[4]==99 and CMD[5]==0x05):
                    self.led_test()
                elif(CMD[3]==0x01 and CMD[4]==0xFE):
                    print("$$$")
                    self.switcherMode(CMD[5])
                elif(CMD[3]==MNIST_MODE and CMD[4]==0x01):
                    self.k210.mode = MNIST_MODE
                    self.mnist = MNIST(sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==MNIST_MODE and CMD[4]==0x02):
                    self.k210.flag_mnist_recognize = 1
                elif(CMD[3]==OBJECT_RECOGNIZATION_MODE and CMD[4]==0x01):
                    self.k210.mode = OBJECT_RECOGNIZATION_MODE
                    self.yolo_detect = YOLO_DETECT(sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==OBJECT_RECOGNIZATION_MODE and CMD[4]==0x02):
                    self.k210.flag_yolo_recognize = 1
                elif(CMD[3]==FACE_DETECTION_MODE and CMD[4]==0x01):
                    self.k210.mode = FACE_DETECTION_MODE
                    self.face_detect = FACE_DETECT(sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==FACE_DETECTION_MODE and CMD[4]==0x02):
                    self.k210.flag_face_detection = 1
                elif(CMD[3]==FACE_RECOGNIZATION_MODE and CMD[4]==0x01):
                    self.k210.mode = FACE_RECOGNIZATION_MODE
                    _choice=CMD[7]
                    _face_num=CMD[5]
                    _accuracy=CMD[6]
                    self.fac=Face_recognization(sensor=self.sensor, kpu=self.kpu, lcd=self.lcd, face_num=_face_num, accuracy=_accuracy)
                elif(CMD[3]==0x05 and CMD[4]==0x02):
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
                    self.slc=Self_learning_classifier(sensor=self.sensor, kpu=self.kpu, lcd=self.lcd, class_num=_class_num, sample_num=_sample_num)
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x02):
                    if(self.slc!=None):
                        self.slc.flag_add_class = 1
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x03):
                    if(self.slc!=None):
                        if(self.slc.flag_add_class==0 and self.slc.flag_add_sample==0 and self.slc.flag_train==0 and self.k210.flag_slc_mode_load==0):
                            self.k210.flag_slc_recognize = 1
                # elif(CMD[3]==SPEECH_RECOGNIZATION_MODE and CMD[4]==0x01):
                #     self.k210.mode = SPEECH_RECOGNIZATION_MODE
                #     self.asr = speech_recognize()
                #     time.sleep(0.1)
                # elif(CMD[3]==SPEECH_RECOGNIZATION_MODE and CMD[4]==0x03):
                #     self.k210.flag_asr_recognize=1
                elif(CMD[3]==COLOE_MODE and CMD[4]==0x01):
                    self.k210.mode = COLOE_MODE
                    self.color = Color(sensor=self.sensor,lcd=self.lcd)
                elif(CMD[3]==COLOE_MODE and CMD[4]==0x02):
                    self.k210.flag_color_add = CMD[5]
                    self.color.flag_add = 1
                    self.color.clear_data()
                elif(CMD[3]==COLOE_MODE and CMD[4]==0x03):
                    if(self.color.flag_add==0):
                        self.k210.flag_color_recognize = 1
                elif(CMD[3]==QRCODE_MODE and CMD[4]==0x01):
                    self.k210.mode = QRCODE_MODE
                    self.qrcode = QRCode(sensor=self.sensor,lcd=self.lcd)
                elif(CMD[3]==QRCODE_MODE and CMD[4]==0x02):
                    self.k210.flag_qrcode_add = CMD[5]
                    self.qrcode.flag_add = 1
                    self.qrcode.clear_data()
                elif(CMD[3]==QRCODE_MODE and CMD[4]==0x03):
                    if(self.qrcode.flag_add==0):
                        self.k210.flag_qrcode_recognize = 1
                elif(CMD[3]==GUIDEPOST_MODE and CMD[4]==0x01):
                    self.k210.mode = GUIDEPOST_MODE
                    self.guidepost = Guidepost(sensor=self.sensor,kpu=self.kpu,lcd=self.lcd)
                elif(CMD[3]==GUIDEPOST_MODE and CMD[4]==0x02):
                    self.k210.flag_guidepost_recognize = 1
                elif(CMD[3]==KPU_MODEL_MODE and CMD[4]==0x01):
                    pass
                elif(CMD[3]==KPU_MODEL_MODE and CMD[4]==0x03):
                    self.k210.flag_kpu_recognize = 1
                elif(CMD[3]==TRACK_MODE and CMD[4]==0x01):
                    self.change_camera(_framesize=self._framesize,_pixformat=self._pixformat,_w=self._w,_h=self._h,_vflip=self._vflip,_hmirror=self._hmirror,_brightness=self._brightness,_contrast=self._contrast,_saturation=self._saturation,_gain=self._gain,_whitebal=self._whitebal)
                    self.track = Track(lcd=self.lcd,sensor=self.sensor)
                    self.k210.mode = TRACK_MODE
                elif(CMD[3]==TRACK_MODE and CMD[4]==0x02 and self.track!=None):
                    self.k210.flag_track_recognize = 1
                elif(CMD[3]==COLOR_STATISTICS_MODE and CMD[4]==0x01):
                    self.k210.mode = COLOR_STATISTICS_MODE
                    if(int(CMD[5])==1):
                        self.change_camera(_framesize=sensor.QQVGA,_pixformat=sensor.GRAYSCALE,_w=160,_h=120,_freq=24000000,_dual_buff=True)
                    else:
                        self.change_camera(_framesize=sensor.QQVGA,_pixformat=sensor.GRAYSCALE,_vflip=0,_hmirror=0,_w=160,_h=120,_freq=24000000,_dual_buff=True)
                    self.color_statistics = Color_Statistics(lcd=self.lcd,sensor=self.sensor)  
                elif(CMD[3]==COLOR_STATISTICS_MODE and CMD[4]==0x02 and self.color_statistics!=None ):
                    self.k210.flag_color_statistics_recognize = 1                               
                elif(CMD[3]==COLOR_STATISTICS_MODE and CMD[4]==0x03):
                    self.color_statistics.set_up_img_binary(int(CMD[5]),int(CMD[6]))             
                elif(CMD[3]==COLOR_STATISTICS_MODE and CMD[4]==0x04):
                    self.color_statistics.set_up_line_binary(int(CMD[5]),int(CMD[6]))       
                elif(CMD[3]==COLOR_EXTRACTO_MODE and CMD[4]==0x01):
                    self.k210.mode = COLOR_EXTRACTO_MODE
                    if(int(CMD[5])==1):
                        self.change_camera(_framesize=sensor.QQVGA,_pixformat=sensor.RGB565,_w=160,_h=120,_freq=24000000,_dual_buff=True,_whitebal=False)
                    else:
                        self.change_camera(_framesize=sensor.QQVGA,_pixformat=sensor.RGB565,_vflip=0,_hmirror=0,_w=160,_h=120,_freq=24000000,_dual_buff=True,_brightness=-1,_whitebal=False)
                    self.color_ex = Color_Extractor(lcd=self.lcd,sensor=self.sensor)  
                elif(CMD[3]==COLOR_EXTRACTO_MODE and CMD[4]==0x02 and self.color_ex!=None ):
                    self.k210.flag_color_ex_recognize = 1                  
                elif(CMD[3]==APRILTAG_MODE and CMD[4]==0x01):
                    self.k210.mode = APRILTAG_MODE
                    if(int(CMD[5])==1):
                        self.change_camera(_framesize=sensor.QQVGA,_pixformat=sensor.RGB565,_w=160,_h=120,_freq=24000000,_dual_buff=True,_whitebal=False)
                    else:
                        self.change_camera(_framesize=sensor.QQVGA,_pixformat=sensor.RGB565,_vflip=0,_hmirror=0,_w=160,_h=120,_freq=24000000,_dual_buff=True,_whitebal=False)
                    self.apriltag = Apriltag(lcd=self.lcd,sensor=self.sensor)  
                elif(CMD[3]==APRILTAG_MODE and CMD[4]==0x02 and self.apriltag!=None ):
                    self.k210.flag_apriltag_recognize = 1                  
                elif(CMD[3]==APRILTAG_MODE and CMD[4]==0x03):
                    self.apriltag.set_families(int(CMD[5]))     
                elif(CMD[3]==KPU_YOLO_MODEL_MODE and CMD[4]==0x03):
                    self.k210.flag_kpu_yolol_recognize = 1                                       
            elif(CMD[2]==0x02):
                if(CMD[3]==SPEECH_RECOGNIZATION_MODE and CMD[4]==0x02):
                    time.sleep(0.1)
                    _config ={}
                    str_temp = bytes(CMD[9:-1])
                    print(str_temp)
                    str_config = str(str_temp.decode('UTF-8','ignore')).split(',')
                    for i in range(len(str_config)):
                        _config[str_config[i]]=[0.15,i]
                    print(_config)
                    self.asr.config(_config)
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x04):
                    str_temp = bytes(CMD[9:-1])
                    mode_name = str(str_temp.decode('UTF-8','ignore'))
                    self.k210.slc_mode_name = mode_name
                    self.k210.flag_slc_mode_save = 1
                elif(CMD[3]==SELF_LEARNING_CLASSIFIER_MODE and CMD[4]==0x05):
                    str_temp = bytes(CMD[9:-1])
                    mode_name = str(str_temp.decode('UTF-8','ignore'))
                    self.k210.slc_lode_mode_name = mode_name
                    self.k210.flag_slc_mode_load = 1
                elif(CMD[3]==KPU_MODEL_MODE and CMD[4]==0x02):
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    data = _str.split("|")
                    print(data)
                    self.k210.mode = KPU_MODEL_MODE
                    self.kpu_model = KPU_KMODEL(sensor=self.sensor,kpu=self.kpu,lcd=self.lcd,model=data[0],width=int(data[1]),height=int(data[2]))
                elif(CMD[3]==TRACK_MODE and CMD[4]==0x03):
                    time.sleep(0.05)
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    data = _str.split("|")
                    _list = []
                    for i in range(int(CMD[5])):
                        _data = [int(data[6*i]),int(data[6*i+1]),int(data[6*i+2]),int(data[6*i+3]),int(data[6*i+4]),int(data[6*i+5])]
                        _list.append(_data)
                    self.track.set_up(_list,int(data[-1]))
                elif(CMD[3]==0x64 and CMD[4]==0x01):
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    data = _str.split("|")
                    self._choice=CMD[5]
                    if(int(data[0])==1):
                        self._framesize=sensor.QVGA
                    elif(int(data[0])==2):
                        self._framesize=sensor.QQVGA
                    elif(int(data[0])==3):
                        self._framesize=sensor.QQQVGA
                    elif(int(data[0])==4):
                        self._framesize=sensor.QQQQVGA
                    else:
                        self._framesize=sensor.QVGA

                    if(int(data[1])==1):
                        self._pixformat=sensor.RGB565
                    elif(int(data[1])==2):
                        self._pixformat=sensor.GRAYSCALE
                    self._hmirror=int(data[2])
                    self._vflip=int(data[3])
                    self._brightness=int(data[4])
                    self._contrast=int(data[5])
                    self._saturation=int(data[6])
                    self._gain=int(data[7])
                    self._whitebal=int(data[8])
                    self._w=int(data[9])
                    self._h=int(data[10])
                    self._freq=int(data[11])
                    self._dual_buff=int(data[12])
                elif(CMD[3]==VIDEO_MODE and CMD[4]==0x01):
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    data = _str.split("|")
                    print(data)
                    choice=CMD[5]
                    quality=CMD[6]
                    self.record(path=data[0], interval=int(data[1]), quality=quality, width=int(data[2]), height=int(data[3]), duration=int(data[4]))
                elif(CMD[3]==KPU_YOLO_MODEL_MODE and CMD[4]==0x02):
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    data = _str.split("|")
                    print(data)
                    self.k210.mode = KPU_YOLO_MODEL_MODE
                    self.kpu_yolo_model = KPU_YOLO_KMODEL(sensor=self.sensor,kpu=self.kpu,lcd=self.lcd,model=data[0],width=int(data[1]),height=int(data[2]),anchors=eval(data[3]))
                elif(CMD[3]==DEFAULT_MODE and CMD[4]==0xFA):
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    data = eval(_str)
                    print(data)

                    scale = CMD[5]
                    x = data[0]
                    y = data[1]
                    # txt = data[2]
                    txt = bytes(str(data[2]),'utf-8')
                    self.canvas_txt(txt,scale,x,y)
                elif(CMD[3]==FACTORY_MODE and CMD[4]==0x01):
                    str_temp = bytes(CMD[9:-1])
                    _str = str(str_temp.decode('UTF-8','ignore'))
                    sn = eval(_str)[0]
                    self.sn_write(sn)
                    
    def uart_listen(self):
        num = 0
        while True:
            gc.collect()
            time.sleep_ms(5)
          
            try:
                self.uart_handle()
            except Exception as e:
                print(str(e))
                print("==uart_handle==")

            try:
                if(self.k210.mode==DEFAULT_MODE):
                    pass
                elif(self.k210.mode==COLOR_STATISTICS_MODE and self.color_statistics!=None):
                    if(self.k210.flag_color_statistics_recognize):
                        time.sleep_ms(10)
                        tmp =  self.color_statistics.recognize()
                        if(tmp==None or tmp[-1]==None):
                            # self.AI_Uart_CMD(0x01,0x0d,0x02,cmd_data=[0xff])
                            # print('^'*3)
                            pass
                        else:
                            data1,data2,data3,data4,data5,data6,data7,data8,data9,data10,data11,data12,data13,data14,data15,_line=tmp
                            _cmd_data = [data1,data2,data3,data4,data5,data6,data7,data8,data9,data10,data11,data12,data13,data14,data15]
                            _str = str([_line[0],_line[1],_line[2],_line[3],_line[4],_line[5],_line[6],_line[7]])
                            self.AI_Uart_CMD_String(cmd=0x0d,cmd_type=0x02,cmd_data=_cmd_data,str_buf=_str)
                        # self.k210.flag_color_statistics_recognize = 0
                elif(self.k210.mode==MNIST_MODE and self.mnist!=None):
                    if(self.k210.flag_mnist_recognize):
                        time.sleep_ms(5)
                        tmp = self.mnist.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x02,0x02,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x02,0x02,cmd_data=[0xff])
                        else:
                            classid,value = tmp
                            self.AI_Uart_CMD(0x01,0x02,0x02,cmd_data=[classid,value])
                        # self.k210.flag_mnist_recognize = 0
                elif(self.k210.mode==OBJECT_RECOGNIZATION_MODE and self.yolo_detect!=None):
                    if(self.k210.flag_yolo_recognize):
                        time.sleep_ms(10)
                        tmp = self.yolo_detect.recognize()
                        if(tmp==None or tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x03,0x02,cmd_data=[0xff])
                        else:
                            classid,value,objnum = tmp
                            self.AI_Uart_CMD(0x01,0x03,0x02,cmd_data=[classid,value,objnum])
                        # self.k210.flag_yolo_recognize = 0
                elif(self.k210.mode==FACE_DETECTION_MODE):
                    if(self.k210.flag_face_detection):
                        time.sleep_ms(10)
                        tmp = self.face_detect.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x04,0x02,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x04,0x02,cmd_data=[0xff])
                        else:
                            face_num,value = tmp
                            self.AI_Uart_CMD(0x01,0x04,0x02,cmd_data=[face_num,value])
                        # self.k210.flag_face_detection = 0
                elif(self.k210.mode==FACE_RECOGNIZATION_MODE):
                    if(self.fac.flag_add==2):
                        self.k210.flag_add = 0
                    if(self.k210.flag_add):
                        self.fac.add_face()
                    if(self.k210.flag_fac_recognize):
                        time.sleep_ms(10)
                        tmp = self.fac.face_recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x05,0x03,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x05,0x03,cmd_data=[0xff])
                        else:
                            res,max_score = tmp
                            self.AI_Uart_CMD(0x01,0x05,0x03,cmd_data=[int(res),int(max_score)])
                        # self.k210.flag_fac_recognize = 0
                elif(self.k210.mode==SELF_LEARNING_CLASSIFIER_MODE):
                    if(self.k210.flag_slc_mode_load):
                        if(self.slc!=None):
                            if(self.slc.flag_add_class==0 and self.slc.flag_add_sample==0 and self.slc.flag_train==0 and self.k210.flag_slc_mode_save == 0):
                                self.slc.load_classifier(self.k210.slc_lode_mode_name)
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
                        tmp= self.slc.predict()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x06,0x03,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x06,0x03,cmd_data=[0xff])
                        else:
                            id,value = tmp
                            self.AI_Uart_CMD(0x01,0x06,0x03,cmd_data=[id,int(value*10)])
                        # self.k210.flag_slc_recognize = 0
                elif(self.k210.mode==COLOE_MODE):
                    if(self.color.flag_add):
                        self.color.add_color(self.k210.flag_color_add)
                    elif(self.k210.flag_color_recognize):
                        id = self.color.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x07,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x07,0x03,cmd_data=[id])
                        # self.k210.flag_color_recognize=0
                elif(self.k210.mode==QRCODE_MODE):
                    if(self.qrcode.flag_add):
                        self.qrcode.add_qrcode(self.k210.flag_qrcode_add)
                    elif(self.k210.flag_qrcode_recognize):
                        tmp = self.qrcode.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x08,0x03,cmd_data=[0xff])
                        elif(tmp[1]==None):
                            self.AI_Uart_CMD(0x01,0x08,0x03,cmd_data=[0xff])
                        else:
                            id,info = tmp
                            _str = str([id,info])
                            self.AI_Uart_CMD_String(cmd=0x08,cmd_type=0x03,str_buf=_str)
                        # self.k210.flag_qrcode_recognize=0
                elif(self.k210.mode==SPEECH_RECOGNIZATION_MODE and self.asr!=None):
                    if(self.k210.flag_asr_recognize):
                        time.sleep_ms(20)
                        _id = self.asr.recognize()
                        if(_id==None):
                             self.AI_Uart_CMD(0x01,0x09,0x03,cmd_data=[0xff])
                        else:
                            lcd.draw_string(0,0, 'asr:'+str(_id), lcd.WHITE, lcd.BLUE)
                            print( 'asr:'+str(_id))
                            self.AI_Uart_CMD(0x01,0x09,0x03,cmd_data=[int(_id)])
                        # self.k210.flag_asr_recognize=0
                elif(self.k210.mode==GUIDEPOST_MODE and self.guidepost!=None):
                    if(self.k210.flag_guidepost_recognize):
                        tmp = self.guidepost.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x0a,0x02,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x0a,0x02,cmd_data=[0xff])
                        else:
                            id,value = tmp
                            self.AI_Uart_CMD(0x01,0x0a,0x02,cmd_data=[id,value])
                        # self.k210.flag_guidepost_recognize = 0
                elif(self.k210.mode==KPU_MODEL_MODE and self.kpu_model!=None):
                    if(self.k210.flag_kpu_recognize):
                        id,value = self.kpu_model.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x0b,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x0b,0x03,cmd_data=[id,value])
                        # self.k210.flag_kpu_recognize = 0
                elif(self.k210.mode==TRACK_MODE and self.track!=None):
                    if(self.k210.flag_track_recognize):
                        tmp = self.track.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x0c,0x02,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x0c,0x02,cmd_data=[0xff])
                        else:
                            x,y,cx,cy,w,h,pixels,count,code = tmp
                            _cmd_data = [code]
                            _str=str(x)+'|'+str(y)+'|'+str(cx)+'|'+str(cy)+'|'+str(w)+'|'+str(h)+'|'+str(pixels)+'|'+str(count)
                            self.AI_Uart_CMD_String(cmd=0x0c,cmd_type=0x02,cmd_data=_cmd_data,str_buf=_str)
                        # self.k210.flag_track_recognize = 0
                elif(self.k210.mode==COLOR_EXTRACTO_MODE and self.color_ex!=None):
                    if(self.k210.flag_color_ex_recognize):
                        tmp = self.color_ex.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x0e,0x02,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x0e,0x02,cmd_data=[0xff])
                        else:
                            color_l,color_a,color_b= tmp
                            _str=color_l+'|'+color_a+'|'+color_b
                            self.AI_Uart_CMD_String(cmd=0x0e,cmd_type=0x02,str_buf=_str)
                        # self.k210.flag_color_ex_recognize=0
                elif(self.k210.mode==APRILTAG_MODE and self.apriltag!=None):
                    if(self.k210.flag_apriltag_recognize):
                        tmp = self.apriltag.recognize()
                        if(tmp==None):
                            self.AI_Uart_CMD(0x01,0x0f,0x02,cmd_data=[0xff])
                        elif(tmp[0]==None):
                            self.AI_Uart_CMD(0x01,0x0f,0x02,cmd_data=[0xff])   
                        else:
                            tag_family,tag_id = tmp
                            _str=tag_family+'|'+tag_id
                            self.AI_Uart_CMD_String(cmd=0x0f,cmd_type=0x02,str_buf=_str)
                        # self.k210.flag_apriltag_recognize=0
                elif(self.k210.mode==KPU_YOLO_MODEL_MODE and self.kpu_yolo_model!=None):
                    if(self.k210.flag_kpu_yolol_recognize):
                        id,value = self.kpu_yolo_model.recognize()
                        if(id==None):
                            self.AI_Uart_CMD(0x01,0x10,0x03,cmd_data=[0xff])
                        else:
                            self.AI_Uart_CMD(0x01,0x10,0x03,cmd_data=[id,value])
                elif(self.k210.mode==FACTORY_MODE):
                    time.sleep_ms(15)
                    self.button_update_status()
                    self.tf_sn = self.sn_read()
                    if(self.k210.lcd_test):
                        self.lcd_test()
                    elif(self.k210.sensor_test):
                        self.sensor_test()
                    # self.AI_Uart_CMD(0x01,FACTORY_MODE,0x01,cmd_data=[self.btn_A_status,self.btn_B_status,self.tf_status])
                    self.AI_Uart_CMD_String(cmd=FACTORY_MODE,cmd_type=0x01,cmd_data=[self.btn_A_status,self.btn_B_status,self.tf_status],str_buf=str([self.tf_sn]))
            except Exception as e:
                s=str(e)
                print(s)
                print("==222==")
                lcd.draw_string(0,180, s, lcd.WHITE, lcd.BLUE)
                if(len(s)>30):
                    lcd.draw_string(0,220, s[31:-1], lcd.WHITE, lcd.BLUE)

    def reset(self):
        self.AI_Uart_CMD(0x01,0x01,0xFF)
        time.sleep_ms(10)
        machine.reset()
    
    def switcherMode(self, mode):
        if(mode==self.k210.mode or self.k210.sw_lock):
            print('switcherMode return')
            return
        
        self.k210.sw_lock = True
        if(self.k210.mode==GUIDEPOST_MODE):
            self.guidepost.__del__()
            del self.guidepost
            self.guidepost=None
        elif(self.k210.mode==TRACK_MODE):
            self.track.__del__()
            del self.track
            self.track=None
        elif(self.k210.mode==COLOR_STATISTICS_MODE):
            self.color_statistics.__del__()
            del self.color_statistics
            self.color_statistics=None
        elif(self.k210.mode==APRILTAG_MODE):
            self.apriltag.__del__()
            del self.apriltag
            self.apriltag=None
        elif(self.k210.mode==SELF_LEARNING_CLASSIFIER_MODE):
            self.slc.__del__()
            del self.slc
            self.slc=None
        elif(self.k210.mode==OBJECT_RECOGNIZATION_MODE):
            self.yolo_detect.__del__()
            del self.yolo_detect
            self.yolo_detect=None
        elif(self.k210.mode==FACE_DETECTION_MODE):
            self.face_detect.__del__()
            del self.face_detect
            self.face_detect=None
        
        time.sleep(0.1)
        _cmd = self.uart.read()        
        del _cmd
        gc.collect()
        
        self.k210 = self.K210()

        for i in range(3):
            self.AI_Uart_CMD(0x01,0x01,0xFE)
            time.sleep(0.1)
    
        self.lcd.draw_string(0,225, 'switcher mode', lcd.WHITE, lcd.BLUE)
        self.k210.sw_lock = False
        print('===switcher mode===')
  

    def change_camera(self,_framesize=sensor.QVGA,_pixformat=sensor.RGB565,_w=320,_h=240,_vflip=0,_hmirror=0,_brightness=0,_contrast=0,_saturation=0,_gain=0,_whitebal=0,_freq=24000000,_dual_buff=False):
        try:
            # self.sensor.reset(choice=_choice,freq=_freq,dual_buff=_dual_buff)
            self.sensor.reset(freq=_freq,dual_buff=_dual_buff)
            self.sensor.set_framesize(_framesize)
            self.sensor.set_pixformat(_pixformat)
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
            time.sleep(3)
        
        self.sensor.set_vflip(_vflip) 
        self.sensor.set_hmirror(_hmirror) #水平镜像
        self.sensor.set_contrast(_contrast) #对比度
        self.sensor.set_saturation(_saturation) #饱和度
        self.sensor.set_brightness(_brightness) #亮度
        self.sensor.set_auto_whitebal(_whitebal)
        self.sensor.set_auto_gain(_gain)
        self.sensor.set_windowing((_w,_h))
        self.sensor.skip_frames(10)
        self.sensor.run(1)
        time.sleep(0.1)

    def record(self, path="/sd/capture.avi", interval=100000, quality=50, width=320, height=240, duration=10):
        # self.lcd.init(freq=15000000, invert=1)
        self.sensor.reset()
        self.sensor.set_pixformat(sensor.RGB565)
        self.sensor.set_framesize(sensor.QVGA)
        self.sensor.set_windowing((width, height))
      
        self.sensor.run(1)
        self.sensor.skip_frames(30) 

        v = video.open(path, audio=False, record=True, interval=interval, quality=quality)

        fm.register(12, fm.fpioa.GPIOHS0, force=True)
        key = GPIO(GPIO.GPIOHS0, GPIO.PULL_UP)
 
        while True:
            time.sleep_ms(20)
            img = self.sensor.snapshot()
            Draw_CJK_String('按A键开始录制', 40, 5, img, color=(0, 255, 0))
            self.lcd.display(img)
            if key.value() == 0:
                time.sleep_ms(30)
                if key.value() == 0:
                    Draw_CJK_String('开始录制', 40, 20, img, color=(0, 255, 0))
                    self.lcd.display(img)
                    time.sleep_ms(500)
                    break

        for i in range(int(duration*1000000/interval)):
            img = self.sensor.snapshot()
            self.lcd.display(img)
            img_len = v.record(img)

        print("record_finish")
        v.record_finish()
        v.__del__()
        gc.collect()
        self.lcd.clear()
        print(path)
        print(v)
        return path


    def play(self, path="/sd/capture.avi"):
        # play avi
        self.lcd.init(freq=15000000, invert=1)
        v = video.open(path)
        print(path)
        v.volume(50)
        while True:
            if v.play() == 0:
                # print("play end")
                break

        print("play finish")
        v.__del__()
        gc.collect()
        self.lcd.clear()
    
    def init_canvas(self):
        self.img =  image.Image('/flash/white240.jpg', copy_to_fb=True)
        self.lcd.display(self.img)
        # self.img =  image.Image().invert()
    
    def clear_canvas(self):
        self.img =  image.Image('/flash/white240.jpg', copy_to_fb=True)
        self.lcd.display(self.img)
        # self.lcd.clear(lcd.WHITE)
 
    def canvas_txt(self,txt,scale,x,y):
        # Draw_CJK_String(txt, x, y, self.img, color=(0, 0, 0))
        image.font_load(image.UTF8,16,16,0x645000)
        self.img.draw_string(x,y,txt,color=(0,0,0),scale=scale,x_spacing=2,mono_space=1)
        image.font_free()
        self.lcd.display(self.img)
    
    def sd_test(self):
        import os
        flag = False
        flag_sd = False

        for v in os.listdir('/'):
            if v == 'sd':
                flag_sd = True
                with open("/sd/_sd.txt", "w") as f:
                    f.close()

        if flag_sd:
            for v in os.listdir('/sd'):
                if v == '_sd.txt':
                    flag = True

        return flag
    
    def lcd_test(self):
        self.k210.sensor_test = False
        COLOR = [lcd.WHITE,lcd.BLACK,lcd.RED,lcd.GREEN,lcd.BLUE]
        for i in range(5):
            self.lcd.clear(COLOR[i])
            time.sleep(1)
        self.k210.lcd_test = False

    def sensor_test(self):
        self.lcd.display(self.sensor.snapshot())

    # def rgb_test(self):
    #     for i in range(2):
    #         self.rgb.set_led(0,128,0) 
    #         time.sleep(1)
    #         self.rgb.off()
    
    def led_test(self):
        for i in range(2):
            self.led.on()
            time.sleep(1.5)
            self.led.off()

    def button_update_status(self):
        self.btn_A_status = self.btn_A.is_pressed()
        self.btn_B_status = self.btn_B.is_pressed() 
    
    def sn_write(self,sn):
        for v in os.listdir('/'):
            if v == 'flash':
                with open("/flash/_sn.txt", "w") as f:
                    f.close()
            
                with open("/flash/_sn.txt", "a") as f:
                    f.write(str(sn))
                    f.write("\n")
                    f.close()
        
    def sn_read(self):
        flag = False
        sn =  ''
        for v in os.listdir('/'):
            if v == 'flash': 
                for v in os.listdir('/flash'):
                    if v == '_sn.txt':
                        flag = True
                        break
            
            if(flag):
                with open("/flash/_sn.txt", "r") as f:
                    sn = f.readline().rstrip()
                    f.close()
                
                return sn
            else:
                return ''
    
       
    
try:
    aiCamera=AICamera()
except Exception as e:
    lcd.clear((0, 0, 255))
    s=str(e)
    print(s)
    lcd.draw_string(0,200, s, lcd.WHITE, lcd.BLUE)
    if(len(s)>20):
        lcd.draw_string(0,220, s[21:-1], lcd.WHITE, lcd.BLUE)