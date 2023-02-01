
import time
import gc

class Guidepost(object):
    def __init__(self,choice=1,sensor=None,kpu=None,lcd=None):
        self.lcd =lcd
        self.sensor = sensor
        self.kpu = kpu
        self.task = self.kpu.load(0xc50000)
        self.lcd.clear()
        self.labels = ["stop","none","left","right"]

        self.change_camera(choice=choice)
    
    def recognize(self):
        img = self.sensor.snapshot()
        fmap = self.kpu.forward(self.task, img)
        plist=fmap[:]
        pmax=max(plist)
        max_index=plist.index(pmax)
        a = self.lcd.display(img, oft=(40,0))
        if(pmax>0.75):
            self.lcd.draw_string(240, 0, "id:%s"%(self.labels[max_index].strip()), self.lcd.GREEN)
            # self.lcd.draw_string(200, 0, "pmax:%.2f"%(pmax), self.lcd.GREEN)
            # self.lcd.draw_string(200, 15, "id:%s"%(self.labels[max_index].strip()), self.lcd.GREEN)
            return max_index,int(round(pmax,2)*100)
        else:
            # self.lcd.draw_string(200, 0, "pmax:      ", self.lcd.GREEN)
            self.lcd.draw_string(240, 0, "id:       ",  self.lcd.GREEN)
            return None,None

    def __del__(self):
        a = self.kpu.deinit(self.task)
        del self.task
        gc.collect()

    def change_camera(self, choice):
        try:
            self.sensor.reset(choice=choice)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_hmirror(1)
            self.sensor.set_windowing((192, 192))
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
        time.sleep(1)

# t = Guidepost(1)
# while 1:
#     t.recognize()

