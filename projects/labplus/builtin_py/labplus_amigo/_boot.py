import os, sys, time

sys.path.append('')
sys.path.append('.')

# chdir to "/sd" or "/flash"
devices = os.listdir("/")
if "sd" in devices:
    os.chdir("/sd")
    sys.path.append('/sd')
else:
    os.chdir("/flash")
sys.path.append('/flash')
del devices

print("[1956] init end") # for IDE
for i in range(200):
    time.sleep_ms(1) # wait for key interrupt(for maixpy ide)
del i
import json

config = {
"type": "amigo_ips",
"lcd": {
    "height": 320,
    "width": 480,
    "invert": 1,
    "dir": 40,
    "lcd_type": 2
},
"sdcard":{
    "sclk":11,
    "mosi":10,
    "miso":6,
    "cs":26
},
"board_info": {
    'BOOT_KEY': 16,
    'LED_R': 14,
    'LED_G': 15,
    'LED_B': 17,
    'LED_W': 32,
    'BACK': 31,
    'ENTER': 23,
    'NEXT': 20,
    'WIFI_TX': 6,
    'WIFI_RX': 7,
    'WIFI_EN': 8,
    'I2S0_MCLK': 13,
    'I2S0_SCLK': 21,
    'I2S0_WS': 18,
    'I2S0_IN_D0': 35,
    'I2S0_OUT_D2': 34,
    'I2C_SDA': 27,
    'I2C_SCL': 24,
    'SPI_SCLK': 11,
    'SPI_MOSI': 10,
    'SPI_MISO': 6,
    'SPI_CS': 12,
}
}

# check IDE mode
ide_mode_conf = "/flash/ide_mode.conf"
ide = True
try:
    f = open(ide_mode_conf)
    f.close()
    del f
except Exception:
    ide = False

if ide:
    os.remove(ide_mode_conf)
    from machine import UART
    repl = UART.repl_uart()
    repl.init(1500000, 8, None, 1, read_buf_len=2048, ide=True, from_ide=False)
    sys.exit()
import lcd
lcd.init(type=1)
lcd.init()
del ide, ide_mode_conf

# detect boot.py
main_py = '''
try:
    import gc, lcd, image, sys, os
    from Maix import GPIO
    
    lcd.init(color=57997)
    lcd.register(0xd0, [0x07,0x42,0x1b])
    lcd.register(0xd1, [0x00,0x05,0x0c])
    lcd.clear(color=(255,0,0))
    background = image.Image('/flash/1956.jpg', copy_to_fb=True)
    lcd.display(background)
    del background
    gc.collect()
finally:
    gc.collect()
'''

flash_ls = os.listdir()
if not "main.py" in flash_ls:
    f = open("main.py", "wb")
    f.write(main_py)
    f.close()
    del f
del main_py

flash_ls = os.listdir("/flash")
try:
    sd_ls = os.listdir("/sd")
except Exception:
    sd_ls = []
if "cover.boot.py" in sd_ls:
    code0 = ""
    if "boot.py" in flash_ls:
        with open("/flash/boot.py") as f:
            code0 = f.read()
    with open("/sd/cover.boot.py") as f:
        code=f.read()
    if code0 != code:
        with open("/flash/boot.py", "w") as f:
            f.write(code)
        import machine
        machine.reset()

if "cover.main.py" in sd_ls:
    code0 = ""
    if "main.py" in flash_ls:
        with open("/flash/main.py") as f:
            code0 = f.read()
    with open("/sd/cover.main.py") as f:
        code = f.read()
    if code0 != code:
        with open("/flash/main.py", "w") as f:
            f.write(code)
        import machine
        machine.reset()

try:
    del flash_ls
    del sd_ls
    del code0
    del code
except Exception:
    pass


try:
    from machine import I2C
    axp173 = I2C(I2C.I2C3, freq=100000, scl=24, sda=27)
    axp173.writeto_mem(0x34, 0x27, 0x20, mem_size=8)
    axp173.writeto_mem(0x34, 0x28, 0x0C, mem_size=8)
    axp173.writeto_mem(0x34, 0x36, 0xCC, mem_size=8)
    del axp173
except Exception as e:
    print(e)


cfg = json.dumps(config)
# print(cfg)

try:
    with open('/flash/config.json', 'rb') as f:
        tmp = json.loads(f.read())
        # print(tmp)
        if tmp["type"] != config["type"]:
            raise Exception('config.json no exist')
except Exception as e:
    with open('/flash/config.json', "w") as f:
        f.write(cfg)
    import machine
    machine.reset()