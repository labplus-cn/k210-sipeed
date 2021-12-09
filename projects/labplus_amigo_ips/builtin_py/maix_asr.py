import time
import gc
from Maix import I2S
from fpioa_manager import fm
from es8374 import *
from display import Draw_CJK_String
import lcd
import image


sample_rate = 16000

 # amigo
from speech_recognizer import asr
from machine import Timer

def on_timer_asr(timer):
  timer.callback_arg().state()

class maix_asr(asr):
  asr_vocab = ["lv", "shi", "yang", "chun", "yan", "jing", "da", "kuai", "wen", "zhang", "de", "di", "se", "si", "yue", "lin", "luan", "geng", "xian", "huo", "xiu", "mei", "yi", "ang", "ran", "ta", "jin", "ping", "yao", "bu", "li", "liang", "zai", "yong", "dao", "shang", "xia", "fan", "teng", "dong", "she", "xing", "zhuang", "ru", "hai", "tun", "zhi", "tou", "you", "ling", "pao", "hao", "le", "zha", "zen", "me", "zheng", "cai", "ya", "shu", "tuo", "qu", "fu", "guang", "bang", "zi", "chong", "shui", "cuan", "ke", "shei", "wan", "hou", "zhao", "jian", "zuo", "cu", "hei", "yu", "ce", "ming", "dui", "cheng", "men", "wo", "bei", "dai", "zhe", "hu", "jiao", "pang", "ji", "lao", "nong", "kang", "yuan", "chao", "hui", "xiang", "bing", "qi", "chang", "nian", "jia", "tu", "bi", "pin", "xi", "zou", "chu", "cun", "wang", "na", "ge", "an", "ning", "tian", "xiao", "zhong", "shen", "nan", "er", "ri", "zhu", "xin", "wai", "luo", "gang", "qing", "xun", "te", "cong", "gan", "lai", "he", "dan", "wei", "die", "kai", "ci", "gu", "neng", "ba", "bao", "xue", "shuai", "dou", "cao", "mao", "bo", "zhou", "lie", "qie", "ju", "chuan", "guo", "lan", "ni", "tang", "ban", "su", "quan", "huan", "ying", "a", "min", "meng", "wu", "tai", "hua", "xie", "pai", "huang", "gua", "jiang", "pian", "ma", "jie", "wa", "san", "ka", "zong", "nv", "gao", "ye", "biao", "bie", "zui", "ren", "jun", "duo", "ze", "tan", "mu", "gui", "qiu", "bai", "sang", "jiu", "yin", "huai", "rang", "zan", "shuo", "sha", "ben", "yun", "la", "cuo", "hang", "ha", "tuan", "gong", "shan", "ai", "kou", "zhen", "qiong", "ding", "dang", "que", "weng", "qian", "feng", "jue", "zhuan", "ceng", "zu", "bian", "nei", "sheng", "chan", "zao", "fang", "qin", "e", "lian", "fa", "lu", "sun", "xu", "deng", "guan", "shou", "mo", "zhan", "po", "pi", "gun", "shuang", "qiang", "kao", "hong", "kan", "dian", "kong", "pei", "tong", "ting", "zang", "kuang", "reng", "ti", "pan", "heng", "chi", "lun", "kun", "han", "lei", "zuan", "man", "sen", "duan", "leng", "sui", "gai", "ga", "fou", "kuo", "ou", "suo", "sou", "nu", "du", "mian", "chou", "hen", "kua", "shao", "rou", "xuan", "can", "sai", "dun", "niao", "chui", "chen", "hun", "peng", "fen", "cang", "gen", "shua", "chuo", "shun", "cha", "gou", "mai", "liu", "diao", "tao", "niu", "mi", "chai", "long", "guai", "xiong", "mou", "rong", "ku", "song", "che", "sao", "piao", "pu", "tui", "lang", "chuang", "keng", "liao", "miao", "zhui", "nai", "lou", "bin", "juan", "zhua", "run", "zeng", "ao", "re", "pa", "qun", "lia", "cou", "tie", "zhai", "kuan", "kui", "cui", "mie", "fei", "tiao", "nuo", "gei", "ca", "zhun", "nie", "mang", "zhuo", "pen", "zun", "niang", "suan", "nao", "ruan", "qiao", "fo", "rui", "rao", "ruo", "zei", "en", "za", "diu", "nve", "sa", "nin", "shai", "nen", "ken", "chuai", "shuan", "beng", "ne", "lve", "qia", "jiong", "pie", "seng", "nuan", "nang", "miu", "pou", "cen", "dia", "o", "zhuai", "yo", "dei", "n", "ei", "nou", "bia", "eng", "den", "_"]

  def get_asr_list(string='xiao-ai-fas-tong-xue'):
    return [__class__.asr_vocab.index(t) for t in string.split('-') if t in __class__.asr_vocab]

  def get_asr_string(listobj=[117, 214, 257, 144]):
    return '-'.join([__class__.asr_vocab[t] for t in listobj if t < len(__class__.asr_vocab)])

  def unit_test():
    print(__class__.get_asr_list('xiao-ai'))
    print(__class__.get_asr_string(__class__.get_asr_list('xiao-ai-fas-tong-xue')))

  def config(self, sets):
    self.set([(sets[key], __class__.get_asr_list(key)) for key in sets])

  def recognize(self):
    res = self.result()
    # print(tmp)
    if res != None:
      sets = {}
      for tmp in res:
        sets[__class__.get_asr_string(tmp[1])] = tmp[0]
        # print(tmp)
      return sets
    return None

class  Asr(object):
  def __init__(self):
    self.sets_key_id = {}
    self.sets_key_threshold = {}

    i2c = I2C(I2C.I2C2, freq=600*1000, sda=27, scl=24) # amigo
    dev = ES8374(i2c)
    dev.setVoiceVolume(100)
    dev.start(ES_MODULE._ES_MODULE_ADC_DAC)
    # init i2s(i2s0)
    i2s = I2S(I2S.DEVICE_0, pll2=262144000, mclk=31)
    # i2s = I2S(I2S.DEVICE_0)

    # config i2s according to audio info # STANDARD_MODE LEFT_JUSTIFYING_MODE RIGHT_JUSTIFYING_MODE
    i2s.channel_config(I2S.CHANNEL_0, I2S.RECEIVER, align_mode=I2S.STANDARD_MODE)
      
    fm.register(13,fm.fpioa.I2S0_MCLK, force=True)
    fm.register(21,fm.fpioa.I2S0_SCLK, force=True)
    fm.register(18,fm.fpioa.I2S0_WS, force=True)
    fm.register(35,fm.fpioa.I2S0_IN_D0, force=True)
    fm.register(34,fm.fpioa.I2S0_OUT_D2, force=True)
    i2s.set_sample_rate(16000)
    gc.collect()
    time.sleep_ms(1000)
    self.t = maix_asr(0x650000, I2S.DEVICE_0, 3, shift=1) # maix bit set shift=1
    # self.tim = Timer(Timer.TIMER1, Timer.CHANNEL3, mode=Timer.MODE_PERIODIC, period=64, callback=on_timer_asr, arg=self.t)
    self.tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=64, callback=on_timer_asr, arg=self.t)
    self.tim.start()
    self.lcd = lcd
    self.image = image.Image()

  def config(self, sets):
    for key in sets:
      self.sets_key_threshold[key] = sets[key][0]
      self.sets_key_id[key] = sets[key][1]
    self.t.config(self.sets_key_threshold)

  def recognize(self):
    # Draw_CJK_String('语音识别中...', 240, 160, self.image, color=(0, 255, 0))
    # self.lcd.display(self.image)
    tmp = self.t.recognize()
    if isinstance(tmp, dict):
      # print(tmp)
      for key in tmp:
        if key in self.sets_key_id:
          id = self.sets_key_id[key]
      return id 

  def asr_release(self):
    self.tim.stop()
    self.t.__del__()
    del self.t
  
# try:
#   t = Asr()

#   t.config({
#     'kai-deng' : [0.1, 0],
#     'ni-hao' : [0.1, 1]
#   })
  
#   while True:
#     # time.sleep(0.01)
#     tmp = t.recognize()
#     # print(tmp)
#     if tmp != None:
#       print(tmp)
# except Exception as e:
#   print(e)
# finally:
#   t.asr_release()
#   del t