from machine import UART
from fpioa_manager import fm

fm.register(11, fm.fpioa.UARTHS_TX)
fm.register(10, fm.fpioa.UARTHS_RX)
# uart = UART(UART.UART1, 115200)
# UART.set_repl_uart(uart)

print('hello, world')
