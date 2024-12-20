import time
import gc

class YOLO_DETECT(object):
    def __init__(self,sensor,kpu,lcd):
        self.lcd =lcd
        self.sensor = sensor
        self.kpu = kpu

        self.clock = time.clock()
        self.classes = ['aeroplane', 'bicycle', 'bird', 'boat', 'bottle', 'bus', 'car', 'cat', 'chair', 'cow', 'diningtable', 'dog', 'horse', 'motorbike', 'person', 'pottedplant', 'sheep', 'sofa', 'train', 'tvmonitor']
        self.task = self.kpu.load(0x450000)
        self.anchor = (1.08, 1.19, 3.42, 4.41, 6.63, 11.38, 9.42, 5.11, 16.62, 10.52)
        a = self.kpu.init_yolo2(self.task, 0.5, 0.3, 5, self.anchor)
        self.change_camera()
        time.sleep(0.5)
        # self.kpu.memtest()
    
    def recognize(self):
        self.clock.tick()
        img = self.sensor.snapshot()
        code = self.kpu.run_yolo2(self.task, img)
        if code:
            for i in code:
                a=img.draw_rectangle(i.rect(), color=(0,255,0), thickness=2)
                a=self.lcd.display(img)
                self.lcd.draw_string(i.x(), i.y(), self.classes[i.classid()], self.lcd.GREEN, self.lcd.WHITE)
                # print(i.classid())
            return code[0].classid(),int(round(code[0].value(),2)*100),code[0].objnum()
            # return code[0].classid(),int(round(code[0].value(),2)*100)
        else:
            a = self.lcd.display(img)
            return None,None,None

    def __del__(self):
        a = self.kpu.deinit(self.task)
        del self.task
        gc.collect()

    def change_camera(self):
        try:
            self.sensor.reset(freq=24000000)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((320,240))
            # self.sensor.set_hmirror(1)
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        
        # if(choice==1 and self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        self.sensor.skip_frames(30)
        self.sensor.run(1)
