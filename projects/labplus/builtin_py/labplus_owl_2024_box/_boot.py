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


from labplus import *

