#!/usr/bin/python
import smbus
from time import sleep
import board
import busio
import time
import math
from datetime import datetime

x = 0
y = 0
z = 0
svmm = 0
ranges = 0.2
# Register
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c
bus = smbus.SMBus(1) # 
address = 0x68       # via i2cdetect
 
# Activate module
bus.write_byte_data(address, power_mgmt_1, 0)

class accel():
    def svm():  
        accelerometer_xout = accel.read_word_2c(0x3b) # Reading x acceleration
        accelerometer_yout = accel.read_word_2c(0x3d) # Reading y acceleration
        accelerometer_zout = accel.read_word_2c(0x3f) # Reading z acceleration

        x = accelerometer_xout / 16384.0 # Calculting x acceleration by dividing raw data by sensitivity
        y = accelerometer_yout / 16384.0 # Calculting y acceleration by dividing raw data by sensitivity
        z = accelerometer_zout / 16384.0 # Calculting z acceleration by dividing raw data by sensitivity

        svmm = math.sqrt(math.pow(x, 2) + math.pow(y, 2) + math.pow(z, 2)) # Calculating SVM using vector mathematics

        return (x, y, z, svmm)

    def rotation(x, y, z):
        xRot = accel.get_x_rotation(x, y, z) # Calculating x rotation
        yRot = accel.get_y_rotation(x, y, z) # Calculating y rotation

        if xRot < 0: # Make sure that the x rotation isn't negative
            xRot = xRot * -1
        if yRot < 0: # Make sure that the y rotation isn't negative
            yRot = yRot * -1

        return xRot, yRot

    def average(value, run, total):
        total += value
        average = total / run # Calculating average

        return (total, average)

    def motion(svm, past, ranges):
        if svm <= (past - ranges) or svm >= (past + ranges): # Checking for any movement
            return (True)
        else:
            return (False)

    def freefall(svm, average):
        if svm <= (average - 0.3): # Checking for a drop in SVM
            return (True)
        else:
            return (False)

    def read_byte(reg):
        return bus.read_byte_data(address, reg)
     
    def read_word(reg):
        h = bus.read_byte_data(address, reg)
        l = bus.read_byte_data(address, reg+1)
        value = (h << 8) + l

        return value
     
    def read_word_2c(reg):
        val = accel.read_word(reg) # Reading the raw data
        if (val >= 0x8000):
            return -((65535 - val) + 1)
        else:
            return val
     
    def dist(a,b):
        return math.sqrt((a*a)+(b*b)) # Finding the root sum of squares
     
    def get_y_rotation(x,y,z):
        radians = math.atan2(x, accel.dist(y,z))
        return -math.degrees(radians)
     
    def get_x_rotation(x,y,z):
        radians = math.atan2(y, accel.dist(x,z))
        return math.degrees(radians)
