import serial               #import serial pacakge
from time import sleep
import webbrowser           #import package for opening link in browser
import sys #import system package
import board
import busio
import math
from twilio.rest import Client


#twilio
client = Client("XXXXXXXXXXXXXXXXXXXX", "XXXXXXXXXXXXXXXXXXXXXX")


def GPS_Info():
    global NMEA_buff
    global lat_in_degrees
    global long_in_degrees
    nmea_time = []
    nmea_latitude = []
    nmea_longitude = []
    nmea_time = NMEA_buff[0]                    #extract time from GPGGA string
    nmea_latitude = NMEA_buff[1]                #extract latitude from GPGGA string
    nmea_longitude = NMEA_buff[3]               #extract longitude from GPGGA string
    
    print("NMEA Time: ", nmea_time,'\n')
    print ("NMEA Latitude:", nmea_latitude,"NMEA Longitude:", nmea_longitude,'\n')
    
    lat = float(nmea_latitude)                 #convert string into float for calculation
    long = float(nmea_longitude)*-1                #convertr string into float for calculation
    
    lat_in_degrees = convert_to_degrees(lat)    #get latitude in degree decimal format
    long_in_degrees = convert_to_degrees(long) #get longitude in degree decimal format
    
#convert raw NMEA string into degree decimal format   
def convert_to_degrees(raw_value):
    decimal_value = raw_value/100.00
    degrees = int(decimal_value)
    mm_mmmm = (decimal_value - int(decimal_value))/0.6
    position = degrees + mm_mmmm
    position = "%.4f" %(position)
    return position

gpgga_info = "$GPGGA,"
ser = serial.Serial ('/dev/ttyACM0', 9600, timeout=0.5)              #Open port with baud rate
GPGGA_buffer = 0
NMEA_buff = 0
lat_in_degrees = 0
long_in_degrees = 0

while True:
    try:
        while True:
            received_data = (str)(ser.readline())#read NMEA string received
            GPGGA_data_available = received_data.find(gpgga_info)   #check for NMEA GPGGA string                            
            if (GPGGA_data_available>0):
                GPGGA_buffer = received_data.split("$GPGGA,",1)[1]  #store data coming after "$GPGGA," string 
                NMEA_buff = (GPGGA_buffer.split(','))#store comma separated data in buffer
                GPS_Info()
                print("out")
     
                print("lat in degrees:", lat_in_degrees," long in degree: ", long_in_degrees, '\n')
                mess = "Please check http://maps.google.com/?q=' + lat_in_degrees + ',' + long_in_degrees"
                client.messages.create(to="+XXXXXXXXXXXXX",
                                     from_="XXXXXXXXXXXXX",
                                      body=mess)
                sleep(300)
                
    except ValueError:
        pass
    
   
