
import time
import gc

class Guidepost(object):
    def __init__(self,sensor=None,kpu=None,lcd=None):
        try:
            gc.collect()
            self.lcd =lcd
            self.sensor = sensor
            self.kpu = kpu
            self.task = self.kpu.load(0xc50000)
            # self.task = self.kpu.load('/sd/qingjiao3.kmodel')
            self.img = None
            # self.fmap = None
            self.lcd.clear()
            self.labels = ["stop","none","left","right"]
            self.change_camera()
        except Exception:
            try:
                self.__del__()
            except Exception as release_error:
                print("[model init release]", release_error)
                raise RuntimeError("KPU_RELEASE_FAILED")
            raise
    
    def recognize(self):
        self.kpu.memtest()
        # print('==Guidepost==')
        self.img = self.sensor.snapshot()
        print(self.img.width())
        try:
            fmap = self.kpu.forward(self.task, self.img)
        except Exception as e:
            print(e)
            print('==Guidepost Error==')
            return None, None
        plist=fmap[:]
        pmax=max(plist)
        max_index=plist.index(pmax)
        a = self.lcd.display(self.img, oft=(24,24))
        del a
        self.kpu.fmap_free(pmax)
        if(pmax>0.7):
            self.lcd.draw_string(5, 5, "id:%s"%(self.labels[max_index].strip()), self.lcd.GREEN)
            return max_index,int(round(pmax,2)*100)
        else:
            self.lcd.draw_string(5, 5, "id:       ",  self.lcd.GREEN)
            return None,None

    def __del__(self):
        task = getattr(self, "task", None)
        if task is not None:
            self.task = None
            self.kpu.deinit(task)

    def change_camera(self):
        try:
            # self.sensor.reset()
            self.sensor.reset(freq=24000000)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((192, 192))
        except Exception as e:
            print("[camera init]", e)
            raise
        
        # if(choice==1 and self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        
        self.sensor.skip_frames(30)
        self.sensor.run(1)
        time.sleep(0.1)

# t = Guidepost(1)
# while 1:
#     t.recognize()

