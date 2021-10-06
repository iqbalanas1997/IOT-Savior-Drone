#!/usr/bin/env python2

###### Dependencies ######
from dronekit import connect, VehicleMode
from pymavlink import mavutil
import time
import re
import argparse
import serial
import subprocess
import numpy as np

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

def connect_copter():
	# use connection ip address of drone from user input
	connection_string = args.connect or '127.0.0.1:14550'
	# dronekit vehicle connection using ip address
	vehicle = connect(connection_string, wait_ready = True) 
	# when function is run, return 'vehicle' object to be used to control drone by other functions
	return vehicle

def arm_and_takeoff(targetHeight):
	while vehicle.is_armable != True: # while the vehicle is not armable, wait.
		print("Waiting for vehicle to become armable")
		time.sleep(1)
	print("Vehicle is now armable")

	vehicle.mode = VehicleMode("GUIDED") # set vehicle flight mode to guided

	while vehicle.mode!='GUIDED':
		print("Waiting for drone to enter GUIDED flight mode")
		time.sleep(1)
	print("Vehicle now in GUIDED flight mode")

	vehicle.armed = True  # time delay in this request. While loop waits for success.
	while vehicle.armed==False:
		print("Waiting for vehicle to become armed")
		time.sleep(1)
	print("vehicle is armed.")

	vehicle.simple_takeoff(targetHeight) # takeoff drone to height in metres

	while True:
		print("Current Altitude: %.2f" % vehicle.location.global_relative_frame.alt)
		if vehicle.location.global_relative_frame.alt >= .96*targetHeight:
			break
		time.sleep(0.75)
	print("Target altitude reached")
	print('----')

def goto_relative_to_home_location(north, east):	
	# Send SET_POSITION_TARGET_LOCAL_NED command to request the vehicle fly 
	# to a specified location in the North, East, Down frame.
	msg = vehicle.message_factory.set_position_target_local_ned_encode(
		0,		# time_boot_ms (not used)
		0, 0,	# target system, target component
		mavutil.mavlink.MAV_FRAME_LOCAL_NED,	# frame - position is relative to home location
		0b0000111111111000,	# type_mask (only positions enabled)
		north, east, -drop_height, # North, East, Down position
		0, 0, 0, # x, y, z velocity in m/s  (not used)
		0, 0, 0, # x, y, z acceleration (not supported yet, ignored in GCS_Mavlink)
		0, 0)    # yaw, yaw_rate (not supported yet, ignored in GCS_Mavlink) 
	# send command to vehicle
	vehicle.send_mavlink(msg)
	print('-----')
	while vehicle.groundspeed <= 0.3:
		print('Drone preparing to move..')
		time.sleep(1)
	while vehicle.groundspeed > 0.3:
		print('Moving to destination at {:.2f}m/s'.format(vehicle.groundspeed))
		time.sleep(1)
	print('-----')

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

def look_north():
	# look to a yaw of 0 degrees, in absolute angle
	set_yaw(0, 1, False)

def look_east():
	# look to a yaw of 90 degrees, in absolute angle
	set_yaw(90, -1, False)

def look_south():
	# look to a yaw of 180 degrees, in absolute angle
	set_yaw(180, -1, False)

def return_home():
	vehicle.mode = VehicleMode("RTL") # Enter return to launch mode.
	while vehicle.mode != "RTL": # wait for the mode to change.
		print("Drone entering RTL mode..")
		time.sleep(1)
	print("Drone is returning home.")

def drop_seeds():	
	try: # logic to open and close USB connected motor for 0.3 seconds 	
		ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1) # connection location of USB arduino set to 'ser' constant
		def open_motor(): # defines the open motor function
			ser.flush() # clear previous signals to arduino
			ser.write(b'1') # send 1 signal to arduino
		def close_motor(): # define close motor function
			ser.flush() # clear previous signals to arduino
			ser.write(b'0') # send 0 signal to arduino

		open_motor() # send open signal to arduino
		print('Dropping seeds..')
		time.sleep(0.95) # time that drops sufficient amount of seeds as tested
		close_motor() # send close signal to arduino

	except: # if connection to the motor is not possible dont crash programme, print error actuating
		# print('No actuator connected.')
		print('Dropping seeds..')
		time.sleep(0.95)

def capture_ground(column, row):
	# capture an image of the ground and save it with a name referring to its row and column
	capture_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python3', \
		'/home/ruben/iot-seed-drone/flight-server/flight-scripts/capture_ground.py',\
		'--column', str(column), '--row', str(row)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	# while the capture process is running
	while capture_process.poll() is None:
		# for each line of its output
		for line in iter(capture_process.stdout.readline, b''):
			# print the output to this scripts output
			print(line.rstrip().decode('utf-8')) 

# Initialise the suitable_ground variable as True
suitable_ground = True

def analyse_ground(current_column, current_row):
	# run the capture image function to take an image of the current location
	# capture_ground(current_column, current_row)
	start = time.time()
	time.sleep(0.75)
	print('Ground image captured.')
	# the image is saved to the raspberry pi in the following format
	current_location_image = '/home/ruben/iot-seed-drone/sample-images/Column-{}_Row-{}.jpeg'.format( current_column, current_row )
	# run the image comparison script with image 1 as the start drop location and image 2 as the current drop location
	compare_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python3',\
		'/home/ruben/iot-seed-drone/flight-server/flight-scripts/compare_colours.py', \
		'--image1', '/home/ruben/iot-seed-drone/sample-images/Column-1_Row-1.jpeg', '--image2', current_location_image], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	# while the comparison process is running
	while compare_process.poll() is None:
		#  for each of line of the process' output
		for line in iter(compare_process.stdout.readline, b''):
			# print the output of the process
			print(line.rstrip().decode('utf-8'))
			# if the output line has 'Colour Difference: ' followed by a number
			if re.search('(?<=Colour Difference: )[0-9]+.[0-9]+', line.rstrip().decode('utf-8')) is not None:
				# convert the number (that is in string format) into a decimal number format and save it to the variable, colour_difference
				colour_difference = float(re.search('(?<=Colour Difference: )[0-9]+.[0-9]+', line.rstrip().decode('utf-8')).group(0))
				# use the global variable suitable_ground
				global suitable_ground
				# if the colour difference (CIELAB Delta E) is less than or equal to 25
				if colour_difference <= 25:
					# the ground is suitable 
					suitable_ground = True
				# otherwise
				else:
					# the ground is unsuitable 
					suitable_ground = False
	end = time.time()
	# print('Analysis time elapsed = ' + str(end - start) + 's')
	global analysis_times
	analysis_times.append(end - start)

analysis_times = []
successful_drops = 0
total_drops = 0

def seed_planting_mission(total_rows, total_columns):
	global successful_drops
	global total_drops
	# for every column from 1 to the specified toal drop columns
	for column in range(1, total_columns+1): 
		# for every row from 1 to specified total drop rows
		for row in range(1, total_rows+1):
			# print to the command line what column and row the drone is currently at
			print('Column: {}, Row: {}'.format(column, row))
			total_drops += 1
			# if the current location is not the first drop destination
			if not (row == 1 and column == 1):
				print('Analysing ground..')
				# captures image of the ground at the current location and compares it to the starting location
				analyse_ground(column, row) 
				# if the ground is similar in colour to the starting location
				if suitable_ground == True: 
					print('Ground is suitable.')
					# drop seeds
					drop_seeds()
					successful_drops += 1
				# otherwise, do not drop seeds
				else: 
					print('Ground is unsuitable')
			# else, this is the first drop location
			else:
				# capture image of the ground
				# capture_ground(column, row)
				# drop seeds
				drop_seeds()
				successful_drops += 1
			# seperator for better readability
			print('-----')
			# if the last row and column have been reached
			if column == total_columns and row == total_rows: 
				# go back to the starting location and land
				return_home()
			# otherwsie if the column is odd and the row is the last in that column
			elif column % 2 != 0 and row == total_rows:
				print('Moving east to new column:')
				# turn towards the direction of travel (east)
				look_east()
				# move to the the first row of the next column
				goto_relative_to_home_location(drop_spacing * (total_rows - 1), drop_spacing * (column))
			# otherwsie if the column is even and the row is the last in that column
			elif column % 2 == 0 and row == total_rows:
				print('Moving east to new column:')
				# turn towards the direction of travel (east)
				look_east()
				# move to the the first row of the next column
				goto_relative_to_home_location(0, drop_spacing * (column))
			# otherwsie if the column is odd
			elif column % 2 != 0:
				print('Moving north {}m:'.format(drop_spacing))
				# and if the row is the first in that column
				if row == 1:
					# turn towards the direction of travel
					look_north()
				# move north
				goto_relative_to_home_location( drop_spacing * (row), drop_spacing * (column - 1) )
			# otherwise if column is even
			elif column % 2 == 0: 
				print('Moving south {}m:'.format(drop_spacing))
				# and if the row is the first in that column
				if row == 1:
					# turn towards the direction of travel
					look_south()
				# move south
				goto_relative_to_home_location( drop_spacing * (total_rows - 1) - drop_spacing * (row), drop_spacing * (column - 1) ) 

###### Main Excecutable ######

# Connect to drone on specified port
vehicle = connect_copter()
# Take off to specified drop height
arm_and_takeoff(drop_height)
# Start seed planting mission
while vehicle.mode=='GUIDED':
	seed_planting_mission(drop_rows, drop_columns)
print('Successful drops: ' + str(successful_drops) + '/' + str(total_drops))
print('Average time for ground analysis: {:.2f}s'.format(np.mean(analysis_times)))