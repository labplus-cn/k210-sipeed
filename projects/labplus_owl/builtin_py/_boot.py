import os, sys, time

sys.path.append('')
sys.path.append('.')

# chdir to "/sd" or "/flash"
devices = os.listdir("/")
if "sd" in devices:
    # os.chdir("/sd")
    sys.path.append('/sd')
else:
    os.chdir("/flash")
os.chdir('/flash')
sys.path.append('/flash')

for i in range(200):
    time.sleep_ms(1) # wait for key interrupt(for maixpy ide)

# check IDE mode
ide_mode_conf = "/flash/ide_mode.conf"
ide = True
try:
    f = open(ide_mode_conf)
    f.close()
except Exception:
    ide = False

if ide:
    os.remove(ide_mode_conf)
    from machine import UART
    import lcd
    lcd.init(color=lcd.PINK)
    repl = UART.repl_uart()
    repl.init(1500000, 8, None, 1, read_buf_len=2048, ide=True, from_ide=False)
    sys.exit()

debug_mode = "/flash/debug.conf"
is_debug = True
try:
    f = open(debug_mode)
    f.close()
except Exception:
    is_debug = False



from labplus import *
from fpioa_manager import fm

if not is_debug:
    repl = UART.repl_uart()
    repl.init(2000000, 8, None, 1, read_buf_len=2048)
    fm.fpioa.set_function(10, FPIOA.UARTHS_RX)
    fm.fpioa.set_function(11, FPIOA.UARTHS_TX)

    # print('hello, world')
    # fm.register(11, fm.fpioa.UART2_TX)
    # fm.register(10, fm.fpioa.UART2_RX)
    # uart = machine.UART(machine.UART.UART2)
    # uart.init(115200, 8, None, 1, timeout=100, read_buf_len=2048)
    # machine.UART.set_repl_uart(uart)



