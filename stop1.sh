#!/bin/bash

kill $(ps aux | grep '[p]ython personDetection.py'| awk '{print $2}')