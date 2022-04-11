import image
import sensor
import lcd
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String

class color_recognization(object):
    def __init__(self, choice=1):
        self.lcd = lcd
        self.sensor = sensor
        self.roi = [135,95,60,60]
        self.mylist = [0,0,0]
        # green_threshold = (0, 80, -70, -10, -0, 30)
        self.threshold_list = []

        fm.register(16, fm.fpioa.GPIOHS0+16)
        self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)

        self.change_camera(choice=choice)
        time.sleep(3)
    
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
        self.sensor.skip_frames(10)

    def add_color(self,num):
        mylist = [0,0,0]
        index = -1
        while True:
            img = self.sensor.snapshot()

            #设置识别颜色的区域
            img = img.draw_rectangle(self.roi,image.lab_to_rgb(mylist),2,0)

            #创建直方图对象
            color = img.get_histogram(roi=self.roi)

            #创建阈值对象
            # threshold = color.get_threshold()
            # L = threshold.l_value()
            # A = threshold.a_value()
            # B = threshold.b_value()
            # img.draw_string(35,35, 'L:{0},A:{1},B:{2}'.format(L,A,B), scale=2) 

            #计算直方图频道的CDF
            mylist[0]=color.get_percentile(0.5).l_value()
            mylist[1]=color.get_percentile(0.5).a_value()
            mylist[2]=color.get_percentile(0.5).b_value()
            
            rgb=image.lab_to_rgb(mylist)
            img.draw_string(5, 215, 'R:{0},G:{1},B:{2}'.format(rgb[0],rgb[1],rgb[2]), scale=2, color=rgb)

            #统计数据对象
            statistics = color.get_statistics()
            LAB = (statistics.l_min(),statistics.l_max(),statistics.a_min(),statistics.a_max(),statistics.b_min(),statistics.b_max())

            Draw_CJK_String('按A键按顺序添加需识别颜色,颜色区域在中心框', 5, 5, img, color=(0, 128, 0))
            # Draw_CJK_String('', 5, 20, img, color=(0, 128, 0))
            if self.key.value() == 0:
                time.sleep_ms(30)
                if self.key.value() == 0:
                    index += 1
                    self.threshold_list.append(LAB)
                    Draw_CJK_String('添加待识别颜色，id：{0}'.format(index), 5, 20, img, color=(0, 0, 128))
                    # img.draw_string(5,35, 'L_min:{0},L_max:{1},A_min:{2},A_max:{3},B_min:{4},B_max:{5}'.format(LAB[0],LAB[1],LAB[2],LAB[3],LAB[4],LAB[5]), scale=1) 
                    self.lcd.display(img)
                    time.sleep_ms(3000)
                    if index >= num-1:
                        print(self.threshold_list)
                        del img
                        break
            lcd.display(img)

    def recognize(self):
        img=self.sensor.snapshot()
        img.draw_rectangle(self.roi,(0,255,0),2,0)
        Draw_CJK_String('识别中...', 5, 5, img, color=(0, 128, 0))
        img_roi = img.copy(roi=self.roi)
        id = None
        for i in range(len(self.threshold_list)):
            blobs_roi = img_roi.find_blobs([self.threshold_list[i]])
            blobs = img.find_blobs([self.threshold_list[i]])
            if blobs_roi:
                for b in blobs_roi:
                    pixels = b.pixels()
                    if(pixels>=2000):
                        id = i
                        Draw_CJK_String('ID：{0}'.format(id), self.roi[0], self.roi[1]-15, img, color=(0, 128, 0))
                        # print(b.pixels())
                        # print(id)
                        # print('-----------')
            # if blobs:
            #     for b in blobs:
            #         if(b.w()*b.h()>2000):
            #             id = i
            #             Draw_CJK_String('id：{0}'.format(id), self.roi[0], self.roi[1]-15, img, color=(0, 128, 0))
            #             tmp=img.draw_rectangle([b.x(), b.y(), b.w(), b.h()])
        self.lcd.display(img)
        return id



# t = color_recognization(1)
# t.add_color(3)

# while True:
#     print(t.recognize())