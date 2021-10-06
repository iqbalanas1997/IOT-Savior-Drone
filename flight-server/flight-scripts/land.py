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

vehicle.mode = VehicleMode('LAND')

while vehicle.mode!='LAND':
	print("Waiting for drone to enter LAND flight mode")
	time.sleep(1)
print("Vehicle now in LAND MODE")
