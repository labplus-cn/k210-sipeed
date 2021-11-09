from fpioa_manager import fm
from machine import I2C, PWM, SPI, Timer, UART
from Maix import GPIO, I2S, Audio, FPIOA

class LED():
    """LED K210引脚控制的LED,默认使用Pinx与对应的GPIOHSx驱动
    """
    def __init__(self, pin):
        fm.register(pin, fm.fpioa.GPIOHS0 + pin)
        self.GPIO = GPIO(GPIO.GPIOHS0 + pin, GPIO.OUT)
        self.GPIO.value(1)
    
    def on(self):
        self.GPIO.value(0)
    
    def off(self):
        self.GPIO.value(1)


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