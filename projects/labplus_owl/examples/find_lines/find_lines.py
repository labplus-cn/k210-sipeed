
from labplus import *

sensor.set_pixformat(sensor.GRAYSCALE)

while True:
    # capture
    cam = sensor.snapshot()
    # turn the image to black and white leaving only the edges as white pixels
    edge = cam.find_edges(image.EDGE_CANNY, threshold=(100, 200))
    lines = edge.find_lines(threshold=1000, theta_margin=25, rho_margin=25)

    if not lines == None:
        for line in lines:
            cam.draw_line(line.line())
    
    lcd.display(cam)
