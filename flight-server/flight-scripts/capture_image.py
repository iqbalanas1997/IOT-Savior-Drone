#!/usr/bin/env python3

from datetime import datetime
from picamera import PiCamera

now = datetime.now().strftime("%d-%m-%Y_%H:%M:%S")

filename = str(now) + '.jpeg' 
filepath = "/home/pi/images/" + filename
camera = PiCamera()
camera.resolution = (2000, 2000)
camera.capture(filepath)

print('Image saved to: ' + filepath)