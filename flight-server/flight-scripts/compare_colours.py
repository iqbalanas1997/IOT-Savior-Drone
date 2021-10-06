#!/usr/bin/env python3

import argparse
from colorthief import ColorThief
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
# from datetime import datetime
import time

parser = argparse.ArgumentParser(description='Specify images to compare')

parser.add_argument('--image1') # creates an argument for drop rows
parser.add_argument('--image2') # creates an argument for drop columns

# gets arguments submitted to program at initial run
args = parser.parse_args()
image1 = args.image1 # file path of image1 from user input 
image2 = args.image2 # file path of image2 from user input 

# Initialise color_thief classes using specified image filepaths
image1_color_thief = ColorThief(image1)
image2_color_thief = ColorThief(image2)

# print('Analysing Ground..')
start = time.time()
# Use color_thief to return an RGB array of dominant colour
# Image1 3 element array of RGB colours, quality is how many pixels are skipped in analysis (larger number speeds up process)
image1_colour = image1_color_thief.get_color(quality=1)
# Image2 3 element array of RGB colours, quality is how many pixels are skipped in analysis (larger number speeds up process)
image2_colour = image2_color_thief.get_color(quality=1) 

# Convert into color_math RGB object using the RGB array found by color_thief
image1_rgb = sRGBColor(image1_colour[0], image1_colour[1], image1_colour[2])
image2_rgb = sRGBColor(image2_colour[0], image2_colour[1], image2_colour[2])

# Convert from RGB to Lab Color Space
image1_lab = convert_color(image1_rgb, LabColor)
image2_lab = convert_color(image2_rgb, LabColor)

# Difference in the CIE color space
delta_e = delta_e_cie2000(image1_lab, image2_lab)
end = time.time()
# print('Analysis Complete')

print('Colour Difference: ' + f'{delta_e:.2f}')
print('{}'.format(end - start))
