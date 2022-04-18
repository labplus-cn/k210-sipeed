import sensor
import image
import lcd
import KPU as kpu
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
from display import Draw_CJK_String

class Face_recognization(object):
    def __init__(self, choice=1, task_fd=0x300000, task_ld=0x380000, task_fe=0x3d0000, face_num=1, accuracy=80):
        self.kpu = kpu
        self.lcd = lcd
        self.sensor = sensor
        self.task_fd = self.kpu.load(task_fd)
        self.task_ld = self.kpu.load(task_ld)
        self.task_fe = self.kpu.load(task_fe)
        self.face_num = face_num
        self.clock = time.clock()
        self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437,
                6.92275, 6.718375, 9.01025)  # anchor for face detect
        self.dst_point = [(44, 59), (84, 59), (64, 82), (47, 105),
                    (81, 105)]  # standard face key point position        
        self.accuracy = accuracy
        self.feature_file_exits = 0

        self.names = ['ID:0', 'ID:1', 'ID:2', 'ID:3', 'ID:4',
                'ID:5', 'ID:6', 'ID:7', 'ID:8', 'ID:9']

        fm.register(16, fm.fpioa.GPIOHS0+16)
        # self.key = GPIO(GPIO.GPIOHS0+16, GPIO.IN) #GPIO.PULL_UP
        self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)

        a = self.kpu.init_yolo2(self.task_fd, 0.5, 0.3, 5, self.anchor)
        self.img_face = image.Image(size=(128, 128))
        a = self.img_face.pix_to_ai()
        self.record_ftr = []
        self.record_ftrs = []
        self.change_camera(choice=choice)
        self.init_data()
        self.load_data()
        time.sleep(3)

    def add_face(self):
        print('555')
        self.clear_data()
        tmp_num = 0
        while True:
            img = self.sensor.snapshot()
            self.clock.tick()
            code = self.kpu.run_yolo2(self.task_fd, img)
            Draw_CJK_String('按A键添加人脸数据', 5, 5, img, color=(0, 255, 0))
            if code:
                for i in code:
                    gc.collect()
                    # 1、Cut face and resize to 128x128
                    a = img.draw_rectangle(i.rect())
                    face_cut = img.cut(i.x(), i.y(), i.w(), i.h())
                    face_cut_128 = face_cut.resize(128, 128)
                    a = face_cut_128.pix_to_ai()
                    # a = img.draw_image(face_cut_128, (0,0))
                    # 2、Landmark for face 5 points
                    fmap = self.kpu.forward(self.task_ld, face_cut_128)
                    plist = fmap[:]
                    le = (i.x() + int(plist[0] * i.w() - 10), i.y() + int(plist[1] * i.h()))
                    re = (i.x() + int(plist[2] * i.w()), i.y() + int(plist[3] * i.h()))
                    nose = (i.x() + int(plist[4] * i.w()), i.y() + int(plist[5] * i.h()))
                    lm = (i.x() + int(plist[6] * i.w()), i.y() + int(plist[7] * i.h()))
                    rm = (i.x() + int(plist[8] * i.w()), i.y() + int(plist[9] * i.h()))
                    a = img.draw_circle(le[0], le[1], 4)
                    a = img.draw_circle(re[0], re[1], 4)
                    a = img.draw_circle(nose[0], nose[1], 4)
                    a = img.draw_circle(lm[0], lm[1], 4)
                    a = img.draw_circle(rm[0], rm[1], 4)
                    # 3、align face to standard position
                    src_point = [le, re, nose, lm, rm]
                    T = image.get_affine_transform(src_point, self.dst_point)
                    a = image.warp_affine_ai(img, self.img_face, T)
                    del T
                    a = self.img_face.ai_to_pix()
                    # a = img.draw_image(img_face, (128,0))
                    del (face_cut_128)
                    # 4、calculate face feature vector
                    fmap = self.kpu.forward(self.task_fe, self.img_face)
                    feature = self.kpu.face_encode(fmap[:])
                    # 5、人脸数据存入库中
                    if self.key.value() == 0:
                        time.sleep_ms(30)
                        if self.key.value() == 0:
                            self.record_ftr = feature
                            self.record_ftrs.append(self.record_ftr)
                            self.save_data(self.record_ftr)
                            # print("add a face.")
                            # a = img.draw_string(5,15, "Add a face, id={0}".format(tmp_num), color=(0, 255, 0), scale=1)
                            Draw_CJK_String('添加人脸数据, id={0}'.format(tmp_num), 5, 20, img, color=(0, 255, 0))
                            self.lcd.display(img)
                            time.sleep(3)
                            tmp_num = tmp_num + 1
                            if tmp_num >= self.face_num:
                                return
                    break 
            a = self.lcd.display(img)
            gc.collect()     
            
    def face_recognize(self):
        img = self.sensor.snapshot()
        Draw_CJK_String('识别中...', 5, 5, img, color=(0, 255, 0))
        self.clock.tick()
        code = self.kpu.run_yolo2(self.task_fd, img)
        res =  None
        max_score = 0
        if code:
            for i in code:
                gc.collect()
                # 1、Cut face and resize to 128x128
                a = img.draw_rectangle(i.rect())
                face_cut = img.cut(i.x(), i.y(), i.w(), i.h())
                face_cut_128 = face_cut.resize(128, 128)
                a = face_cut_128.pix_to_ai()
                # a = img.draw_image(face_cut_128, (0,0))
                # 2、Landmark for face 5 points
                fmap = self.kpu.forward(self.task_ld, face_cut_128)
                plist = fmap[:]
                le = (i.x() + int(plist[0] * i.w() - 10), i.y() + int(plist[1] * i.h()))
                re = (i.x() + int(plist[2] * i.w()), i.y() + int(plist[3] * i.h()))
                nose = (i.x() + int(plist[4] * i.w()), i.y() + int(plist[5] * i.h()))
                lm = (i.x() + int(plist[6] * i.w()), i.y() + int(plist[7] * i.h()))
                rm = (i.x() + int(plist[8] * i.w()), i.y() + int(plist[9] * i.h()))
                a = img.draw_circle(le[0], le[1], 4)
                a = img.draw_circle(re[0], re[1], 4)
                a = img.draw_circle(nose[0], nose[1], 4)
                a = img.draw_circle(lm[0], lm[1], 4)
                a = img.draw_circle(rm[0], rm[1], 4)
                # 3、align face to standard position
                src_point = [le, re, nose, lm, rm]
                T = image.get_affine_transform(src_point, self.dst_point)
                a = image.warp_affine_ai(img, self.img_face, T)
                del T
                a = self.img_face.ai_to_pix()
                # a = img.draw_image(img_face, (128,0))
                del (face_cut_128)
                # 4、calculate face feature vector
                fmap = self.kpu.forward(self.task_fe, self.img_face)
                feature = self.kpu.face_encode(fmap[:])
                scores = []
                # 5、compare feature with store face feature.
                for j in range(len(self.record_ftrs)): 
                    score = self.kpu.face_compare(self.record_ftrs[j], feature)
                    scores.append(score) # 跟录入的人脸库中的每一张人脸比较，相似度值存入scores[]
                max_score = 0
                index = 0
                for k in range(len(scores)):  # 获取最大的相似度值人脸的索引号
                    if max_score < scores[k]:
                        max_score = scores[k]
                        index = k
                if max_score > self.accuracy:  # 最大相似度值大于给定阈值
                    a = img.draw_string(i.x(), i.y(), ("%s :%2.1f" % (
                        self.names[index], max_score)), color=(0, 255, 0), scale=2)
                    res = index
                else:
                    a = img.draw_string(i.x(), i.y(), ("X :%2.1f" % (
                        max_score)), color=(255, 0, 0), scale=2)
                break 
            # fps = self.clock.fps()
            # print("%2.1f fps" % fps)
        a = self.lcd.display(img)
        gc.collect()    
        return res,max_score # 如果图片跟人脸库中对应人脸相似度大于阈值，返回对应人脸索引号，否则返回None

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
    
    #保存数据
    def save_data(self, record_ftr):
        with open("_face_record_ftrs.txt", "a") as f:
            f.write(str(record_ftr))
            f.write("\n")
            f.close()

    #载入数据
    def load_data(self):
        if(self.feature_file_exits):
            with open("_face_record_ftrs.txt", "rb") as f:
                while(1):
                    line = f.readline()
                    if not line:
                        break
                    self.record_ftrs.append(eval(line))
                    time.sleep_ms(5)
                f.close()

    #初始化数据
    def init_data(self):
        import os
        self.feature_file_exits = 0
        for v in os.listdir('/flash'):
            if v == '_face_record_ftrs.txt':
                self.feature_file_exits = 1
    
        if(self.feature_file_exits==0):
            with open("_face_record_ftrs.txt", "w") as f:
                f.close()

    #清空数据
    def clear_data(self):
        self.record_ftr = []
        self.record_ftrs = []
        with open("_face_record_ftrs.txt", "w") as f:
            f.close()
        time.sleep_ms(5)

    def __del__(self):
        a = self.kpu.deinit(self.task_fe)
        a = self.kpu.deinit(self.task_ld)
        a = self.kpu.deinit(self.task_fd)

# """
# 测试代码
# """ 
# fc = Face_recognization(face_num=3)
# fc.add_face()
# while True:
#     index = fc.face_recognize()
#     if index != None:
#         print("detect a face index:", index)

