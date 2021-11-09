
while True:
    cam = sensor.snapshot()

    #
    # thresholds : 定义需要跟踪的颜色范围,[(lo,hi),(lo,hi),(lo,hi)]
    thresholds = ((56,68,-12,0,-52,-30),)
    # invert: 
    # invert = False
    # roi: 定义需要处理图形区域(x,y,w,h),,如果未使用则为整个图形
    # roi = None
    # x_stride,y_stride;搜索色块是从x/y方向跳过的像素个数,加大此值可以加快搜索速度
    # x_stride = 2
    # y_stride = 2
    blobs = cam.find_blobs(thresholds, area_threshold=200, pixel_threshold= 6000, merge=True, marge=10)
    if not blobs == None:
        for blob in blobs:
            cam.draw_rectangle(blob.rect())
    
    lcd.display(cam)
