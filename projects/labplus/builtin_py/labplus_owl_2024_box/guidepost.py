
import time
import gc

class Guidepost(object):
    def __init__(self,sensor=None,kpu=None,lcd=None):
        self.lcd =lcd
        self.sensor = sensor
        self.kpu = kpu
        self.task = self.kpu.load(0xc50000)
        # self.task = self.kpu.load('/sd/qingjiao3.kmodel')
        self.img = None
        self.fmap = None
        self.lcd.clear()
        self.labels = ["stop","none","left","right"]
        self.change_camera()
        self.kpu.memtest()
    
    def recognize(self):
        gc.collect()
        # print('==Guidepost==')
        self.img = self.sensor.snapshot()
        try:
            self.fmap = self.kpu.forward(self.task, self.img)
        except Exception as e:
            print(e)
        plist=self.fmap[:]
        pmax=max(plist)
        max_index=plist.index(pmax)
        a = self.lcd.display(self.img, oft=(40,40))
        self.kpu.fmap_free(pmax)
        if(pmax>0.7):
            self.lcd.draw_string(160, 0, "id:%s"%(self.labels[max_index].strip()), self.lcd.GREEN)
            return max_index,int(round(pmax,2)*100)
        else:
            self.lcd.draw_string(160, 0, "id:       ",  self.lcd.GREEN)
            return None,None

    def __del__(self):
        a = self.kpu.deinit(self.task)
        print('kpu.deinit:{}'.format(a))
        del self.task
        del self.fmap
        # del self.img
        # del self.lcd
        # del self.sensor
        # del self.kpu
        gc.collect()

    def change_camera(self):
        try:
            self.sensor.reset(freq=24000000)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((192, 192))
            self.sensor.set_hmirror(1)
            # self.sensor.set_vflip(1)
            # self.sensor.set_brightness(-1) #亮度
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        
        self.sensor.skip_frames(30)
        self.sensor.run(1)
        time.sleep(1)

# t = Guidepost(1)
# while 1:
#     t.recognize()

