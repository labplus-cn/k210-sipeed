import image
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String

class Color(object):
    def __init__(self, lcd=None, sensor=None, choice=1):
        self.lcd = lcd
        self.sensor = sensor
        self.roi = [135,95,60,60]
        self.mylist = [0,0,0]
        # green_threshold = (0, 80, -70, -10, -0, 30)
        self.threshold_list = []
        self.color_file_exits = 0

        fm.register(12, fm.fpioa.GPIOHS0, force=True)
        self.key = GPIO(GPIO.GPIOHS0, GPIO.PULL_UP)

        self.change_camera(choice=choice)
        self.init_data()
        self.load_data()
        time.sleep(3)
        self.index = -1
        self.flag_add = 0
    
    def change_camera(self, choice):
        try:
            self.sensor.reset(freq=20000000)
            self.sensor.set_pixformat(self.sensor.RGB565)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_vflip(1)
            self.sensor.set_windowing((240,240))
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


    def add_color(self,num):
        self.flag_add = 1
        # self.clear_data()
        mylist = [0,0,0]
        # index = -1
        # while True:
        img = self.sensor.snapshot()

        #创建直方图对象
        color = img.get_histogram(roi=self.roi)

        #计算直方图频道的CDF
        mylist[0]=color.get_percentile(0.5).l_value()
        mylist[1]=color.get_percentile(0.5).a_value()
        mylist[2]=color.get_percentile(0.5).b_value()
        
        rgb=image.lab_to_rgb(mylist)
        #设置识别颜色的区域
        img = img.draw_rectangle(self.roi,image.lab_to_rgb(mylist),2,0)
        img.draw_string(5, 215, 'R:{0},G:{1},B:{2}'.format(rgb[0],rgb[1],rgb[2]), scale=2, color=rgb)

        #统计数据对象
        statistics = color.get_statistics()
        LAB = (statistics.l_min(),statistics.l_max(),statistics.a_min(),statistics.a_max(),statistics.b_min(),statistics.b_max())

        Draw_CJK_String('按A键按顺序添加需识别颜色,颜色区域在中心框', 5, 5, img, color=(0, 128, 0))
        # Draw_CJK_String('', 5, 20, img, color=(0, 128, 0))
        if self.key.value() == 0:
            time.sleep_ms(30)
            if self.key.value() == 0:
                self.index += 1
                self.threshold_list.append(LAB)
                self.save_data(LAB)
                Draw_CJK_String('添加待识别颜色，id：{0}'.format(self.index), 5, 20, img, color=(0, 0, 128))
                # img.draw_string(5,35, 'L_min:{0},L_max:{1},A_min:{2},A_max:{3},B_min:{4},B_max:{5}'.format(LAB[0],LAB[1],LAB[2],LAB[3],LAB[4],LAB[5]), scale=1) 
                self.lcd.display(img)
                time.sleep_ms(3000)
                if self.index >= num-1:
                    # print(self.threshold_list)
                    del img
                    # break
                    self.index = -1
                    self.flag_add = 0
                    gc.collect()
                    return
        self.lcd.display(img)
        del img
        gc.collect()

    def recognize(self):
        img=self.sensor.snapshot()
        img.draw_rectangle(self.roi,(0,255,0),2,0)
        Draw_CJK_String('识别中...', 5, 5, img, color=(0, 128, 0))
        img_roi = img.copy(roi=self.roi)
        id = None
        for i in range(len(self.threshold_list)):
            blobs_roi = img_roi.find_blobs([self.threshold_list[i]])
            # blobs = img.find_blobs([self.threshold_list[i]])
            if blobs_roi:
                for b in blobs_roi:
                    pixels = b.pixels()
                    if(pixels>=2000):
                        id = i
                        # Draw_CJK_String('ID：{0}'.format(id), self.roi[0], self.roi[1]-15, img, color=(0, 128, 0))
                        # self.lcd.draw_string(0, 50, '5:'+str(e), self.lcd.WHITE, self.lcd.BLUE)
                        # break
                    else:
                        id = None
                        pass
            del blobs_roi
        Draw_CJK_String('ID：{0}'.format(id), self.roi[0], self.roi[1]-15, img, color=(0, 128, 0))
        self.lcd.display(img)
        del img
        del img_roi
        gc.collect()
        return id
    
        #保存数据
    def save_data(self, record):
        print('color_record')
        with open("/flash/_color_record.txt", "a") as f:
            f.write(str(record))
            f.write("\n")
            f.close()

    #载入数据
    def load_data(self):
        if(self.color_file_exits):
            with open("/flash/_color_record.txt", "r") as f:
                while(1):
                    line = f.readline()
                    if not line:
                        break
                    self.threshold_list.append(eval(line))
                    time.sleep_ms(5)
                f.close()

    #初始化数据
    def init_data(self):
        import os
        for v in os.listdir('/flash'):
            if v == '_color_record.txt':
                self.color_file_exits = 1
    
        if(self.color_file_exits==0):
            with open("/flash/_color_record.txt", "w") as f:
                f.close()

    #清空数据
    def clear_data(self):
        self.threshold_list = []
        with open("/flash/_color_record.txt", "w") as f:
            f.close()
        time.sleep_ms(3)


roi1 = (18,22,10,10)
roi2 = (46,22,10,10)
roi3 = (74,22,10,10)
roi4 = (102,22,10,10)
roi5 = (130,22,10,10)
roi6 = (18,54,10,10)
roi7 = (46,54,10,10)
roi8 = (74,54,10,10)
roi9 = (102,54,10,10)
roi10 = (130,54,10,10)
roi11 = (18,86,10,10)
roi12 = (46,86,10,10)
roi13 = (74,86,10,10)
roi14 = (102,86,10,10)
roi15 = (130,86,10,10)

roi_list = [roi1,roi2,roi3,roi4,roi5,roi6,roi7,roi8,roi9,roi10,roi11,roi12,roi13,roi14,roi15]

class Color_Statistics(object):
    def __init__(self, lcd=None, sensor=None):
        self.lcd = lcd
        self.sensor = sensor
        # self.lcd.init(freq=15000000, invert=1)
        # self.lcd.rotation(1)
        self.clock = time.clock()
        self.img = None
        self.img_binary1=200
        self.img_binary2=255
        self.line_binary1=230
        self.line_binary2=255
        # if(self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        # elif(self.sensor.get_id()==0x5640):
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)
        time.sleep(0.2)

    def recognize(self):
        # self.clock.tick()
        self.img = self.sensor.snapshot()
        self.img.binary([(self.img_binary1,self.img_binary2)])
        _line = self.img.get_regression([(self.line_binary1,self.line_binary2)])
        for i in range(len(roi_list)):
            self.img.draw_rectangle(roi_list[i], color=(0, 128, 0), fill=False)

        if(_line):
            self.img.draw_line(_line.line(), color = 127)
            # print(line.line(),line.rho(),line.x1(),line.y1(),line.x2(),line.y2(),line.length(),line.magnitude(),line.theta())
        else:
            _line = None
        data1 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi1).mode()
        data2 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi2).mode() 
        data3 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi3).mode() 
        data4 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi4).mode() 
        data5 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi5).mode() 
        data6 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi6).mode() 
        data7 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi7).mode() 
        data8 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi8).mode() 
        data9 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi9).mode() 
        data10 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi10).mode() 
        data11 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi11).mode() 
        data12 =  self.img.get_statistics(thresholds = [(230,255)] , roi = roi12).mode() 
        data13 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi13).mode() 
        data14 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi14).mode() 
        data15 = self.img.get_statistics(thresholds = [(230,255)] , roi = roi15).mode() 
        # fps=self.clock.fps()
        # self.img.draw_string(1,1, ("%2.1ffps:"%(fps)), color=(0,128,0),scale=1)
        self.lcd.display(self.img)
        gc.collect()
        # return 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,_line
        return data1,data2,data3,data4,data5,data6,data7,data8,data9,data10,data11,data12,data13,data14,data15,_line

    def set_up_img_binary(self,binary1,binary2):
        self.img_binary1 = binary1
        self.img_binary2 = binary2

    def set_up_line_binary(self,binary1,binary2):
        self.line_binary1 = binary1
        self.line_binary2 = binary2
        
    def __del__(self):
        del self.img
        del self.lcd
        gc.collect()


class Color_Extractor(object):
    Roi = (70,50,20,20)
    def __init__(self, lcd=None, sensor=None):
        self.lcd = lcd
        self.sensor = sensor
        # if(self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        # elif(self.sensor.get_id()==0x5640):
        #     self.sensor.set_vflip(0)
        #     self.sensor.set_hmirror(0)
        # self.lcd.init(freq=15000000, invert=1)
        self.img = None
        self.color_l=None
        self.color_a=None
        self.color_b=None
        time.sleep(0.2)

    def recognize(self):
        try:
            self.img = self.sensor.snapshot()
            self.statistics=self.img.get_statistics(roi=self.Roi)
            self.color_l=self.statistics.l_mode()
            self.color_a=self.statistics.a_mode()
            self.color_b=self.statistics.b_mode()
            self.img.draw_rectangle(self.Roi)
            self.img.draw_string(2, 2,str([self.color_l,self.color_a,self.color_b]), color=(0,128,0), scale=2)
            self.lcd.display(self.img)
            return str(self.color_l),str(self.color_a),str(self.color_b)
            gc.collect()
        except Exception as e:
            self.color_l=None
            self.color_a=None
            self.color_b=None
            return self.color_l,self.color_a,self.color_b
        
    def __del__(self):
        del self.img
        del self.lcd
        gc.collect()
        