import KPU as kpu


task = kpu.load(0x300000)
anchor = (1.889, 2.5245, 2.9465, 3.94056, 3.99987, 5.3658, 5.155437, 6.92275, 6.718375, 9.01025)

kpu.init_yolo2(task, 0.5, 0.3, 5, anchor)

while True:
    img = sensor.snapshot()
    code = kpu.run_yolo2(task, img)
    if code:
        for i in code:
            a = img.draw_rectangle(i.rect())
    lcd.display(img)

kpu.deinit(task)