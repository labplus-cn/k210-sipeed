
import time
import _thread

def thread1():
    t = 0
    while True:
        print('thread1:%4d' % t)
        t = t + 1
        time.sleep_ms(10)

def thread2():
    t = 0
    while True:
        print('thread2:%4d' % t)
        t = t + 1
        time.sleep_ms(50)


fm.register(11, fm.fpioa.UART2_TX)
fm.register(10, fm.fpioa.UART2_RX)
uart = machine.UART(machine.UART.UART2)
uart.init(115200, 8, None, 1, timeout=100, read_buf_len=2048)

_thread.start_new_thread(thread1, ())
_thread.start_new_thread(thread2, ())

while True:
    print('main')
    time.sleep(4)
    if uart.any() > 0:
        print('uart received')
