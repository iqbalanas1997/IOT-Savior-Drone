#!/usr/bin/env python2

###### Dependencies ######
from dronekit import connect, VehicleMode
from pymavlink import mavutil
import time
import re
import argparse
import serial
import subprocess

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

		open_motor() # send open signal to arduino
		print('Dropping seeds..')
		time.sleep(0.3) # time that drops sufficient amount of seeds as tested
		close_motor() # send close signal to arduino

	except: # if connection to the motor is not possible dont crash programme, print error actuating
		print('No actuator connected.')

def capture_ground(column, row):
	capture_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python3', '/home/pi/iot-seed-drone/flight-server/flight-scripts/capture_ground.py', '--column', str(column), '--row', str(row)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	while capture_process.poll() is None:
		for line in iter(capture_process.stdout.readline, b''): # for each line of the output
			print(line.rstrip().decode('utf-8')) # print the output

suitable_ground = True

def analyse_ground(current_column, current_row):
	capture_ground(current_column, current_row)
	current_location_image = '/home/pi/images/Column-{}_Row-{}.jpeg'.format( current_column, current_row )
	compare_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python3', '/home/pi/iot-seed-drone/flight-server/flight-scripts/compare_colours.py', '--image1', '/home/pi/images/Column-1_Row-1.jpeg', '--image2', current_location_image], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
	while compare_process.poll() is None:
		for line in iter(compare_process.stdout.readline, b''): # for each line of the output
			print(line.rstrip().decode('utf-8')) # print the output
			if re.search('(?<=Colour Difference: )[0-9]+.[0-9]+', line.rstrip().decode('utf-8')) is not None:
				colour_difference = float(re.search('(?<=Colour Difference: )[0-9]+.[0-9]+', line.rstrip().decode('utf-8')).group(0))
				global suitable_ground
				if colour_difference <= 25:
					suitable_ground = True
				else:
					suitable_ground = False

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
	# Send SET_POSITION_TARGET_LOCAL_NED command to request the vehicle fly to a specified location in the North, East, Down frame.
	msg = vehicle.message_factory.set_position_target_local_ned_encode(
		0,		# time_boot_ms (not used)
		0, 0,	# target system, target component
		mavutil.mavlink.MAV_FRAME_LOCAL_NED,	# frame - position is relative to home location (North, East, Down frame)
		0b0000111111111000,	# type_mask (only positions enabled)
		north, east, -drop_height, # North, East, Down position
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
	time.sleep(1)

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
	# while vehicle.heading > heading*0.95 and vehicle.heading < heading*1.05:
	time.sleep(1.5)

def look_north():
	set_yaw(0, 1, False)

def look_east():
	set_yaw(90, -1, False)

def look_south():
	set_yaw(180, -1, False)

def return_home():
	vehicle.mode = VehicleMode("RTL") # Enter return to launch mode.
	while vehicle.mode != "RTL": # wait for the mode to change.
		print("Drone entering RTL mode..")
		time.sleep(1)
	print("Drone is returning home.")

def seed_planting_mission(total_rows, total_columns):

	for column in range(1, total_columns+1):

		for row in range(1, total_rows+1): # runs until the second to last row (loops go to 1 before second argument)

			print('Column: {}, Row: {}'.format(column, row)) # print what column and row currently at
			drop_seeds()
				
			print('-----')

			if column == total_columns and row == total_rows: # runs when the last row and column have been reached
				return_home() # go back top starting location
			elif column % 2 != 0 and row == total_rows:
				print('Moving east to new column:')
				look_east()
				goto_relative_to_home_location(drop_spacing * (total_rows - 1), drop_spacing * (column))
			elif column % 2 == 0 and row == total_rows:
				print('Moving east to new column:')
				look_east()
				goto_relative_to_home_location(0, drop_spacing * (column))
			# This part starts running after the first drop in a column and handles moving to the next drop location
			elif column % 2 != 0: # if column is odd and not the last drop in the column
				print('Moving north {}m:'.format(drop_spacing))
				if row == 1:
					look_north()
				goto_relative_to_home_location( drop_spacing * (row), drop_spacing * (column - 1) )
			elif column % 2 == 0: # if column is even
				print('Moving south {}m:'.format(drop_spacing))
				if row == 1:
					look_south()
				goto_relative_to_home_location( drop_spacing * (total_rows - 1) - drop_spacing * (row), drop_spacing * (column - 1) ) 


###### Main Excecutable ######

# Connect to drone on specified port
vehicle = connectMyCopter()
# Take off to specified drop height
arm_and_takeoff(drop_height)
# Start seed planting mission
while vehicle.mode=='GUIDED':
	seed_planting_mission(drop_rows, drop_columns)
# While vehicle is still armed, wait 1 second loop
# while vehicle.armed == True:
# 	time.sleep(1)
print('End of mission')
