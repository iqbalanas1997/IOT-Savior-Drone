###### Dependencies ######
from dronekit import connect
import time
import argparse

##### Functions ######

parser = argparse.ArgumentParser(description='Drone commands')

parser.add_argument('--connect')

args = parser.parse_args()

def connectMyCopter():

	connection_string = args.connect

	vehicle = connect(connection_string, wait_ready = True)

	return vehicle

vehicle = connectMyCopter()


vehicle.armed = False

while vehicle.armed != False:
	print("Waiting for drone to disarm..")
	time.sleep(1)
	
print("Vehicle disarmed")