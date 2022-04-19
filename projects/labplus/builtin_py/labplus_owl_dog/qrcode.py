import image
import sensor
import lcd
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String

class QRCode_recognization(object):
    def __init__(self, choice=1):
        self.lcd = lcd
        self.sensor = sensor
        self.QRCodeName = []
        self.qrcode_file_exits = 0
        self.init_data()
        self.load_data()

        fm.register(16, fm.fpioa.GPIOHS0+16)
        self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)

        self.change_camera(choice=choice)
        time.sleep(3)

    def add_qrcode(self, num):
        self.clear_data()
        index = -1
        info = None
        while True:
            img = self.sensor.snapshot()
            res = img.find_qrcodes()
            Draw_CJK_String('按A键添加二维码数据id:', 5, 5, img, color=(0, 128, 0))
            if len(res)>0:
                gc.collect()
                img.draw_rectangle(res[0].rect(), color=(0,255,0))
                Draw_CJK_String('按A键添加二维码数据id:{0}'.format(index+1), 5, 5, img, color=(0, 128, 0))
                Draw_CJK_String('二维码数据：{0}'.format(res[0].payload()), 5, 18, img, color=(0, 128, 0))
                if self.key.value() == 0:
                    time.sleep_ms(30)
                    if self.key.value() == 0:
                        index += 1
                        info = res[0].payload()
                        self.QRCodeName.append(info)
                        self.save_data(info)
                        Draw_CJK_String('已添加二维码, id:{0}'.format(index), 5, 30, img, color=(0, 0, 128))
                        Draw_CJK_String('二维码数据: {0}'.format(info), 5, 43, img, color=(0, 0, 128))
                        self.lcd.display(img)
                        time.sleep(3)
                        if index >= num-1:
                            # print(self.QRCodeName)
                            del img
                            break
                    # break 
            a = self.lcd.display(img)
            gc.collect()     
            
    def recognize(self):
        img = self.sensor.snapshot()
        res = img.find_qrcodes()
        Draw_CJK_String('识别中...', 5, 5, img, color=(0, 128, 0))
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
                Draw_CJK_String('二维码数据: {0}'.format(info), 5, 18, img, color=(0, 128, 0))
                break 
        a = self.lcd.display(img)
        gc.collect()    
        return index,info #否则返回None
    
    def change_camera(self, choice):
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
            self.sensor.set_brightness((-1))
            self.sensor.set_vflip(1)
        self.sensor.set_hmirror(1)
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