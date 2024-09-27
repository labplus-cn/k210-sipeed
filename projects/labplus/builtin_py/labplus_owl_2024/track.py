

def upRange(start, stop, step):
    while start <= stop:
        yield start
        start += abs(step)

def downRange(start, stop, step):
    while start >= stop:
        yield start
        start -= abs(step)

def find_max(smart_camera_blobs_ret):
    max_size = 0
    for blob in smart_camera_blobs_ret:
        if blob.w()*blob.h() > max_size:
            max_blob = blob
            max_size = blob.w()*blob.h()
    return max_blob


import image
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String


blobs = None
blob_num = None

class Track(object):
    def __init__(self, lcd=None, sensor=None, choice=1, threshold=[[0, 80, 15, 127, 15, 127]], area_threshold=50):
        self.lcd = lcd
        self.sensor = sensor
        self.lcd.init(freq=15000000, invert=1)
        self.threshold = threshold
        self.area_threshold = area_threshold
        self.img = None

        # self.change_camera(choice=choice)
        if(choice==1 and self.sensor.get_id()==0x2642):
            self.sensor.set_vflip(1)
            self.sensor.set_hmirror(1)
        elif(choice==1 and self.sensor.get_id()==0x5640):
            self.sensor.set_vflip(0)
            self.sensor.set_hmirror(0)
        
        # self.init_data()
        # self.load_data()
        time.sleep(0.5)
        # self.index = -1
        # self.flag_add = 0
    
    def change_camera(self, choice):
        try:
            # self.sensor.reset(choice=choice)  
            self.sensor.reset(freq=18000000)
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        self.sensor.set_framesize(self.sensor.QQVGA)
        self.sensor.set_pixformat(self.sensor.RGB565)
        # if(choice==1 and self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        # elif(choice==1 and self.sensor.get_id()==0x5640):
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)
        # else:
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)
        #     self.sensor.set_brightness(2)
        #     self.sensor.set_contrast(-1)
        #     self.sensor.set_saturation(0)
        #     self.sensor.set_auto_gain(0)
        self.sensor.run(1)
        self.sensor.skip_frames(20)

    def recognize(self):
        self.img = self.sensor.snapshot()
        self.img.draw_string(1,1, ("track color..."), color=(0,128,0),scale=1)
        smart_camera_blobs_ret = self.img.find_blobs(self.threshold, area_threshold=self.area_threshold, merge=True)
        blobs = smart_camera_blobs_ret
        
        if blobs:
            blob_num = len(blobs)
            b_end = int(blob_num - 1)
            for b in (0 <= b_end) and upRange(0, b_end, 1) or downRange(0, b_end, 1):
                self.img.draw_rectangle(smart_camera_blobs_ret[b].x(), smart_camera_blobs_ret[b].y(), smart_camera_blobs_ret[b].w(), smart_camera_blobs_ret[b].h(), color=(0, 128, 0), fill=False)
            
            x = find_max(smart_camera_blobs_ret).x()
            y = find_max(smart_camera_blobs_ret).y()
            cx = find_max(smart_camera_blobs_ret).cx()
            cy = find_max(smart_camera_blobs_ret).cy()
            w = find_max(smart_camera_blobs_ret).w()
            h = find_max(smart_camera_blobs_ret).h()
            pixels = find_max(smart_camera_blobs_ret).pixels()
            count = find_max(smart_camera_blobs_ret).count()
            code = find_max(smart_camera_blobs_ret).code()
            self.lcd.display(self.img)
            gc.collect()
            return x,y,cx,cy,w,h,pixels,count,code
        else:
            del smart_camera_blobs_ret
            self.lcd.display(self.img)
            gc.collect()
            return None,None,None,None,None,None,None,None,None

    def set_up(self,threshold, area_threshold):
        self.threshold = threshold
        self.area_threshold = area_threshold

    def __del__(self):
        del self.img
        del self.lcd
        gc.collect()

# t = Track(lcd=lcd,sensor=sensor,choice=1)

# while True:
#     t.recognize()
