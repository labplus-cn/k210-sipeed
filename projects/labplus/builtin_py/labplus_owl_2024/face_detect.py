import time
import gc

class FACE_DETECT(object):
    def __init__(self,sensor,kpu,lcd):
        self.lcd =lcd
        self.sensor = sensor
        self.kpu = kpu
        self.kpu.memtest()
        self.lcd.rotation(1)
        self.clock = time.clock()
        self.task = self.kpu.load(0x300000)
        self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025) 
        a = self.kpu.init_yolo2(self.task, 0.5, 0.3, 5, self.anchor)
        self.change_camera()
        time.sleep(1)
    
    def recognize(self):
        # self.kpu.memtest()
        self.clock.tick()
        img = self.sensor.snapshot()
        code = self.kpu.run_yolo2(self.task, img)
        if code:
            for i in code:
                a=img.draw_rectangle(i.rect(), color=(0,255,0), thickness=2)
                a = self.lcd.display(img)
            return code[0].objnum(),int(round(code[0].value(),2)*100)
        else:
            a = self.lcd.display(img)
            return None,None

    def __del__(self):
        a = self.kpu.deinit(self.task)
        print('kpu.deinit:{}'.format(a))
        del self.task
        gc.collect()


    def change_camera(self):
        try:
            self.sensor.reset(freq=24000000)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_brightness(-1) #亮度
        except Exception as e:
            self.lcd.clear((0, 0, 255))
            self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
        
        # if(choice==1 and self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        # elif(choice==1 and self.sensor.get_id()==0x5640):
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)
        # else:
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)
        
        self.sensor.skip_frames(30)
        self.sensor.run(1)


# t = FACE_DETECT(1)
# while 1:
#     t.recognize()