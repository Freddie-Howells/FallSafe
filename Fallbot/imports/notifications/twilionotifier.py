# import the necessary packages
from twilio.rest import Client
from imutils.io import TempFile
from threading import Thread
import boto3
import cv2

class TwilioNotifier:
    def __init__(self, conf):
        # store the configuration object
        self.conf = conf

    def send(self, image):
        # create a temporary path for the image and write it to file
        tempImage = TempFile()
        cv2.imwrite(tempImage.path, image)

        # start a thread to upload the file and send it
        t = Thread(target=self._send, args=(tempImage,))
        t.start()

    def _send(self, tempImage):
        # create a s3 client object
        s3 = boto3.client("s3",
            aws_access_key_id=self.conf["aws_access_key_id"],
            aws_secret_access_key=self.conf["aws_secret_access_key"],
        )

        # get the filename and upload the video in public read mode
        filename = tempImage.path[tempImage.path.rfind("/home/pi/Desktop/Fallbot/images/") + 1:]
        s3.upload_file(filename, self.conf["s3_bucket"], filename,
            ExtraArgs={"ACL": "public-read",
            "ContentType": "image/jpg"})

        # get the bucket location and build the url
        location = s3.get_bucket_location(
            Bucket=self.conf["s3_bucket"])["LocationConstraint"]
        url = "https://s3-{}.amazonaws.com/{}/{}".format(location,
            self.conf["s3_bucket"], filename)

        # connect to Twilio and send the file via MMS
        client = Client(self.conf["twilio_sid"],
            self.conf["twilio_auth"])
        client.messages.create(to=self.conf["twilio_to"], 
            from_=self.conf["twilio_from"], 
            body=self.conf["message_body"], media_url=url)

        # delete the temporary file
        tempImage.cleanup()