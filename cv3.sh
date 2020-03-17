#!/bin/bash


kill $(ps aux | grep '[p]ython webControl.py' | awk '{print $2}')