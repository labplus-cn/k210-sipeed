from fpioa_manager import fm
from Maix import GPIO
from machine import Timer
import time
import uerrno

class LED():
    """LED K210引脚控制的LED,默认使用Pinx与对应的GPIOHSx驱动
    """
    def __init__(self, pin, invert=True):
        fm.register(pin, fm.fpioa.GPIOHS0 + pin)
        self.GPIO = GPIO(GPIO.GPIOHS0 + pin, GPIO.OUT)
        self.invert = invert
        if invert:
            self.GPIO.value(1)
        else:
            self.GPIO.value(0)
    
    def on(self):
        if self.invert:
            self.GPIO.value(0)
        else:
            self.GPIO.value(1)
    
    def off(self):
        if self.invert:
            self.GPIO.value(1)
        else:
            self.GPIO.value(0)

class Motor:
    # 硬件引脚资源
    motor_pins = [[12,13],[14,15],[0,1],[2,3]]

    def __init__(self, channel):
        if channel in range(4):
            self.channel = channel
            self.pin_a = Motor.motor_pins[channel][0]
            self.pin_b = Motor.motor_pins[channel][1]
        else:
            OSError('not valid motor number')
        # assigned the pins
        fm.fpioa.set_function(self.pin_a, FPIOA.GPIOHS0 + self.pin_a)
        fm.fpioa.set_function(self.pin_b, FPIOA.TIMER2_TOGGLE1 + self.channel)
        # default:
        # pin-a as GPIO, and out high
        # pin-b as PWM, adn out duty = 0
        self.gpio = GPIO(GPIO.GPIOHS0 + self.pin_a, GPIO.OUT)
        self.gpio.value(0)
        self.pwm = PWM(Timer(Timer.TIMER2, Timer.CHANNEL0 + self.channel, mode=Timer.MODE_PWM), freq=1000, duty=0)
        self.pwm.duty(0)
        self._speed = 0
            
    @property
    def speed(self):
        return self._speed
    @speed.setter
    def speed(self, speed):
        if speed >= 0:
            '需要换向'
            if self._speed < 0:
                # stop
                self.pwm.duty(0)
                self.gpio.value(0)
                # change the direction
                fm.fpioa.set_function(self.pin_a, FPIOA.GPIOHS0 + self.pin_a)
                fm.fpioa.set_function(self.pin_b, FPIOA.TIMER2_TOGGLE1 + self.channel)
                # set new outputs
                self.gpio.value(0)
                self.pwm.duty(speed)
            else:
                # just set the new output
                self.pwm.duty(speed)
        
        if speed < 0:
            if self._speed >= 0:
                # stop
                self.pwm.duty(0)
                self.gpio.value(0)
                # change the direction
                fm.fpioa.set_function(self.pin_b, FPIOA.GPIOHS0 + self.pin_a)
                fm.fpioa.set_function(self.pin_a, FPIOA.TIMER2_TOGGLE1 + self.channel)
                # set new outputs
                self.gpio.value(0)
                self.pwm.duty(-speed)
            else:
                # just set the new output
                self.pwm.duty(-speed)
        self._speed = speed



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

class button:
    """ 按键类
    
    Returns
    -------
    [type]
        [description]
    
    Raises
    ------
    OSError
        [description]
    """

    # 按键状态
    KEY_DOWN = 0
    KEY_UP = 1

    # 记录所有创建的button对象,在定时器里周期性调用
    btn_list = []

    # 定时器触发事件处理
    def on_timer(timer):
        """on_button_timer 按键扫描定时器程序,为所有的按键(button)触发10mS一次的update操作
        
        Parameters
        ----------
        timer : [Timer类]
            定时器
        """
        try:
            for btn in button.btn_list:
                btn.update()
        except:
            # print('stop timer!')
            timer.deinit()
            button._timer_inited = False
    
    # 定时器初始化(所有button对象共享一个定时器)
    _timer_inited = False
    def timer_init(timer):
        button._timer_inited = True
        return Timer(timer, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC, period=10, callback=button.on_timer)
        print('timer started')

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
        if button._timer_inited == False:
            self.tim = button.timer_init(Timer.TIMER1)
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
            self.pressed = 0
            return True
        else:
            return False

    def get_presses(self):
        ret = self.pressed
        self.pressed = 0
        return ret


class RGB():
    """K210引脚控制的RGB, WS2812灯带
    """
    def __init__(self, pin,  num):
        self.rgb = ws2812(pin,num)
        self.num = num

    def set_led(self,r,g,b):
        for i in range(self.num):
            self.rgb.set_led(i,(r,g,b))
        self.rgb.display()

    def off(self):
        for i in range(self.num):
            self.rgb.set_led(i,(0,0,0))
        self.rgb.display()

