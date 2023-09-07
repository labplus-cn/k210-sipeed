# import KPU as kpu
# import sensor
# import lcd
from Maix import GPIO
from fpioa_manager import fm
import time
import gc
from display import Draw_CJK_String

class Self_learning_classifier(object):
  def __init__(self, choice=1, kpu=None, lcd=None, sensor=None, class_num=1, sample_num=15):
    self.model_addr = 0x850000
    self.class_num = class_num
    self.sample_num = sample_num
    self.threshold = 9
    self.sensor = sensor
    self.kpu = kpu
    self.lcd = lcd
    gc.collect()

    #A键
    fm.register(16, fm.fpioa.GPIOHS0+16)
    self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)
    #B键
    fm.register(17, fm.fpioa.GPIOHS0+17)
    self.key_b = GPIO(GPIO.GPIOHS0+17, GPIO.PULL_UP)

    gc.collect()
    self.model = self.kpu.load(self.model_addr)
    self.classifier = self.kpu.classifier(self.model, self.class_num, self.sample_num)

    self.change_camera(choice=choice)
    #new
    self.flag_add_class = 0
    self.flag_add_sample = 0
    self.flag_train = 0
    self.class_img_num = 0
    self.sample_img_num = 0
    

  # snapshot every class
  def add_class_img(self):
    self.flag_add_class = 1
    self.flag_add_sample = 0
    # while True:
    img = self.sensor.snapshot()
    # img = img.draw_string(0, 0, "add class image", color=(0,255,0),scale=2)
    Draw_CJK_String('按A键按顺序添加分类图片', 5, 5, img, color=(0, 255, 0))
    if self.key.value() == 0:
        time.sleep_ms(30)
        if self.key.value() == 0:
          index = self.classifier.add_class_img(img)
          # print("add class img:", index)
          # img = img.draw_string(0, 0, "add class:{0}".format(index), color=(0,255,0),scale=1)
          Draw_CJK_String('添加分类图片，id：{0}'.format(index), 5, 20, img, color=(0, 255, 0))
          self.lcd.display(img)
          time.sleep_ms(3000)
          if index >= self.class_num-1:
            # print("Add class img successed.")
            del img
            self.flag_add_class = 0
            self.flag_add_sample = 1
            return
    self.lcd.display(img)
   


  # capture img
  def add_sample_img(self):
    self.flag_add_sample = 1
    # while True:
    img = self.sensor.snapshot()
    Draw_CJK_String('按B键添加训练集图片', 5, 5, img, color=(0, 0, 200))
    if self.key_b.value() == 0:
        time.sleep_ms(30)
        if self.key_b.value() == 0:
          index = self.classifier.add_sample_img(img)
          Draw_CJK_String('添加训练集图片{0}'.format(index+1), 5, 20, img, color=(0, 0, 200))
          self.lcd.display(img)
          time.sleep_ms(2000)
          if index >= self.sample_num-1:
            print("Add sample img successed.")
            del img
            self.flag_add_sample = 0
            self.flag_train=1
            # break
            return
    self.lcd.display(img)

  # train
  def train(self):
    # print("start train")
    # self.flag_train=1
    self.classifier.train()
    # time.sleep_ms(100)
    self.flag_train=0

  def predict(self):
    img = self.sensor.snapshot()
    Draw_CJK_String('识别中...', 5, 5, img, color=(0, 255, 0))
    res_index = None
    min_dist = None
    try:
        res_index, min_dist = self.classifier.predict(img)
        # print("{:.2f}".format(min_dist))
    except Exception as e:
        print("predict err:", e)
        return res_index,min_dist
    if res_index >= 0 and min_dist < self.threshold :
        # print("predict result:", class_names[res_index])
        # img = img.draw_string(0, 0, "predict,index:{0} min_dist:{1}".format(res_index, min_dist), color=(0,255,0),scale=1)
        if(min_dist<=6):
          Draw_CJK_String('识别到id:{0}'.format(res_index), 5, 20, img, color=(0, 255, 0))
        self.lcd.display(img)
        return res_index,min_dist
    else:
        # print("unknown, maybe:", class_names[res_index])
        self.lcd.display(img)
        return res_index,min_dist

  def save_classifier(self, name="classes.classifier"):
    self.classifier.save(name)
    Draw_CJK_String('保存模型', 160, 100, img, color=(0, 255, 0))

  def load_classifier(self, name="classes.classifier"):
    try:
      del self.classifier
    except:
      print("del model fail")
    gc.collect()
    self.classifier, self.class_num, self.sample_num = self.kpu.classifier.load(self.model, name)
    # print(self.class_num)

  def change_camera(self, choice):
    try:
        self.sensor.reset(choice=choice)  
    except Exception as e:
        self.lcd.clear((0, 0, 255))
        self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
    self.sensor.set_framesize(self.sensor.QVGA)
    self.sensor.set_pixformat(self.sensor.RGB565)
    self.sensor.set_hmirror(1)
    if(choice==1 and self.sensor.get_id()==0x2642):
      self.sensor.set_vflip(1)
      self.sensor.set_hmirror(1)
    elif(choice==1 and self.sensor.get_id()==0x5640):
      self.sensor.set_vflip(0)
      self.sensor.set_hmirror(0)
    else:
      self.sensor.set_vflip(0)
      self.sensor.set_hmirror(0)
    
    self.sensor.run(1)
    time.sleep(0.5)