import serial
import time

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
	print('No seed actuator connected.')