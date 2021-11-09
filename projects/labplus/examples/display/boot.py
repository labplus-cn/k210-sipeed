
# display testing
from display import *
from labplus import *

str = "盛思1956测试"

img = image.Image()

while True:
    cam = sensor.snapshot()
    img.draw_image(cam, 0, 0, 0.75, 0.75)
    Draw_CJK_String(str, 0, 0, img)
    Draw_CJK_String(str, 0, 50, img)
    Draw_CJK_String(str, 0, 100, img)
    Draw_CJK_String(str, 0, 150, img)
    Draw_CJK_String(str, 0, 200, img)
    Draw_CJK_String(str, 0, 250, img)
    Draw_CJK_String(str, 0, 300, img)

    lcd.display(img)
