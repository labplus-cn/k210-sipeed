from Maix import GPIO
from fpioa_manager import fm
import time
import gc
import os
from display import Draw_CJK_String

class Self_learning_classifier(object):
  def __init__(self, kpu=None, lcd=None, sensor=None, class_num=1, sample_num=5):
    self.model_addr = 0x850000
    self.class_num = class_num
    self.sample_num = sample_num
    self.threshold = 6
    self.sensor = sensor
    self.kpu = kpu
    self.lcd = lcd
    self.img = None
    gc.collect()

    #A键
    fm.register(12, fm.fpioa.GPIOHS0, force=True)
    self.key = GPIO(GPIO.GPIOHS0, GPIO.PULL_UP)
    #B键
    fm.register(13, fm.fpioa.GPIOHS1, force=True)
    self.key_b = GPIO(GPIO.GPIOHS1, GPIO.PULL_UP)

    self.kpu.memtest()
    gc.collect()
    self.model = self.kpu.load(self.model_addr)
    self.classifier = self.kpu.classifier(self.model, self.class_num, self.sample_num)

    self.change_camera()
    #new
    self.flag_add_class = 0
    self.flag_add_sample = 0
    self.flag_train = 0
    self.flag_save = 0
    self.class_img_num = 0
    self.sample_img_num = 0

    self.kpu.memtest()
    
  # snapshot every class
  def add_class_img(self):
    self.flag_add_class = 1
    self.flag_add_sample = 0
    # while True:
    self.img = self.sensor.snapshot()
    Draw_CJK_String('按A键按顺序添加分类图片', 40, 5, self.img, color=(0, 255, 0))
    if self.key.value() == 0:
        time.sleep_ms(30)
        if self.key.value() == 0:
          index = self.classifier.add_class_img(self.img)
          # print("add class self.img:", index)
          Draw_CJK_String('添加分类图片，id：{0}'.format(index), 40, 20, self.img, color=(0, 255, 0))
          self.lcd.display(self.img)
          time.sleep_ms(3000)
          if index >= self.class_num-1:
            # print("Add class self.img successed.")
            del self.img
            self.flag_add_class = 0
            self.flag_add_sample = 1
            return
    self.lcd.display(self.img)
   
  # capture self.img
  def add_sample_img(self):
    self.flag_add_sample = 1
    # while True:
    self.img = self.sensor.snapshot()
    Draw_CJK_String('按B键添加训练集图片', 40, 5, self.img, color=(0, 0, 200))
    if self.key_b.value() == 0:
        time.sleep_ms(30)
        if self.key_b.value() == 0:
          index = self.classifier.add_sample_img(self.img)
          Draw_CJK_String('添加训练集图片{0}'.format(index+1), 40, 20, self.img, color=(0, 0, 200))
          self.lcd.display(self.img)
          time.sleep_ms(2000)
          if index >= self.sample_num-1:
            print("Add sample self.img successed.")
            # del self.img
            self.flag_add_sample = 0
            self.flag_train=1
            return
    self.lcd.display(self.img)

  # train
  def train(self):
    self.classifier.train()
    self.flag_train=0

  def predict(self):
    gc.collect()
    self.img = self.sensor.snapshot()
    Draw_CJK_String('识别中...', 40, 5, self.img, color=(0, 255, 0))
    res_index = None
    min_dist = None
    try:
        res_index, min_dist = self.classifier.predict(self.img)
    except Exception as e:
        print("err:", e)
        return res_index,min_dist
    if res_index >= 0 and min_dist <= self.threshold :
        
      if(min_dist <= self.threshold):
        Draw_CJK_String('识别到id:{0}'.format(res_index), 40, 20, self.img, color=(0, 255, 0))
        print('识别到id:{0}'.format(res_index))
        self.lcd.display(self.img)
        return res_index,min_dist
    else:
        Draw_CJK_String('未识别到', 40, 20, self.img, color=(0, 255, 0))
        self.lcd.display(self.img)
        return None,None

  def save_classifier(self, name="classes.classifier"):
    self.classifier.save(name)
    self.img = self.sensor.snapshot()
    Draw_CJK_String('保存模型成功', 40, 40, self.img, color=(0, 200, 0))
    self.lcd.display(self.img)
    time.sleep_ms(1500)

  def load_classifier(self, name="classes.classifier"):
    file_exit = False
    for v in os.listdir('/flash'):
      if name == '/flash/'+v:
        file_exit = True
    
    if file_exit:
      try:
        del self.classifier
      except:
        print("del model fail")
      gc.collect()
      self.classifier, self.class_num, self.sample_num = self.kpu.classifier.load(self.model, name)
      self.img = self.sensor.snapshot()
      Draw_CJK_String('载入已保存模型', 40, 40, self.img, color=(0, 200, 0))
      self.lcd.display(self.img)
      time.sleep_ms(1500)
    else:
      self.img = self.sensor.snapshot()
      Draw_CJK_String('模型文件不存在', 40, 40, self.img, color=(180, 0, 0))
      self.lcd.display(self.img)
      time.sleep_ms(1500)
  
  def __del__(self):
    a = self.kpu.deinit(self.model)
    print('kpu.deinit:{}'.format(a))
    del self.model
    del self.classifier
    del self.img
    del self.lcd
    del self.sensor
    del self.kpu
    gc.collect()


  def change_camera(self):
    try:
      self.sensor.reset(freq=24000000)
    except Exception as e:
      self.lcd.clear((0, 0, 255))
      self.lcd.draw_string(self.lcd.width()//2-100,self.lcd.height()//2-4, "Camera: " + str(e), self.lcd.WHITE, self.lcd.BLUE) 
    self.sensor.set_framesize(self.sensor.QVGA)
    self.sensor.set_pixformat(self.sensor.RGB565)
    # self.sensor.set_hmirror(1)
    # if(choice==1 and self.sensor.get_id()==0x2642):
    #   self.sensor.set_vflip(1)
    #   self.sensor.set_hmirror(1)
    
    self.sensor.run(1)
    time.sleep(0.5)