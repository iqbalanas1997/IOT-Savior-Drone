###### Dependencies ######
from dronekit import connect
import time
import json
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

while vehicle.armed==False:
    time.sleep(1)

while vehicle.armed==True:
    time.sleep(0.25)
    flight_stats = {
    'battery': vehicle.battery.level,
    'altitude': vehicle.location.global_relative_frame.alt,
    'airspeed': vehicle.airspeed,
    'obstacle': vehicle.rangefinder.distance
    }
    print(json.dumps(flight_stats))
