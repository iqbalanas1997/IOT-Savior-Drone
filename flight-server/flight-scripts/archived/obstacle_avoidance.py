#!/usr/bin/env python
import time
import rospy
from sensor_msgs.msg import LaserScan
import numpy as np
import math
import re
from dronekit import connect, VehicleMode
from pymavlink import mavutil

vehicle = None
drop_height = 2
drop_spacing = 4
drop_columns = 3
drop_rows = 3

def connectMyCopter():
    global vehicle
    vehicle = connect('127.0.0.1:14550', wait_ready = True)
    return vehicle


def arm_and_takeoff(targetHeight):
	while vehicle.is_armable != True:
		print("Waiting for vehicle to become armable")
		time.sleep(1)
	print("Vehicle is now armable")

	vehicle.mode = VehicleMode("GUIDED")

	while vehicle.mode!='GUIDED':
		print("Waiting for drone to enter GUIDED flight mode")
		time.sleep(1)
	print("Vehicle now in GUIDED MODE")

	vehicle.armed = True  # time delay in this request. While loop waits for success.
	while vehicle.armed==False:
		print("Waiting for vehicle to become armed")
		time.sleep(1)
	print("Props are spinning!")

	vehicle.simple_takeoff(targetHeight) ## in metres

	while True:
		print("Current Altitude: %.2f" % vehicle.location.global_relative_frame.alt)
		if vehicle.location.global_relative_frame.alt >= .96*targetHeight:
			break
		time.sleep(0.75)
	print("Target altitude reached")
	print('----')
	return None

def set_yaw(heading, clockwise, relative=True):
	if relative:
		is_relative=1 #yaw relative to direction of travel
	else:
		is_relative=0 #yaw is an absolute angle
	# create the CONDITION_YAW command using command_long_encode()
	msg = vehicle.message_factory.command_long_encode(
		0, 0,    # target system, target component
		mavutil.mavlink.MAV_CMD_CONDITION_YAW, #command
		0, #confirmation
		heading,    # param 1, yaw in degrees
		0,          # param 2, yaw speed deg/s
		clockwise,	# param 3, direction -1 ccw, 1 cw
		is_relative, # param 4, relative offset 1, absolute angle 0
		0, 0, 0)    # param 5 ~ 7 not used
	# send command to vehicle
	vehicle.send_mavlink(msg)
	time.sleep(3)

def turn_right():
	set_yaw(30, 1)

def turn_left():
	set_yaw(30, -1)

def north_position(location): 
	return float(re.search('(?<=north=)-?[0-9]+.[0-9]+', location).group(0))

def east_position(location):
	return float(re.search('(?<=east=)-?[0-9]+.[0-9]+', location).group(0))

def distance_magnitude(initial_n, initial_e, current_n, current_e):
	return math.sqrt((current_n-initial_n)**2 + (current_e-initial_e)**2)

def goto_relative_to_current_location(north, east, down):	
	# Send SET_POSITION_TARGET_LOCAL_NED command to request the vehicle fly to a specified location in the North, East, Down frame.
	msg = vehicle.message_factory.set_position_target_local_ned_encode(
		0,       # time_boot_ms (not used)
		0, 0,    # target system, target component
		mavutil.mavlink.MAV_FRAME_BODY_NED, # frame - body frame relative to current vehicle location
		0b0000111111111000, # type_mask (only positions enabled)
		north, east, down, # North, East, Down in the MAV_FRAME_BODY_NED frame
		0, 0, 0, # x, y, z velocity in m/s  (not used)
		0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink) 
	# send command to vehicle
	vehicle.send_mavlink(msg)
	initial_location = str(vehicle.location.local_frame) # Get initial location in string format
	# initial_north = north_position(initial_location) # Use north position function to get number format of relative north pos
	# initial_east = east_position(initial_location) # Use east position function to get number format of relative east pos
	distance_moved = 0 # initialise distance moved
	print('-----')
	while distance_moved < drop_spacing*0.96: # While distance moved is not close to user specified drop spacing
		# Calculate distance moved every 0.5 seconds
		distance_moved = distance_magnitude(north_position(initial_location), east_position(initial_location), north_position(str(vehicle.location.local_frame)), east_position(str(vehicle.location.local_frame)))
		print('Distance to destination: {}'.format(drop_spacing - distance_moved))
		time.sleep(0.5)
	print('Destination reached')
	print('-----')

def move_forward(drop_spacing):
	goto_relative_to_current_location(drop_spacing, 0, 0)

# globals
# scan_data = None
ranges = None
min_distance = None
min_index = None

def scan_callback(scan_msg):
    """ scan will be of type LaserScan """
    # Save a global reference to the most recent sensor state so that
    # it can be accessed in the main control loop.
    # (The global keyword prevents the creation of a local variable here.)
    # global scan_data
    global ranges
    global min_distance
    global min_index
    # if scan_msg is not None:
    ranges = scan_msg.ranges
    min_distance = np.amin(ranges)
    min_index = np.argmin(ranges)

def ros_subscriber():
    # Turn this into an official ROS node named approach
    rospy.init_node('obstacle')
    # Subscribe to the /forward_lidar topic.
    # scan_callback will be called every time a new scan message is
    # published.
    # global scan_callback
    rospy.Subscriber('/forward_lidar', LaserScan, scan_callback)

def avoid_obstacle():
    
    

def main():
    ros_subscriber()
    connectMyCopter()
    arm_and_takeoff(drop_height)
    # t_end = time.time() + 3
    # time.sleep(2)
    # while min_distance < drop_spacing:
        # time.sleep(1)
        # print(min_distance, min_index)
        if min_index > len(ranges)/2 and min_distance < drop_spacing:
            print('turn right')
            turn_right()
        elif min_index < len(ranges)/2 and min_distance < drop_spacing:
            print('turn left')
            turn_left()
        else:
            print('path clear')
        # print(len(ranges))
    

if __name__ == '__main__':
    main()