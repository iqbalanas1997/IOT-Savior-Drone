#!/usr/bin/env python3

from picamera import PiCamera
import argparse

parser = argparse.ArgumentParser(description='Drop Row and Column')

parser.add_argument('--row')
parser.add_argument('--column')

args = parser.parse_args()

column = args.column
row = args.row

filename = 'Column-' + str(column) + '_Row-' + str(row) + '.jpeg' 
filepath = "/home/pi/images/" + filename
camera = PiCamera()
camera.resolution = (500, 500)
camera.capture(filepath)

print('Ground image captured.')