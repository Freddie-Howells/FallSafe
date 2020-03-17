#!/bin/bash

kill $(ps aux | grep '[p]ython personDetection.py'| awk '{print $2}')

lxterminal --command python /home/pi/Desktop/Fallbot/startWebControl.py







