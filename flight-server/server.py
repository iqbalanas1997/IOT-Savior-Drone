#!/usr/bin/env python3

from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import datetime
import time
import subprocess
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
CORS(app, support_credentials=True)
socket = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=True)

@app.route('/api/time')
def get_current_time():
    return {'time': datetime.datetime.now()}

###### GET FLIGHT PARAMETER FROM FRONT END SUBMISSION

drop_height = 0
drop_columns = 0
drop_rows = 0
drop_spacing = 0

@app.route('/api/params', methods = ['POST']) # when post method received on api route
def get_flight_params(): # complete the following function
    flight_params = request.get_json() # get json object of flight parameters
    global drop_height # use global variable in this function
    global drop_columns # use global variable in this function
    global drop_rows # use global variable in this function
    global drop_spacing # use global variable in this function
    drop_height = flight_params['dropHeight'] # set drop height to the number received from front end
    drop_columns = flight_params['dropColumns'] # set drop columns to the number received from front end
    drop_rows = flight_params['dropRows'] # set drop rows to the number received from front end
    drop_spacing = flight_params['dropSpacing'] # set drop spacing to the number received from front end
    return 'Done', 201 # send status code back to front end

@socket.on('connect') # when user connects to socket
def on_connect():
    print('user connected')

@socket.on('disconnect') # when user disconnects from socket
def on_disconnect():
    print('Client disconnected')

mission_process = None
stats_process = None

# The following functions handle starting a subprocess. 
# Subprocesses are required as dronekit is a python2 module and the server is a python3 script. 
# The output text is available to the server due to 'stdout=subprocess.PIPE'.  
# 'stdbuf -o0' allows the output stream to be unbuffered, so the result is viewable as soon as it happens, 
# otherwise the output text will only show when the process is complete.

def start_mission():
    # sends the drone on a seed planting mission with the defined flight parameters
    mission_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', \
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/basic_mission.py',\
            '--connect', '127.0.0.1:14550',\
            '--height', str(drop_height), '--spacing', str(drop_spacing), '--columns', str(drop_columns), '--rows', str(drop_rows) ],\
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return mission_process

def start_stats():
    # starts a dronekit script that prints live data such as velocity, altitude and battery life
    stats_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python',\
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/flight_stats.py',\
            '--connect', '127.0.0.1:14551'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return stats_process

def land_mode():
    # starts a DroneKit script to put the drone into ‘LAND’ mode
    land_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python',\
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/land.py',\
            '--connect', '127.0.0.1:14550'],\
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return land_process

def return_to_launch():
    # starts a DroneKit script to put the drone into ‘RTL’ mode
    home_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python',\
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/return-to-launch.py',\
            '--connect', '127.0.0.1:14550'], \
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return home_process

def disarm_drone():
    # starts a DroneKit script that stops the drones motors in case of emergency
    disarm_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python',\
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/disarm.py',\
            '--connect', '127.0.0.1:14550'],\
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return disarm_process

def drop_seeds():
    # starts a programme to open and close the seed dispersion mechanism through the USB connected Arduino
    seeds_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python',\
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/disperse_seeds.py'],\
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return seeds_process

def capture_image():
    
    capture_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python3',\
            '/home/pi/iot-seed-drone/flight-server/flight-scripts/capture_image.py'],\
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return capture_process

@socket.on('flight-start') # when flight start command received from frontend socket
def on_flight_start():
    # send mission log message to front end confirming parameters sent succesfully
    emit('message', 'Flight parameters sent successfully.')
    global mission_process
    mission_process = start_mission()
    while mission_process.poll() is None: # while process is running
        for line in iter(mission_process.stdout.readline, b''):
            emit('message', line.rstrip().decode('utf-8'))
            if re.search('(?<=Column: )[0-9]+', line.rstrip().decode('utf-8')) is not None:
                emit('column', re.search('(?<=Column: )[0-9]+', line.rstrip().decode('utf-8')).group(0))
            if re.search('(?<=Row: )[0-9]+', line.rstrip().decode('utf-8')) is not None:
                emit('row', re.search('(?<=Row: )[0-9]+', line.rstrip().decode('utf-8')).group(0))
    emit('message', 'Mission complete.')
    time.sleep(1)
    emit('status', 'complete')

@socket.on('flight-land')
def on_land():
    mission_process.terminate()
    mission_process.wait()
    land_process = land_mode()
    while land_process.poll() is None: # while process is running
        for line in iter(land_process.stdout.readline, b''):
            emit('message', line.rstrip().decode('utf-8'))

@socket.on('flight-home')
def on_home():
    if mission_process is not None:
        mission_process.terminate()
        mission_process.wait()
    home_process = return_to_launch() # start the return to home subprocess and set it to variable home_process
    while home_process.poll() is None: # while process is running
        for line in iter(home_process.stdout.readline, b''): # for each line of the output
            emit('message', line.rstrip().decode('utf-8')) # send output messages to mission log

@socket.on('flight-stop')
def on_flight_stop():
    mission_process.terminate()
    mission_process.wait()

@socket.on('flight-stats')
def get_flight_stats():
    stats_process = start_stats()
    while stats_process.poll() is None: # while process is running
        for line in iter(stats_process.stdout.readline, b''): # for each line of the output
            emit('stats', line.rstrip().decode('utf-8')) # send data to frontend

@socket.on('drop-seeds')
def on_drop_seeds():
    seeds_process = drop_seeds()
    while seeds_process.poll() is None: # while process is running
        for line in iter(seeds_process.stdout.readline, b''): # for each line of the output
            emit('message', line.rstrip().decode('utf-8')) # send output message to mission log

@socket.on('image-capture')
def on_image_capture():
    capture_process = capture_image()
    while capture_process.poll() is None: # while process is running
        for line in iter(capture_process.stdout.readline, b''): # for each line of the output
            emit('message', line.rstrip().decode('utf-8')) # send output message to mission log

@socket.on('disarm')
def on_disarm():
    if mission_process is not None:
        mission_process.terminate()
        mission_process.wait()
    disarm_process = disarm_drone()
    while disarm_process.poll() is None: # while process is running
        for line in iter(disarm_process.stdout.readline, b''): # for each line of the output
            emit('message', line.rstrip().decode('utf-8')) # send output message to mission log

if __name__ == '__main__':
    socket.run(app)