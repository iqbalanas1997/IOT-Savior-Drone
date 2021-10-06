###### Dependencies ######
from dronekit import connect, VehicleMode
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

vehicle.mode = VehicleMode('RTL')

while vehicle.mode!='RTL':
	print("Waiting for drone to enter RETURN TO LAUNCH flight mode")
	time.sleep(1)
print("Vehicle now in RETURN TO LAUNCH mode")