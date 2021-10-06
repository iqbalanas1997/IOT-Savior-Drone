###### Dependencies ######
from dronekit import connect, VehicleMode
import time
import math
import re
import argparse
from pymavlink import mavutil
import serial
import rospy
from sensor_msgs.msg import LaserScan
import numpy as np

##### Functions ######

parser = argparse.ArgumentParser(description='Drone commands')

parser.add_argument('--connect')
parser.add_argument('--height')
parser.add_argument('--spacing')
parser.add_argument('--rows')
parser.add_argument('--columns')

args = parser.parse_args()

connection_string = '127.0.0.1:14550' #args.connect
drop_height = 5 #float(args.height)
drop_spacing = 5 #float(args.spacing)
drop_columns = 3 #int(args.columns)
drop_rows = 3 #int(args.rows)

def connectMyCopter():

	vehicle = connect(connection_string, wait_ready = True)

	return vehicle

def drop_seeds():	
	try:	
		ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
		def open_motor():
			ser.flush()
			ser.write(b'1')
		def close_motor():
			ser.flush()
			ser.write(b'0')
		open_motor()
		print('Dropping seeds..')
		time.sleep(3)
		close_motor()
		time.sleep(1)
	except:
		print('Error actuating.')

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
		mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED, # frame - body frame relative to current vehicle location
		0b0000111111111000, # type_mask (only positions enabled)
		north, east, down, # North, East, Down in the MAV_FRAME_BODY_NED frame
		0, 0, 0, # x, y, z velocity in m/s  (not used)
		0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink) 
	# send command to vehicle
	vehicle.send_mavlink(msg)
	# initial_location = str(vehicle.location.local_frame) # Get initial location in string format
	# distance_moved = 0 # initialise distance moved
	# print('-----')
	# while distance_moved < drop_spacing*0.96: # While distance moved is not close to user specified drop spacing
	# 	# Calculate distance moved every 0.5 seconds
	# 	distance_moved = distance_magnitude(north_position(initial_location), east_position(initial_location), north_position(str(vehicle.location.local_frame)), east_position(str(vehicle.location.local_frame)))
	# 	print('Distance to destination: {}'.format(drop_spacing - distance_moved))
	# 	time.sleep(0.5)
	# print('Destination reached')
	# print('-----')
	print('-----')
	time.sleep(2)
	while vehicle.groundspeed > 0.3:
		print('Moving to destination at {:.2f}m/s'.format(vehicle.groundspeed))
		
		time.sleep(1)
	print('-----')

def move_forward(distance):
	goto_relative_to_current_location(distance, 0, 0)

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
	time.sleep(1.5)

def turn_right(degrees):
	set_yaw(degrees, 1)

def turn_left(degrees):
	set_yaw(degrees, -1)

def return_home():
	vehicle.parameters['RTL_ALT'] = 0 # Stay at current altitude when returning home
	vehicle.mode = VehicleMode("RTL") # Enter return to launch mode.
	while vehicle.mode != "RTL": # wait for the mode to change.
		time.sleep(1)
		print("Drone is returning home.")

def seed_planting_mission():
	for column in range(1, drop_columns+1):

		for row in range(1, drop_rows+1):
			print('Column: %d, Row: %d' % (column, row)) # print what column and row currently at
			drop_seeds()

			if column == drop_columns and row == drop_rows: # if all column and rows have been reached, return home.
				return_home()
			elif column % 2 != 0 and row == drop_rows: # if column is odd and row is last, move right to get to new column.
				print('Moving right to new column.')
				turn_right(90)
				obstacle_avoidance()
				move_forward(drop_spacing)
			elif column % 2 == 0 and row == 1: # if column is even & is first row in column move right.
				print('Moving Right {}m'.format(drop_spacing))
				turn_right(90)
				obstacle_avoidance()
				move_forward(drop_spacing)
			elif column % 2 == 0 and row == drop_rows: # if column is even and row is last, move left to get to new column.
				print('Moving left to new column.')
				turn_left(90)
				obstacle_avoidance()
				move_forward(drop_spacing)
			elif column % 2 != 0 and column != 1 and row == 1 : # if column is odd & is not first column & first row in column, move left. 
				print('Moving Left {}m'.format(drop_spacing))
				turn_left(90)
				obstacle_avoidance()
				move_forward(drop_spacing)
			else: # if none of the conditions previous have been met, move forward.
				print('Moving Forward {}m'.format(drop_spacing))
				obstacle_avoidance()
				move_forward(drop_spacing)

# globals
ranges = None
obstacle_distance = None # the minimum distacne read from lidar sensor
min_distance_index = None # where in the array is the minimum distance found (end of array is the left-most point)
avoid_distance = 2 # stay 2 meters away from

def scan_callback(scan_msg):
    """ scan will be of type LaserScan """
    # Save a global reference to the most recent sensor state so that
    # it can be accessed in the main control loop.
    # (The global keyword prevents the creation of a local variable here.)
    # global scan_data
    global ranges
    global obstacle_distance
    global min_distance_index
    # if scan_msg is not None:
    ranges = scan_msg.ranges
    obstacle_distance = np.amin(ranges)
    min_distance_index = np.argmin(ranges)

def ros_subscriber():
    # Turn this into an official ROS node named approach
    rospy.init_node('obstacle')
    # Subscribe to the /forward_lidar topic.
    # scan_callback will be called every time a new scan message is
    # published.
    # global scan_callback
    rospy.Subscriber('/forward_lidar', LaserScan, scan_callback)

def check_obstacle():
	if obstacle_distance < drop_spacing * 1.5:
		obstacle = True
		# If the minimum distance is observed in the second half of the array, obstacle is on the left 
		if min_distance_index > len(ranges)/2:
			obstacle_position = 'left'
		# If the minimum distance is observed in the first half of the array, obstacle is on the right 
		else:
			obstacle_position = 'right'
	else:
		obstacle = False
		obstacle_position = None
	return obstacle, obstacle_position


def avoid_on_right(turn_angle, obstacle_distance):
	 # inverse tan of avoid distance over distance to obstacle
	hyp_distance = math.sqrt( avoid_distance**2 + obstacle_distance**2 ) # find hypothenuse
	print('Moving forward: {}m'.format(hyp_distance))
	move_forward(hyp_distance)
	turn_left(2*turn_angle)
	move_forward(hyp_distance)
	turn_right(turn_angle)

def avoid_on_left(turn_angle, obstacle_distance):
	 # inverse tan of avoid distance over distance to obstacle
	hyp_distance = math.sqrt( avoid_distance**2 + obstacle_distance**2 ) # find hypothenuse
	move_forward(hyp_distance)
	turn_right(2*turn_angle)
	move_forward(hyp_distance)
	turn_left(turn_angle)

def obstacle_avoidance():
	# check obstacle
	[obstacle, obstacle_position] = check_obstacle()
	orginal_obstacle_distance = obstacle_distance
	turn_angle = math.degrees(math.atan( avoid_distance / orginal_obstacle_distance ))
	if obstacle == True:
		print('Obstacle in path')
		if obstacle_position == 'left':
			turn_right(turn_angle)
			[obstacle, _] = check_obstacle()
			if obstacle == False:
				avoid_on_right(turn_angle, orginal_obstacle_distance)
			elif obstacle == True:
				turn_left( 2 * turn_angle )
				[obstacle, _] = check_obstacle()
				if obstacle == False:
					avoid_on_left(turn_angle, orginal_obstacle_distance)
				elif obstacle == True:
					print('No route around found.')
					vehicle.mode = VehicleMode("LAND")
		if obstacle_position == 'right':
			turn_left(turn_angle)
			[obstacle, _] = check_obstacle()
			if obstacle == False:
				avoid_on_left(turn_angle, orginal_obstacle_distance)
			elif obstacle == True:
				turn_right(2 * turn_angle)
				[obstacle, _] = check_obstacle()
				if obstacle == False:
					avoid_on_right(turn_angle, orginal_obstacle_distance)
				elif obstacle == True:
					print('No route around found.')
					vehicle.mode = VehicleMode("LAND")
	else:
		print('No obstacles in path')

###### Main Excecutable ######

ros_subscriber()

# Connect to drone on specified port
vehicle = connectMyCopter()
# Take off to specified drop height
arm_and_takeoff(drop_height)

# Start seed planting mission
while vehicle.mode=='GUIDED':
	seed_planting_mission()