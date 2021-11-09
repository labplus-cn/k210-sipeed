from fpioa_manager import fm
from Maix import GPIO
from machine import Timer
import time
import uerrno





def on_button_timer(timer):
    # for i in range(0, len(button.btn_list)):
    try:
        for btn in button.btn_list:
            btn.update()
    except:
        # print('stop timer!')
        timer.deinit()

button_timer_inited = False
def button_timer_init(timer):
    button_timer_inited = True
    return Timer(timer, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=10, callback=on_button_timer)


class button:
    # 按键列表
    btn_list = []

    KEY_UNKONW = 1
    KEY_DOWN = 2
    KEY_UP = 3

    def __init__(self, pin, invert=False):
        global button_timer_inited
        fm.register(pin, fm.fpioa.GPIOHS0 + pin)
        self.GPIO = GPIO(GPIO.GPIOHS0 + pin, GPIO.IN, GPIO.PULL_UP)
        self.state = self.GPIO.value()
        self.invert = invert
        button.btn_list.append(self)       
        # self.trigger_time = 0
        self.pressed = 0
        if self.GPIO.value():
            self.curr_state = button.KEY_DOWN if self.invert else button.KEY_UP
        else:
            self.curr_state = button.KEY_UP if self.invert else button.KEY_DOWN
        self.pre_state = self.curr_state
        self.counter = 0
        if button_timer_inited == False:
            self.tim = button_timer_init(Timer.TIMER1)
            if self.tim == None:
                raise OSError(uerrono.ENODEV)
        
        # self.GPIO.irq(gpio_irq, GPIO.IRQ_RISING)
        # self.GPIO.irq(gpio_irq, GPIO.IRQ_FALLING)
        # self.GPIO.irq(gpio_irq, GPIO.IRQ_BOTH)

    def __del__(self):
        button.btn_list.remove(self)
        if len(button.btn_list) == 0:
            self.tim.stop()

    def update(self):
        if self.GPIO.value():
            self.counter = self.counter + 1
        else:
            self.counter = self.counter - 1
        
        if self.counter < -3:
            self.counter = -3
            self.curr_state = button.KEY_UP if self.invert else button.KEY_DOWN

        if self.counter > 3:
            self.counter = 3
            self.curr_state = button.KEY_DOWN if self.invert else button.KEY_UP
            
        if self.curr_state != self.pre_state:
            self.pre_state = self.curr_state

            if (self.curr_state == button.KEY_DOWN):
                self.pressed = self.pressed + 1
                # print('button pressed')
        # print('timer elapsed!')
        pass

    # def irq(self):
    #     # # 按键状态改变,发生第一次中断:记录中断时间
    #     diff = time.ticks_diff(time.ticks(), self.trigger_time)

    #     # 大于10ms的边沿
    #     if diff > 10:
    #         if self.GPIO.value() == 0:     
    #             # key down 
    #             print("%6d:button triggled, value = %d" % (time.ticks(), self.GPIO.value()))
    #     self.trigger_time = time.ticks()

    def is_pressed(self):
        if self.curr_state == button.KEY_DOWN:
            return True
        else:
            return False
    
    def was_pressed(self):
        if self.pressed != 0:
            return True
        else:
            return False

    def get_presses(self):
        ret = self.pressed
        self.pressed = 0
        return ret




# def gpio_irq(GPIO):
#     global trigger_index
#     # 判断是哪一个按键触发
#     btn_in_list = False
#     # for i in range(0, len(button.btn_list)):
#     for btn in button.btn_list:
#         if btn.GPIO == GPIO:
#             btn.irq()
#             # time.sleep_ms(2)
#             # # debounce,ignore irq that elapse less than 5ms
#             # # if time.ticks_diff(time.ticks(), btn.trigger_time) < 10:
#             # #     return
#             # btn.trigger_time = time.ticks()
#             # print("%6d:button triggled:%4d, value = %d" % (btn.trigger_time, trigger_index, btn.GPIO.value()))
#             # # btn.event_state_changed(btn.GPIO.value())
#             btn_in_list = True
#             break
#     if btn_in_list == False:
#         print('no valid gpio found, list lenght = %d' % len(button.btn_list))