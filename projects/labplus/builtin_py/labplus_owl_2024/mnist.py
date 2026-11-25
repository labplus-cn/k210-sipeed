from fpioa_manager import *
import os, Maix, gc, time

class MNIST(object):
    def __init__(self, sensor, lcd, kpu):
        try:
            self.kpu = kpu
            self.lcd = lcd
            self.sensor = sensor
            # self.choice = choice

            try:
                self.lcd.init(freq=15000000, invert=1)
                self.lcd.rotation(1)
                self.lcd.clear(0,0,0)
                self.task_mnist = self.kpu.load(0x610000)
                self.change_camera()
                time.sleep(1)
            except Exception as e:
                print("[MNIST init]", e)
                raise
        except Exception:
            try:
                self.__del__()
            except Exception as release_error:
                print("[model init release]", release_error)
                raise RuntimeError("KPU_RELEASE_FAILED")
            raise

    def recognize(self):
        img_mnist = self.sensor.snapshot()

        img_mnist1=img_mnist.to_grayscale(1)        #convert to gray
        img_mnist2=img_mnist1.resize(28,28)         #resize to mnist input 28x28
        a=img_mnist2.invert()                 #invert picture as mnist need
        a=img_mnist2.strech_char(1)           #preprocessing pictures, eliminate dark corner

        #lcd.display(img2,oft=(10,40))   #display small 28x28 picture
        a=img_mnist2.pix_to_ai()              #generate data for ai
        
        fmap_mnist=self.kpu.forward(self.task_mnist,img_mnist2)     #run neural network model 
        plist_mnist=fmap_mnist[:]                   #get result (10 digit's probability)
        pmax_mnist=max(plist_mnist)                 #get max probability
        max_index_mnist=plist_mnist.index(pmax_mnist)     #get the digit

        # print(str(max_index_mnist)+","+str(int(pmax_mnist*100)))

        img_mnist.draw_rectangle(180,0,220,50,color=(0,0,0),fill=True)
        img_mnist.draw_string(180,3,str(max_index_mnist),color=(255,255,255),scale=4)
        self.lcd.display(img_mnist,oft=(0,0))        #display large picture

        gc.collect() 
        return max_index_mnist,int(round(pmax_mnist,2)*100)
        # lcd.draw_string(8,8,"%d: %.3f"%(max_index,pmax),lcd.WHITE,lcd.BLACK)
        # return max_index_mnist,pmax_mnist

    def __del__(self):
        task = getattr(self, "task_mnist", None)
        if task is not None:
            self.task_mnist = None
            self.kpu.deinit(task)

    def change_camera(self):
        try:
            self.sensor.reset(freq=24000000)
            self.sensor.set_pixformat(self.sensor.GRAYSCALE)
            self.sensor.set_framesize(self.sensor.QVGA)
            self.sensor.set_windowing((240, 240))  
            # self.sensor.set_hmirror(1)
        except Exception as e:
            print("[camera init]", e)
            raise
        
        # if(choice==1 and self.sensor.get_id()==0x2642):
        #     self.sensor.set_vflip(1)
        #     self.sensor.set_hmirror(1)
        
        self.sensor.skip_frames(30)
        self.sensor.run(1)

# t = MNIST(1)
# while 1:
#     t.recognize()
