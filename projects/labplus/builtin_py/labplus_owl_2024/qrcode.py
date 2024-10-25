import image
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String

class QRCode(object):
    def __init__(self, lcd=None, sensor=None):
        self.lcd = lcd
        self.sensor = sensor
        self.QRCodeName = []
        self.qrcode_file_exits = 0
        self.init_data()
        self.load_data()

        fm.register(12, fm.fpioa.GPIOHS0, force=True)
        self.key = GPIO(GPIO.GPIOHS0, GPIO.PULL_UP)

        self.change_camera()
        time.sleep(1)
        self.index = -1
        self.flag_add = 0

    def add_qrcode(self, num):
        # self.clear_data()
        # index = -1
        self.flag_add = 1
        info = None
        # while True:add_face
        img = self.sensor.snapshot()
        res = img.find_qrcodes()
        Draw_CJK_String('按A键添加二维码数据id:', 40, 5, img, color=(0, 128, 0))
        if len(res)>0:
            gc.collect()
            img.draw_rectangle(res[0].rect(), color=(0,255,0))
            Draw_CJK_String('按A键添加二维码数据id:{0}'.format(self.index+1), 40, 5, img, color=(0, 128, 0))
            Draw_CJK_String('二维码数据：{0}'.format(res[0].payload()), 40, 18, img, color=(0, 128, 0))
            if self.key.value() == 0:
                time.sleep_ms(30)
                if self.key.value() == 0:
                    self.index += 1
                    info = res[0].payload()
                    self.save_data(info)
                    self.QRCodeName.append(info)
                    Draw_CJK_String('已添加二维码, id:{0}'.format(self.index), 40, 30, img, color=(0, 0, 128))
                    Draw_CJK_String('二维码数据: {0}'.format(info), 40, 43, img, color=(0, 0, 128))
                    self.lcd.display(img)
                    time.sleep(3)
                    if self.index >= num-1:
                        # print(self.QRCodeName)
                        self.index = -1
                        self.flag_add = 0
                        gc.collect()
                        # break
                # break 
        self.lcd.display(img)
        del img
        gc.collect()     
            
    def recognize(self):
        img = self.sensor.snapshot()
        res = img.find_qrcodes()
        Draw_CJK_String('识别中...', 40, 5, img, color=(0, 128, 0))
        index =  None
        info = None
        if len(res)>0:
            info = res[0].payload()
            for i in res:
                gc.collect()
                img.draw_rectangle(res[0].rect(), color=(0,128,0))
                for j in range(len(self.QRCodeName)): 
                    if(self.QRCodeName[j]==i.payload()):
                        index = j
                        info = i.payload()
                        Draw_CJK_String('ID：{0}'.format(j), i.x(), i.y()-15, img, color=(0, 128, 0))
                Draw_CJK_String('二维码数据: {0}'.format(info), 40, 18, img, color=(0, 128, 0))
                # break 
        a = self.lcd.display(img)
        del img
        gc.collect()    
        return index,info #否则返回None
    
    def change_camera(self):
        try:
            self.sensor.reset(freq=24000000)
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        self.sensor.set_framesize(self.sensor.QVGA)
        self.sensor.set_pixformat(self.sensor.RGB565)
        self.sensor.set_windowing((240,240))
        # if(choice==1 and self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
  
        self.sensor.skip_frames(30)
        self.sensor.run(1)
    
        #保存数据
    def save_data(self, record):
        with open("/flash/_qrcode_record.txt", "a") as f:
            f.write(str(record))
            f.write("\n")
            f.close()

    #载入数据
    def load_data(self):
        if(self.qrcode_file_exits):
            with open("/flash/_qrcode_record.txt", "r") as f:
                while(1):
                    line = f.readline()
                    if not line:
                        break
                    self.QRCodeName.append(line.rstrip())
                    time.sleep_ms(5)
                f.close()

    #初始化数据
    def init_data(self):
        import os
        for v in os.listdir('/flash'):
            if v == '_qrcode_record.txt':
                self.qrcode_file_exits = 1
    
        if(self.qrcode_file_exits==0):
            with open("/flash/_qrcode_record.txt", "w") as f:
                f.close()

    #清空数据
    def clear_data(self):
        self.QRCodeName = []
        with open("/flash/_qrcode_record.txt", "w") as f:
            f.close()
        time.sleep_ms(3)

class Apriltag(object):
    def __init__(self, lcd=None, sensor=None):
        self.lcd = lcd
        self.sensor = sensor
        #不可修改
        self.sensor.set_auto_gain(False)
        self.sensor.set_auto_whitebal(False)
        self.sensor.set_windowing((240,240))
        # if(self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        # elif(self.sensor.get_id()==0x5640):
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)

        self.img = None
        self.tag_args = (None,None)
        self.tag_families = image.TAG36H11
        self.tag_families |= 0
        time.sleep(0.1)

    def set_families(self,user_tag_families):
        self.tag_families |= user_tag_families

    def recognize(self):
        gc.collect()
        try:
            self.img = self.sensor.snapshot()
            _tag_list = self.img.find_apriltags(families=self.tag_families)
            if(len(_tag_list)):
                for tag in _tag_list:
                    self.img.draw_rectangle(tag.rect(), color = (255, 0, 0))
                    # self.img.draw_cross(tag.cx(), tag.cy(), color = (0, 255, 0))
                    self.img.draw_string(tag.x(),tag.y()-20,"id:%s"%tag.id(), color=(0,128,0), scale=2)
                    self.tag_args = (tag.family(), tag.id())
                    # print(tag_args)
                    self.lcd.display(self.img)
                    return str(self.tag_args[0]),str(self.tag_args[1])
            else:
                self.lcd.display(self.img)
                return (None,None)
        except Exception as e:
            return (None,None)
        
    def __del__(self):
        del self.img
        del self.lcd
        gc.collect()
        