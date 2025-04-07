#!/usr/bin/python3

# @file RGBdaylight_blynk_basic.py
# @brief Blynk RGB Daylight with manual control
# @author Metaphysix
# @version 1.5

import BlynkLib
import time
#from BlynkTimer import BlynkTimer
from rgb import RGB
from daylight import Daylight
from config import Config
import argparse
import subprocess

try:
    subprocess.run(["sudo", "./pi-blaster/pi-blaster"], check=True)
except subprocess.CalledProcessError as e:
    print(f"Exception occured: {e}")

parser = argparse.ArgumentParser(description='Daylight simulator launch options')
parser.add_argument('--test', action="store_true",  help='Rapidly cycle colors')
parser.add_argument('--test-color', action="store",  help='Set to a specific daytime color')
args = parser.parse_args()

config = Config("settings.json")
# Setup RGB Light Strip
# R,G,B LED control pins
lights = RGB(config) 

# Setup Daylight Controller
day = Daylight(config,lights)

# Initialize Blynk
blynk = BlynkLib.Blynk('rGDrN4x3w9lihTz9YxvCPRzTcMvXNlrS')

# Init variables
r=0
g=0
b=0
automode = 0
start_time = 0
stop_time = 0
current_time = 0
prev_time = 0
delay = 5

def get_current_time():
    current_time = time.localtime()  # Get current time as a struct_time object
    return current_time.tm_hour * 3600 + current_time.tm_min * 60 + current_time.tm_sec

# Red LED control through V0 virtual pin
@blynk.on("V0")
def v0_write_handler(value):
    global r
    r=int(value[0])/100
    if automode == False:
        lights.color=[r, g, b, 1]
        #print(f'Red value changed to {r}')

# Blue LED control through V1 virtual pin
@blynk.on("V1")
def v1_write_handler(value):
    global b
    b=int(value[0])/100
    if automode == False:
        lights.color=[r, g, b, 1]
        #print(f'Blue value changed to {b}')
        
# Green LED control through V2 virtual pin
@blynk.on("V2")
def v2_write_handler(value):
    global g
    g=int(value[0])/100
    if automode == False:
        lights.color=[r, g, b, 1]
        #print(f'Green value changed to {g}')

# Manual/Auto mode
@blynk.on("V3")
def v3_write_handler(value):
    global automode
    if int(value[0]) == 1:  # Alarm mode
        automode = 1
        print("Alarm mode activated")
    elif int(value[0]) == 2:  # Auto mode
        automode = 2
        print("Auto mode activated")
    else:  # Manual mode
        automode = 0
        print("Manual mode activated") 
        lights.color=[r, g, b, 1]
           

# Time window
@blynk.on("V4")
def v4_time_handler(value):
    global start_time, stop_time
    start_time = int(value[0])  # start time in seconds
    stop_time = int(value[1])
    print('Start Time: {}, Stop Time: {}'.format(start_time, stop_time))
    
def lightalarm(start_time, stop_time, current_time):
    start_values=[0.01, 0.005, 0]
    end_values=[1, 0.5, 0.5]
    act_values=[0,0,0]
    total_duration=stop_time-start_time
    elapsed_duration = current_time - start_time
    ratio = elapsed_duration / total_duration
    
    for i in range(0, 3):
        act_values[i]=start_values[i] + (end_values[i] - start_values[i]) * ratio
    lights.color=act_values
    
#function to sync the data from virtual pins
@blynk.on("connected")
def blynk_connected():
    print("Raspberry Pi Connected to Blynk") 

while True:
    blynk.run()
    current_time = get_current_time()
    
    if current_time % delay == 0 and prev_time != current_time:
        prev_time = current_time
        # Alarm
        if automode == 1 and current_time >= start_time and current_time <= stop_time:
            lightalarm(start_time, stop_time, current_time)
    
        # Daylight sim
        if automode == 2:
            day.update(current_time)
        
