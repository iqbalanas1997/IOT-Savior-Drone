#!/bin/bash
cd ~/iot-seed-drone/flight-server/venv/bin && source activate && gunicorn -b 127.0.0.1:5000 --worker-class eventlet -w 1 server:app