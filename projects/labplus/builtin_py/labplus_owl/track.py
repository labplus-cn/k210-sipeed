

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

img = None
blobs = None
blob_num = None


# import sensor
# import lcd


class Track(object):
    def __init__(self, lcd=None, sensor=None, choice=1, threshold=[0, 80, 15, 127, 15, 127], area_threshold=50):
        self.lcd = lcd
        self.sensor = sensor
        self.roi = [135,95,60,60]
        self.mylist = [0,0,0]
        self.threshold = threshold
        self.area_threshold = area_threshold
        self.threshold_list = []
        self.color_file_exits = 0

        # fm.register(16, fm.fpioa.GPIOHS0+16)
        # self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)

        self.change_camera(choice=choice)
        # self.init_data()
        # self.load_data()
        time.sleep(1)
        # self.index = -1
        # self.flag_add = 0
    
    def change_camera(self, choice):
        try:
            self.sensor.reset(choice=choice)  
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        self.sensor.set_framesize(self.sensor.QQVGA)
        self.sensor.set_pixformat(self.sensor.RGB565)
        if(choice==1):
            self.sensor.set_vflip(1)
        else:
            self.sensor.set_vflip(0)
        self.sensor.set_hmirror(1)
        self.sensor.run(1)
        self.sensor.skip_frames(10)

    def recognize(self):
        # img.draw_rectangle(self.roi,(0,255,0),2,0)
        self.img = self.sensor.snapshot()
        Draw_CJK_String('巡线识别中...', 5, 5, self.img, color=(0, 128, 0))
        smart_camera_blobs_ret = self.img.find_blobs([self.threshold], area_threshold=self.area_threshold, merge=True)
        blobs = smart_camera_blobs_ret
        
        if blobs:
            blob_num = len(blobs)
            b_end = int(blob_num - 1)
            for b in (0 <= b_end) and upRange(0, b_end, 1) or downRange(0, b_end, 1):
                self.img.draw_rectangle(smart_camera_blobs_ret[b].x(), smart_camera_blobs_ret[b].y(), smart_camera_blobs_ret[b].w(), smart_camera_blobs_ret[b].h(), color=(255, 0, 0), fill=False)
            
            x = find_max(smart_camera_blobs_ret).x()
            y = find_max(smart_camera_blobs_ret).y()
            cx = find_max(smart_camera_blobs_ret).cx()
            cy = find_max(smart_camera_blobs_ret).cy()
            w = find_max(smart_camera_blobs_ret).w()
            h = find_max(smart_camera_blobs_ret).h()
            pixels = find_max(smart_camera_blobs_ret).pixels()
            count = find_max(smart_camera_blobs_ret).count()
            self.lcd.display(self.img)
            gc.collect()
            return x,y,cx,cy,w,h,pixels,count
        else:
            del smart_camera_blobs_ret
            self.lcd.display(self.img)
            gc.collect()
            return None,None,None,None,None,None,None,None

    def __del__(self):
        del self.img
        del self.lcd
        gc.collect()

# t = Track(lcd=lcd,sensor=sensor,choice=1)

# while True:
#     t.recognize()
