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

def start_mission():
    mission_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', '/home/ruben/iot-seed-drone/flight-server/flight-scripts/basic_mission.py', '--connect', '127.0.0.1:14550',\
    '--height', str(drop_height), '--spacing', str(drop_spacing), '--columns', str(drop_columns), '--rows', str(drop_rows) ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return mission_process

def start_stats():
    stats_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', '/home/ruben/iot-seed-drone/flight-server/flight-scripts/flight_stats.py', '--connect', '127.0.0.1:14551'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return stats_process

def land_mode():
    land_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', '/home/ruben/iot-seed-drone/flight-server/flight-scripts/land.py', '--connect', '127.0.0.1:14550'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return land_process

def return_to_launch():
    home_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', '/home/ruben/iot-seed-drone/flight-server/flight-scripts/return-to-launch.py', '--connect', '127.0.0.1:14550'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return home_process

def disarm_drone():
    disarm_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', '/home/ruben/iot-seed-drone/flight-server/flight-scripts/disarm.py', '--connect', '127.0.0.1:14550'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return disarm_process

def drop_seeds():
    seeds_process = subprocess.Popen(['stdbuf', '-o0', '/usr/bin/python', '/home/ruben/iot-seed-drone/flight-server/flight-scripts/disperse_seeds.py'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return seeds_process

@socket.on('flight-start') # when flight start command received from frontend socket
def on_flight_start():
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
        for line in iter(land_process.stdout.readline, b''): # read each line of output
            emit('message', line.rstrip().decode('utf-8')) # send the output to the frontend app

@socket.on('flight-home')
def on_home():
    if mission_process is not None:
        mission_process.terminate()
        mission_process.wait()
    home_process = return_to_launch()
    while home_process.poll() is None: # while process is running
        for line in iter(home_process.stdout.readline, b''): # read each line of output
            emit('message', line.rstrip().decode('utf-8')) # send outputs to mission log

@socket.on('flight-stop')
def on_flight_stop():
    mission_process.terminate()
    mission_process.wait()

@socket.on('flight-stats')
def get_flight_stats():
    stats_process = start_stats()
    while stats_process.poll() is None: # while process is running
        for line in iter(stats_process.stdout.readline, b''):
            emit('stats', line.rstrip().decode('utf-8'))

@socket.on('drop-seeds')
def on_drop_seeds():
    seeds_process = drop_seeds()
    while seeds_process.poll() is None: # while process is running
        for line in iter(seeds_process.stdout.readline, b''): # for each line of the output
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