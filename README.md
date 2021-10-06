# A Python and Linux based autonomous drone with a control web application developed using React and Flask

Project demonstration video: https://www.youtube.com/watch?v=-t-tnROBe4w 

The drone can go on a seed planting mission using arguments submitted to the mission flight script - column, row, height, spacing. It sends a drop signal to an arduino based system with a Raspberry Pi USB connection and pyserial. It will be able to avoid obstacles (simulated with gazebo and ROS) and verify that the drop location is suitable using image colour comparison. 

The control web application is served with nginx on the drone's Raspberry Pi. Serves React frontend app and Flask backend. A RTMP live video server is to be implemented.

## Key files
### basic-mission.py
in flight-server/flight-scripts/ - Connects to the drone on port 14550. The drone flight script is programmed with Dronekit, a python API for the flight control software ArduPilot. Takes column, row, height, spacing, and connection address as arguments.

### flight-stats.py
python flight stats script in flight-server/flight-scripts/ - Connects to the drone on port 14551 and returns critical data until the drone becomes unarmed.

### server.py
in flight-scripts/venv/bin/ (Rapberry Pi virtual environement. Development PC venv is flight-scripts/lnx-venv) - 
A flask server that is able to call subprocesses for the flight scripts (required due to dronekit being Python2.7 and web server dependencies being Python3). Flight mission subprocess PIPE output sends mission log to frontend web application using web sockets. Uses gunicorn and eventlet to allow for flask-socketio connection to the frontend for real time communication. Flight stats subprocess sends flight statistics using flight-stats.py subprocess output.

### App.js
in src - React control frontend, mobile centred styled with tailwindCSS and uses socket.io and REST API to communicate with backend. Shows a mission log using the output from the flight script subprocess. Shows flight statistics using the output from the flight stats subprocess. Live video feed to be implemented.

<img width="577" alt="Screenshot 2021-06-19 at 20 20 21" src="https://user-images.githubusercontent.com/66388962/122653366-dc0c4780-d13b-11eb-9dbd-ddd557488e06.png">

# Project Report
## Individual
[Engel_Team29_ IndividualReport.pdf](https://github.com/RubenEngel/iot-seed-drone/files/6681264/Engel_Team29_.IndividualReport.pdf)
## Team 
[Team29_TeamReport.pdf](https://github.com/RubenEngel/iot-seed-drone/files/6681266/Team29_TeamReport.pdf)
