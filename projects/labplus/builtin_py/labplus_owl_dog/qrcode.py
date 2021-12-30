import image
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String

class QRCode_recognization(object):
    def __init__(self, lcd, sensor, choice=1):
        self.lcd = lcd
        self.sensor = sensor
        self.QRCodeName = [None]*20
        # self.qrcode_num = qrcode_num

        fm.register(16, fm.fpioa.GPIOHS0+16)
        self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)

        self.change_camera(choice=choice)
        time.sleep(3)

    def add_qrcode(self, id):
        while True:
            img = self.sensor.snapshot()
            res = img.find_qrcodes()
            Draw_CJK_String('按A键添加二维码数据', 5, 5, img, color=(0, 255, 0))
            if len(res)>0:
                gc.collect()
                img.draw_rectangle(res[0].rect(), color=(0,255,0))
                Draw_CJK_String('二维码数据：{0}'.format(res[0].payload()), 5, 18, img, color=(0, 255, 0))
                if self.key.value() == 0:
                    time.sleep_ms(30)
                    if self.key.value() == 0:
                        self.QRCodeName[id] = res[0].payload()
                        Draw_CJK_String('添加二维码, id={0}'.format(id), 5, 30, img, color=(0, 0, 128))
                        Draw_CJK_String('二维码数据: {0}'.format(res[0].payload()), 5, 43, img, color=(0, 0, 128))
                        self.lcd.display(img)
                        time.sleep(3)
                        return
                    break 
            a = self.lcd.display(img)
            gc.collect()     
            
    def recognize(self):
        img = self.sensor.snapshot()
        res = img.find_qrcodes()
        Draw_CJK_String('识别中...', 5, 5, img, color=(0, 255, 0))
        index =  None
        if len(res)>0:
            for i in res:
                gc.collect()
                img.draw_rectangle(res[0].rect(), color=(0,255,0))
                for j in range(len(self.QRCodeName)): 
                    if(self.QRCodeName[j]==i.payload()):
                        index = j
                        Draw_CJK_String('id={0}'.format(j), i.x()+5, i.y()+5, img, color=(0, 255, 0))
                Draw_CJK_String('二维码数据: {0}'.format(i.payload()), 5, 18, img, color=(0, 255, 0))
                break 
        a = self.lcd.display(img)
        gc.collect()    
        return index #否则返回None
    
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
            self.sensor.set_vflip(0)
        self.sensor.set_hmirror(1)
        self.sensor.run(1)
       