#!/bin/bash
import sqlite3
import board
import busio
import time
import math
from datetime import datetime
import twilio
import RPi.GPIO as GPIO
from time import sleep
from twilio.rest import Client
import threading
from socket import socket, AF_INET, SOCK_DGRAM
from accel2 import accel
import smbus
from time import sleep
 
# Register accelerometer
power_mgmt_1 = 0x6b
power_mgmt_2 = 0x6c
 
bus = smbus.SMBus(1) 
address = 0x68       # check address via i2cdetect

# Activate module
bus.write_byte_data(address, power_mgmt_1, 0)

#Twilio
client = Client("XXXXXXXXXXXXXXXXXXXXXXXXXXX", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

# Defining variables
# Accelerometer variables
x = 0
y = 0
z = 0
svm = 0
runs = 0
pastSvm = 0
svmTotal = 0
svmAverage = 0
pastSvmAverage = 0
pastPastSvmAverage = 0

# Variables required for fall()
movement = 0
pastTime = 0
pastTime2 = 0
currentTime = 0
complete = False

# Socket communication
SERVER_IP   = '192.168.XXX.XXX' 
PORT_NUMBER = 5000
SIZE = 1024
print("Test client sending packets to IP {0}, via port {1}\n".format(SERVER_IP, PORT_NUMBER))
myMessage = "Activate"
mySocket = socket( AF_INET, SOCK_DGRAM )

#if fall detected, monitor wearer for return to normal movement in designated period of time
            
def fall():
    movement = 0
    seconds = 20
    complete = False
    pastTime = time.time()
    time.clock()
    currentTime = time.time()
    timer = currentTime - pastTime
    while timer <= 5 and complete == False: # Check for five seconds if their is a change in orientation of the individual
        x, y, z, svm = accel.svm()
        xRot, yRot = accel.rotation(x, y, z)
        currentTime = time.time()
        timer = currentTime - pastTime
        if xRot >= 45:
            pastTime2 = time.time()
            time.clock()
            elapsed = 0
            sleep(1)
            while elapsed < seconds: # Check for 20 seconds if there is any movement of the individual
                pastSvm = svm
                x, y, z, svm = accel.svm()
                elapsed = time.time() - pastTime2
                if accel.motion(svm, pastSvm, 0.2) == True:
                    movement += 1
                    print(movement)
                time.sleep(0.1)
            if movement >= 6: # If movement is detected more than 5 times normal movement has been resumed
                print("Normal movement resumed")
            else: # If movement is detected less than 5 times Fallbot is launched
                complete = True
                print("Fall detected and person not moving. Fallbot will be launched")
                sleep(1) # Delay in seconds
                mySocket.sendto(myMessage.encode('utf-8'),(SERVER_IP,PORT_NUMBER))
                client.messages.create(to="+XXXXXXXXXXXX",
                                        from_="+XXXXXXXXXXXX",
                                        body= "Elderly person has fallen. Fallbot has been launched")
        elif yRot <= 45:
            pastTime2 = time.time()
            time.clock()
            elapsed = 0
            sleep(1)
            while elapsed < seconds: # Check for 20 seconds if there is any movement of the individual
                pastSvm = svm
                x, y, z, svm = accel.svm()
                elapsed = time.time() - pastTime2
                if accel.motion(svm, pastSvm, 0.2) == True:
                    movement += 1
                    print(movement)
                time.sleep(0.1)
            if movement >= 6: # If movement is detected more than 5 times normal movement has been resumed
                print("Normal movement resumed")
            else: # If movement is detected less than 5 times Fallbot is launched
                complete = True
                print("Fall detected and person not moving. Fallbot will be launched")
                sleep(1) # Delay in seconds
                mySocket.sendto(myMessage.encode('utf-8'),(SERVER_IP,PORT_NUMBER))
                client.messages.create(to="+XXXXXXXXXXXX",
                                        from_="+XXXXXXXXXXXX",
                                        body= "Elderly person has fallen. Fallbot has been launched")
       
x, y, z, svm = accel.svm()
sleep(0.1)
print("Ready")
while True:
	runs += 1
        svmTotal, svmAverage = accel.average(svm, runs, svmTotal)
        print(svmAverage)
        x, y, z, svm = accel.svm()
        xRot, yRot = accel.rotation(x, y, z)
        print(svm)
        print(xRot, yRot)
        print()
        if runs >= 3:
        	accell = accel.freefall(svm, pastPastSvmAverage)
        elif runs == 2:
            	accell = accel.freefall(svm, pastSvmAverage)
        elif runs == 1:
            	accell = accel.freefall(svm, svmAverage)
            
        if accell == True: # If a drop of SVM towards zero is detected, then it checks for other phases of a fall
            	print("Fall detected. Checking for movement")
            	fall()

        pastSvm = svm
        sleep(0.1)
        pastSvmAverage = svmAverage
        pastPastSvmAverage = pastSvmAverage
    
GPIO.cleanup()
