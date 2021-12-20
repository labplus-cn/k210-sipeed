import KPU as kpu
import sensor
import lcd
from Maix import GPIO
from fpioa_manager import fm
import time
import gc
from display import Draw_CJK_String

def draw_string(img, x, y, text, color, scale, bg=None ):
    if bg:
        img.draw_rectangle(x-2,y-2, len(text)*8*scale+4 , 16*scale, fill=True, color=bg)
    img = img.draw_string(x, y, text, color=color,scale=scale)
    return img

class self_learning_classfier(object):
  def __init__(self, model_addr=0x850000, class_num=3, sample_num=15, threshold=11, class_names=['class.1', 'class.2', 'class.3'], fea_len=512):
    self.model_addr = model_addr
    self.class_num = class_num
    self.sample_num = sample_num
    self.threshold = threshold
    self.class_names = class_names
    gc.collect()
    sensor.reset()
    sensor.set_framesize(sensor.QVGA)
    sensor.set_pixformat(sensor.RGB565)
    sensor.set_vflip(1)
    sensor.set_hmirror(1)
    # sensor.set_windowing((224, 224))
    fm.register(16, fm.fpioa.GPIOHS0+16)
    self.key = GPIO(GPIO.GPIOHS0+16, GPIO.PULL_UP)

    gc.collect()
    self.model = kpu.load(self.model_addr)
    self.classifier = kpu.classifier(self.model, self.class_num, self.sample_num)

  # snapshot every class
  def add_class_img(self):
    cap_num = 0
    while True:
      img = sensor.snapshot()
      Draw_CJK_String('按enter键按顺序添加分类图片', 5, 5, img, color=(0, 255, 0))
      # img.draw_string(5, 5, "start add class img.", color=(0, 255, 0), scale=2)
      if self.key.value() == 0:
          time.sleep_ms(30)
          if self.key.value() == 0:
            index = self.classifier.add_class_img(img)
            cap_num += 1
            # print("add class img:", index)
            # img.draw_string(5, 5, "add class img.", color=(0, 255, 0), scale=2)
            # img.draw_string(5, 30, "class id:"+str(index), color=(0, 255, 0), scale=2)
            Draw_CJK_String('添加分类图片，id：{0}'.format(index), 5, 20, img, color=(0, 255, 0))
            _ = lcd.display(img)
            time.sleep(3)
            time.sleep_ms(500)
            if index >= self.class_num-1:
              # print("Add class img successed.")
              # img.draw_string(5, 5, "Add class img successed.", color=(0, 255, 0), scale=2)
              Draw_CJK_String('添加分类图片完成', 160, 240, img, color=(0, 255, 0))
              _ = lcd.display(img)
              time.sleep(2)
              del img
              break
      else:
        time.sleep_ms(20)
        if cap_num < self.class_num:
            # img = draw_string(img, 0, 220, "press boot key to cap "+self.class_names[cap_num], color=lcd.WHITE, scale=1, bg=lcd.RED)
            # img = draw_string(img, 0, 220, "press boot key to cap ", color=lcd.WHITE, scale=1, bg=lcd.RED)
            pass
      lcd.display(img)

  # capture img
  def add_sample_img(self):
    cap_num = 0
    while True:
      img = sensor.snapshot()
      # img.draw_string(5, 5, "start add sample img.", color=(0, 255, 0), scale=2)
      Draw_CJK_String('按enter键添加训练集图片', 5, 5, img, color=(0, 0, 200))
      if self.key.value() == 0:
          time.sleep_ms(30)
          if self.key.value() == 0:
            index = self.classifier.add_sample_img(img)
            cap_num += 1
            # print("add sample img:", index)
            # img.draw_string(5, 5, "add sample img.", color=(0, 255, 0), scale=2)
            # img.draw_string(5, 30, "sample number:"+str(index), color=(0, 255, 0), scale=2)
            Draw_CJK_String('添加训练集图片{0}'.format(index+1), 5, 20, img, color=(0, 0, 200))
            _ = lcd.display(img)
            time.sleep_ms(2500)
            if index >= self.sample_num-1:
              # print("Add sample img successed.")
              # img.draw_string(5, 5, "Add sample img successed.", color=(0, 255, 0), scale=1)
              Draw_CJK_String('添加训练集图片完成', 160, 240, img, color=(0, 255, 0))
              _ = lcd.display(img)
              time.sleep_ms(2500)
              del img
              gc.collect()
              break
      else:
        time.sleep_ms(20)
        if cap_num < self.class_num + self.sample_num:
            # img = draw_string(img, 0, 220, "boot key to cap sample{}".format(cap_num), color=lcd.WHITE,scale=1, bg=lcd.RED)
            pass
      lcd.display(img)

  # train
  def train(self):
    print("start train")
    self.classifier.train()

  def predict(self):
    gc.collect()
    img = sensor.snapshot()
    Draw_CJK_String('识别中...', 5, 5, img, color=(0, 255, 0))
    res_index = None
    try:
        res_index, min_dist = self.classifier.predict(img)
        # print("{:.2f}".format(min_dist))
    except Exception as e:
        print("predict err:", e)
    if res_index >= 0 and min_dist < self.threshold :
        # print("predict result:", self.class_names[res_index])
        # img.draw_string(5, 5, "predict result:{}".format(self.class_names[res_index]), color=(0, 255, 0), scale=2)
        Draw_CJK_String('识别到id:{0}'.format(res_index), 5, 20, img, color=(0, 255, 0))
        lcd.display(img)
        return res_index
    else:
        # print("unknown, maybe:", class_names[res_index])
        lcd.display(img)
        return -1
        
  def save_classifier(self, name="classes.classifier"):
    self.classifier.save(name)

  def load_classifier(self, name="classes.classifier"):
    try:
      del self.classifier
    except:
      print("del model fail")
    gc.collect()
    self.classifier, self.class_num, self.sample_num = kpu.classifier.load(self.slc.model, name)
    print(self.class_num)

