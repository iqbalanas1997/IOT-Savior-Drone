###### Dependencies ######
from dronekit import connect, VehicleMode
import time
import math
import re
import argparse
from pymavlink import mavutil
import serial

##### Functions ######

parser = argparse.ArgumentParser(description='Drone commands')

parser.add_argument('--connect') # creates an argument for connection string of the drone
parser.add_argument('--height') # creates an argument for flight height of drone
parser.add_argument('--spacing') # creates an argument for spacing between seed drops
parser.add_argument('--rows') # creates an argument for drop rows
parser.add_argument('--columns') # creates an argument for drop columns

args = parser.parse_args() # get arguments that user has input when starting program

# set user inputted arguments to constants used in program
drop_height = float(args.height) 
drop_spacing = float(args.spacing)
drop_columns = int(args.columns)
drop_rows = int(args.rows)

def connectMyCopter():

	connection_string = args.connect # use connection ip address of drone from user input

	vehicle = connect(connection_string, wait_ready = True) # dronekit vehicle connection using ip address

	return vehicle # when fucntion is run, return vehicle constant to be used to control drone by other functions

def drop_seeds():	
	try: # logic to open and close USB connected motor for 0.3 seconds 	
		ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1) # connection location of USB arduino set to 'ser' constant
		def open_motor(): # defines the open motor function
			ser.flush() # clear previous signals to arduino
			ser.write(b'1') # send 1 signal to arduino
		def close_motor(): # define close motor function
			ser.flush() # clear previous signals to arduino
			ser.write(b'0') # send 0 signal to arduino

		open_motor()
		print('Dropping seeds..')
		time.sleep(0.3) # time that drops sufficient amount of seeds as tested
		close_motor()

	except: # if connection to the motor is not possible dont crash programme, print error actuating
		print('Error actuating.')

def arm_and_takeoff(targetHeight):
	while vehicle.is_armable != True: # while the vehicle is not armable, wait.
		print("Waiting for vehicle to become armable")
		time.sleep(1)
	print("Vehicle is now armable")

	vehicle.mode = VehicleMode("GUIDED") # set vehicle flight mode to guided

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
	# searches the string returned by MAVLink location call to get the north position as a decimal number
	return float(re.search('(?<=north=)-?[0-9]+.[0-9]+', location).group(0))

def east_position(location):
	# searches the string returned by MAVLink location call to get the east position as a decimal number
	return float(re.search('(?<=east=)-?[0-9]+.[0-9]+', location).group(0))

def distance_magnitude(initial_n, initial_e, current_n, current_e):
	# calculates the hypotenuse using the north and east positions
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
	print('-----')
	time.sleep(2)
	while vehicle.groundspeed > 0.3:
		print('Moving to destination at {:.2f}m/s'.format(vehicle.groundspeed))
		time.sleep(1)
	print('-----')
	# # get initial location in string format
	# initial_location = str(vehicle.location.local_frame) 
	# # initialise distance moved
	# distance_moved = 0 
	# print('-----')
	# # While distance moved is not 96% of user specified drop spacing
	# while distance_moved < drop_spacing*0.96: 
	# 	# Calculate distance moved every 0.5 seconds
	# 	distance_moved = distance_magnitude(north_position(initial_location), east_position(initial_location),\
	# 		north_position(str(vehicle.location.local_frame)), east_position(str(vehicle.location.local_frame)))
	# 	# print the distance left to travel to the command line
	# 	print('Distance to destination: {}'.format(drop_spacing - distance_moved))
	# 	time.sleep(0.5)
	# print('Destination reached')
	# print('-----')

def set_yaw(heading, clockwise, relative):
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

def move_forward(drop_spacing):
	# move relative north by specified drop spacing
	goto_relative_to_current_location(drop_spacing, 0, 0)

def turn_right():
	# turn 90 degrees clockwise relative to current heading
	set_yaw(90, 1, True)

def turn_left():
	# turn 90 degrees anticlockwise relative to current heading
	set_yaw(90, -1, True)

def return_home():
	vehicle.mode = VehicleMode("RTL") # Enter return to launch mode.
	while vehicle.mode != "RTL": # wait for the mode to change.
		time.sleep(1)
		print("Drone is returning home.")

def seed_planting_mission(drop_rows, drop_columns):
	# for every column from 1 to the specified toal drop columns
	for column in range(1, drop_columns+1): 
		# for every row from 1 to specified total drop rows
		for row in range(1, drop_rows+1):
			print('Column: %d, Row: %d' % (column, row)) # print what column and row currently at
			# send drop seeds signal to arduino
			drop_seeds()
			# if all column and rows have been reached
			if column == drop_columns and row == drop_rows:
				# go back to the starting location and land
				return_home()
			# if column is odd and row is the last in that column
			elif column % 2 != 0 and row == drop_rows:  
				print('Moving right to new column.')
				# turn 90 degrees right relative to current heading
				turn_right()
				# move forward specified drop spacing
				move_forward(drop_spacing)
			# if column is even & the row is the first in the column.
			elif column % 2 == 0 and row == 1: 
				print('Moving Right {}m'.format(drop_spacing))
				# turn 90 degrees right relative to current heading
				turn_right()
				# move forward specified drop spacing (in metres) relative to current location
				move_forward(drop_spacing)
			# if column is even and row is last, move left to get to new column.
			elif column % 2 == 0 and row == drop_rows: 
				print('Moving left to new column.')
				# turn 90 degrees left relative to current heading
				turn_left()
				# move forward specified drop spacing meters relative to current location
				move_forward(drop_spacing)
			# if column is odd but it is not the first column & the row is the first in the column
			elif column % 2 != 0 and column != 1 and row == 1 :  
				print('Moving Left {}m'.format(drop_spacing))
				# turn 90 degrees left relative to current heading
				turn_left()
				# move forward specified drop spacing meters relative to current location
				move_forward(drop_spacing)
			# if none of the conditions previous have been met
			else: 
				print('Moving Forward {}m'.format(drop_spacing))
				# move forward specified drop spacing meters relative to current location
				move_forward(drop_spacing)


###### Main Excecutable ######

# Connect to drone on specified port
vehicle = connectMyCopter()
# Take off to specified drop height
arm_and_takeoff(drop_height)
# Start seed planting mission
seed_planting_mission(drop_rows, drop_columns)
# While vehicle is still armed, wait 1 second loop
while vehicle.armed == True:
	time.sleep(1)
