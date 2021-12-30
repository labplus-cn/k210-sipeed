import KPU as kpu
import sensor
import lcd
from Maix import GPIO
from fpioa_manager import fm
import time
import gc
from display import Draw_CJK_String

class Self_learning_classifier(object):
  def __init__(self, sensor, choice=1, model_addr=0x850000, class_num=1, sample_num=15, threshold=11, class_names=["class.1", "class.2", "class.3"]):
    self.model_addr = model_addr
    self.class_num = class_num
    self.sample_num = sample_num
    self.threshold = threshold
    self.class_names = class_names
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
    self.model = kpu.load(self.model_addr)
    self.classifier = kpu.classifier(self.model, self.class_num, self.sample_num)

    self.change_camera(choice=choice)
    time.sleep(3)

  # snapshot every class
  def add_class_img(self):
    while True:
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
            lcd.display(img)
            time.sleep_ms(3000)
            if index >= self.class_num-1:
              print("Add class img successed.")
              del img
              break
      lcd.display(img)

  # capture img
  def add_sample_img(self):
    while True:
      img = self.sensor.snapshot()
      # img = img.draw_string(0, 0, "add image sample image", color=(0,255,0),scale=2)
      Draw_CJK_String('按B键添加训练集图片', 5, 5, img, color=(0, 0, 200))
      if self.key_b.value() == 0:
          time.sleep_ms(30)
          if self.key_b.value() == 0:
            index = self.classifier.add_sample_img(img)
            # print("add sample img:", index)
            # img = img.draw_string(0, 0, "add image sample:{0}".format(index), color=(0,255,0),scale=1)
            Draw_CJK_String('添加训练集图片{0}'.format(index+1), 5, 20, img, color=(0, 0, 200))
            lcd.display(img)
            time.sleep_ms(2000)
            if index >= self.sample_num-1:
              print("Add sample img successed.")
              del img
              break
      lcd.display(img)

  # train
  def train(self):
    print("start train")
    self.classifier.train()

  def predict(self):
    img = self.sensor.snapshot()
    Draw_CJK_String('识别中...', 5, 5, img, color=(0, 255, 0))
    res_index = None
    try:
        res_index, min_dist = self.classifier.predict(img)
        # print("{:.2f}".format(min_dist))
    except Exception as e:
        print("predict err:", e)
    if res_index >= 0 and min_dist < self.threshold :
        # print("predict result:", class_names[res_index])
        # img = img.draw_string(0, 0, "predict,index:{0} min_dist:{1}".format(res_index, min_dist), color=(0,255,0),scale=1)
        Draw_CJK_String('识别到id:{0}'.format(res_index), 5, 20, img, color=(0, 255, 0))
        lcd.display(img)
        return res_index
    else:
        # print("unknown, maybe:", class_names[res_index])
        lcd.display(img)
        return None

  def save_classifier(self, name="classes.classifier"):
    self.classifier.save(name)

  def load_classifier(self, name="classes.classifier"):
    try:
      del self.classifier
    except:
      print("del model fail")
    gc.collect()
    self.classifier, self.class_num, self.sample_num = kpu.classifier.load(self.model, name)
    # print(self.class_num)
  
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