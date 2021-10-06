from picamera import PiCamera
from datetime import datetime

now = datetime.now()
dt_string = now.strftime("%d%m%Y-%H:%M:%S")
filename="images/" + dt_string

with PiCamera() as camera:	
    camera.resolution = (500, 500)
    camera.capture(filename)
