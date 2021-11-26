import sensor
import image
import lcd
import KPU as kpu
import time
from Maix import FPIOA, GPIO
import gc
from fpioa_manager import fm
# import utime

# BOUNCE_PROTECTION = 50

# def set_key_state(*_):
#     global start_processing
#     start_processing = True
#     utime.sleep_ms(BOUNCE_PROTECTION)

#     key_gpio.irq(set_key_state, GPIO.IRQ_RISING, GPIO.WAKEUP_NOT_SUPPORT)

# print("mem free:", gc.mem_free())

class Face_recognization(object):
    def __init__(self, task_fd=0x300000, task_ld=0x380000, task_fe=0x3d0000, face_num=1, accuracy=85):
        self.task_fd = kpu.load(task_fd)
        self.task_ld = kpu.load(task_ld)
        self.task_fe = kpu.load(task_fe)
        self.face_num = face_num
        self.clock = time.clock()
        self.anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437,
                6.92275, 6.718375, 9.01025)  # anchor for face detect
        self.dst_point = [(44, 59), (84, 59), (64, 82), (47, 105),
                    (81, 105)]  # standard face key point position        
        self.accuracy = accuracy

        self.names = ['Mr.1', 'Mr.2', 'Mr.3', 'Mr.4', 'Mr.5',
                'Mr.6', 'Mr.7', 'Mr.8', 'Mr.9', 'Mr.10']

        fm.register(16, fm.fpioa.GPIOHS0+16)
        self.key = GPIO(GPIO.GPIOHS0+16, GPIO.IN)

        a = kpu.init_yolo2(self.task_fd, 0.5, 0.3, 5, self.anchor)
        self.img_face = image.Image(size=(128, 128))
        a = self.img_face.pix_to_ai()
        self.record_ftr = []
        self.record_ftrs = []

    def add_face(self):
        tmp_num = 0
        while True:
            img = sensor.snapshot()
            self.clock.tick()
            code = kpu.run_yolo2(self.task_fd, img)
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
                    fmap = kpu.forward(self.task_ld, face_cut_128)
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
                    fmap = kpu.forward(self.task_fe, self.img_face)
                    feature = kpu.face_encode(fmap[:])
                    # 5、人脸数据存入库中
                    if self.key.value() == 0:
                        time.sleep_ms(30)
                        if self.key.value() == 0:
                            self.record_ftr = feature
                            self.record_ftrs.append(self.record_ftr)
                            print("add a face.")
                            img.draw_string(0,0, "Add a face, index={0}".format(tmp_num), color=(0, 255, 0), scale=1)
                            time.sleep(3)
                            tmp_num = tmp_num + 1
                            if tmp_num >= self.face_num:
                                return
                    break 
                # fps = self.clock.fps()
                # print("%2.1f fps" % fps)
                a = lcd.display(img)
                gc.collect()     
            
    def face_recognize(self):
        img = sensor.snapshot()
        self.clock.tick()
        code = kpu.run_yolo2(self.task_fd, img)
        res =  None
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
                fmap = kpu.forward(self.task_ld, face_cut_128)
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
                fmap = kpu.forward(self.task_fe, self.img_face)
                feature = kpu.face_encode(fmap[:])
                scores = []
                # 5、compare feature with store face feature.
                for j in range(len(self.record_ftrs)): 
                    score = kpu.face_compare(self.record_ftrs[j], feature)
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
            a = lcd.display(img)
            gc.collect()    
            return res # 如果图片跟人脸库中对应人脸相似度大于阈值，返回对应人脸索引号，否则返回None
        
    def __del__(self):
        a = kpu.deinit(self.task_fe)
        a = kpu.deinit(self.task_ld)
        a = kpu.deinit(self.task_fd)

# """
# 测试代码
# """ 
# fc = Face_recognization(face_num=3)
# fc.add_face()
# while True:
#     index = fc.face_recognize()
#     if index != None:
#         print("detect a face index:", index)

