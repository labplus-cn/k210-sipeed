
import time

class KPU_KMODEL(object):
    def __init__(self,choice=1,sensor=None,kpu=None,lcd=None,model=0xc50000,width=128,height=128):
        self.lcd =lcd
        self.sensor = sensor
        self.kpu = kpu
        self.task = self.kpu.load(model)
        self.lcd.clear()
        # self.labels = ["stop","none","left","right"]
        self.width = width
        self.height = height

        self.change_camera(choice=choice)
    
    def recognize(self):
        img = self.sensor.snapshot()
        # img=img.resize(128,128)         #resize to mnist input 128x128
        fmap = self.kpu.forward(self.task, img)
        plist=fmap[:]
        pmax=max(plist)
        max_index=plist.index(pmax)
        a = self.lcd.display(img, oft=(60,0))
        if(pmax>=0.7):
            self.lcd.draw_string(240, 0, "id:%s"%(max_index), self.lcd.GREEN)
            return max_index,int(round(pmax,2)*100)
        else:
            self.lcd.draw_string(240, 0, "id:       ",  self.lcd.GREEN)
            return None,None

    def __del__(self):
        a = self.kpu.deinit(self.task)

    def change_camera(self, choice):
        try:
            self.sensor.reset(choice=choice)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_hmirror(1)
            self.sensor.set_windowing((self.width, self.height))
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        
        if(choice==1 and self.sensor.get_id()==0x2642):
            self.sensor.set_vflip(1)
            self.sensor.set_hmirror(1)
        elif(choice==1 and self.sensor.get_id()==0x5640):
            self.sensor.set_vflip(0)
            self.sensor.set_hmirror(0)
        else:
            self.sensor.set_vflip(0)
            self.sensor.set_hmirror(0)
        
        self.sensor.skip_frames(30)
        self.sensor.run(1)
        time.sleep(1)


