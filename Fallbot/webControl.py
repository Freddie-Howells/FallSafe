# Importing the necessary packages
from imports.utils import Conf
from imutils.video import VideoStream
from imutils import face_utils
import dlib
from twilio.rest import Client
import os
import threading
import imutils
import cv2
from time import sleep
import imports.sensor as sensor
import imports.roboMove2 as fallbot
from flask import Flask, render_template, Response

#startup motion
fallbot.startup()

#set twilio keys
account_sid = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
auth_token = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
client = Client(account_sid, auth_token)

# initialize the output frame
outputFrame = None
lock = threading.Lock()

# initialize a flask object
app = Flask(__name__)

# initialize the video stream and allow the camera sensor to warmup
vs = VideoStream(src=0).start()
sleep(2.0)

@app.route("/")
def index(): # Set the webpage template
    return render_template('index2.html')

def sense(): # Checking if an object is infront of it and stopping if one is detected
    while True:
        sensorM = sensor.sense(18,17,"Front")
        if sensorM <= 25:
            print("ahhhhh")
            fallbot.stop()

def detect_motion():
    global vs, outputFrame, lock
    global text

    # loop over frames from the video stream
    while True:
        # grab the frame from the threaded video file stream, resize, and convert to grayscale
        frame = vs.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        outputFrame = frame.copy()

def generate():
    # grab global references to the output frame and lock variables
    global outputFrame, lock

    # loop over frames from the output stream
    while True:
        # wait until the lock is acquired
        with lock:
            # check if the output frame is available, otherwise skip
            # the iteration of the loop
            if outputFrame is None:
                continue

            # encode the frame in JPEG format
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)

            # ensure the frame was successfully encoded
            if not flag:
                continue

        # yield the output frame in the byte format
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + 
            bytearray(encodedImage) + b'\r\n')
        
@app.route("/<deviceName>")
def action(deviceName): # functions for webpage buttons
    import os
    if deviceName == "Exit":
        os.system('sh /home/pi/Desktop/cv3.sh')
    if deviceName == 'Backwards':
        fallbot.backward()
    if deviceName == 'Forwards':
        fallbot.forward()
    if deviceName == 'Left':
        fallbot.left()
    if deviceName == 'Right':
        fallbot.right()
    if deviceName == 'Stop':
        fallbot.stop()
    
    return render_template('index2.html')

@app.route("/video_feed")
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    return Response(generate(),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

# check to see if this is the main thread of execution
if __name__ == '__main__':
    conf = Conf("config/config.json")
    th = threading.Thread(target=sense)
    t = threading.Thread(target=detect_motion)
    t.daemon = True
    th.start()
    t.start()

    # start the flask app
    app.run(host='0.0.0.0', port=7000, debug=False,
            threaded=True, use_reloader=False)
# release the video stream pointer
vs.stop()

