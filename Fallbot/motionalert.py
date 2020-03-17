import os
import glob
import argparse
import logging
import datetime
from time import sleep

from twilio.rest import Client
#from twilio.exceptions import TwilioException

from boto.s3.connection import S3Connection
from boto.s3.key import Key

class MotionAlert(object):
    def __init__(self, account_sid=None, auth_token=None,
                 aws_access_key_id=None, aws_secret_key=None, s3_bucket=None,
                 twilio_number=None, receiving_number=None,
                 motion_target_dir=None, timestamp=None, body=None,
                 num_of_images=None):
        """
        A class that sends Twilio MMS alerts based on input from Motion, a
        software movement detector for Linux.

        Attributes:
            account_sid: Your Twilio Account Sid.
            auth_token: Your Twilio Auth Token.
            aws_access_key_id: Your AWS Access Key Id.
            aws_secret_key: Your AWS Secret Key.
            s3_bucket: The name of the AWS S3 bucket to use for uploading
                       images.
            twilio_number: The Twilio number from which alerts will be sent.
            receiving_number: The number you wish to receive alerts.
            motion_target_dir: Path to where Motion is storing its images.
            timestamp: Current timestamp, generated by the Motion event.
            body: Text of the message you want to send.
            num_of_images: An integer of the number of images you wish 
                           to send in your alert.
            twilio_client: A Twilio client object initialized with your
                           credentials.
            s3_connection: A S3 connection object initialized with your
                           credentials.
        """
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_key = aws_secret_key
        self.s3_bucket = s3_bucket
        self.twilio_number = twilio_number
        self.receiving_number = receiving_number
        self.motion_target_dir = motion_target_dir
        self.timestamp = timestamp
        self.body = body
        self.num_of_images = int(num_of_images)

        # Initialize our two API clients with our credentials.
        self.twilio_client = Client(self.account_sid,
                                              self.auth_token)
        try:
            self.s3_connection = S3Connection(self.aws_access_key_id,
                                         self.aws_secret_key)
        except Exception as e:
            raise MotionAlertError("Error connecting to S3: {0}".format(e))

    def send(self):
        """Send an alert via Twilio MMS from Motion.
        Returns:
            message: a Twilio Message object from a successful request.
        """
        # Let the user know we're working on sending an alert to a phone number.
        logging.info("Sending alert to {0}...".format(self.receiving_number))

        # Get the specified series of images from the camera.
        image_paths = []
        for i in range(self.num_of_images):
            image_file_path = \
                self.get_latest_image_from_directory(self.motion_target_dir)
            # Wait 2 seconds to get next image
            image_paths.append(image_file_path)
            if i != self.num_of_images:
                sleep(1)

        # Try to upload that image to S3.
        s3_keys = []
        if image_paths:
            for image_path in reversed(image_paths):
                s3_key = self.upload_image_to_s3(image_path,
                                                 self.s3_bucket)
                s3_keys.append(s3_key)
        else:
            raise MotionAlertError("Could not retrieve an image to send.")

        # Try to send the image uploaded to S3 via Twilio MMS.
        if s3_keys:
            media_urls = []
            for s3_key in s3_keys:
                media_url = "https://s3.amazonaws.com/{0}" \
                            "/{1}".format(self.s3_bucket,
                                          s3_key.key)
                media_urls.append(media_url)
            message = self.send_alert_to_phone_number(from_=self.twilio_number,
                                                      to=self.receiving_number,
                                                      body=self.body,
                                                      media_url=media_urls)
            return message
        else:
            raise MotionAlertError("Could not send image to "
                                   "{0}.".format(self.receiving_number))

        # Confirm to user we are complete sending the alert.
        if message:
            logging.info("Alert sent to {0}.".format(self.receiving_number))
        else:
            logging.error("An unknown error occured sending to "
                          "{0}.".format(self.receiving_number))

    def get_latest_image_from_directory(self, motion_target_dir):
        """Retrieves the most recently created .jpg file from target directory.

        Arguments:
            motion_target_dir: The directory in which Motion stores its images.

        Returns:
            String with path to most recently created image.
        """
        try:
            # Use a glob generator to find the newest image
            return max(glob.iglob('{0}/*.jpg'.format(motion_target_dir)),
                       key=os.path.getctime)
        except ValueError as e:
            # Raise an error if we did not find any images
            raise MotionAlertError("Could not find any images in motion "
                                   "target directory: "
                                   "{0}".format(motion_target_dir))
        except OSError as e:
            # Raise an error if we cannot access the directory.
            raise MotionAlertError("Could not find the motion target dir: "
                                   "{0}".format(e))

    def upload_image_to_s3(self, image_file_path, bucket_name):
        global bucket
        """Uploads images to Amazon's S3 service.

        Arguments:
            image_file_path: Path to image to upload on local machine.
            bucket_name: Name of the S3 bucket where image should be uploaded.
            key_name: Name of the key for the file on S3 (usually the
                      timestamp).
        """
        try:
            # Attempt to get the S3 bucket with our S3 connection.
            bucket = self.s3_connection.get_bucket(bucket_name)
        except Exception as e:
            # Error out if we're unable to locate the S3 bucket.
            print("Error connecting to S3 bucket: "
                  "{0}".format(e))
            #raise MotionAlertError("Error connecting to S3 bucket: "
             #                      "{0}".format(e))

        try:
            # Create a new key using image_file_path as the key
            key = Key(bucket)
            key.key = image_file_path 
            key.set_contents_from_filename(image_file_path)
            return key
        except Exception as e:
            # Error out if we're unable to upload the image.
            print("Error uploading file to S3: {0}".format(e))
            #raise MotionAlertError("Error uploading file to S3: {0}".format(e))

    def send_alert_to_phone_number(self, from_=None, to=None, body=None,
                                   media_url=None):
        """Sends a MMS using Twilio.

        Keyword Arguments:
            from_: The Twilio number from which the alert will be sent.
            to: The phone number that will receive the alert.
            body: Text for the alert.
            media_url: The fully qualified path to the image for the alert
                       available on the Internet.
        """
        #try:
            # Send the alert using the Twilio Messages resource.
        self.twilio_client.messages.create(from_=from_, to=to,
                                               body=body, media_url=media_url)
        #except TwilioException as e:
         #   # Error out if the request fails.
          #  raise MotionAlertError("Error sending MMS with Twilio: "
           #                        "{0}".format(e))

class MotionAlertError(Exception):
    def __init__(self, message):
        """
        An Exception that handles output of errors to the user.

        Arguments:
            message: The message you want to display to the user for the
            exception.
        """
        logging.error("ERROR: {0}".format(message))
        logging.error("Try running with --help for more information.")

# Create a command line interface for our class.
parser = argparse.ArgumentParser(description="Motion Alert - send MMS alerts "
                                             "from Motion events.",
                                 epilog="Powered by Twilio!")

parser.add_argument("-S", "--account_sid", default='ACd2735ad3d932ba03915d33da219a969f', required=False,
                    help="Use a specific Twilio Account Sid.")
parser.add_argument("-K", "--auth_token", default='4edbc4f1b91c28075f5a104d7bd57de7', required=False,
                    help="Use a specific Twilio Auth Token.")
parser.add_argument("-#", "--twilio_number", default='+12017333298', required=False,
                    help="Use a specific Twilio phone number "
                         "(e.g. +15556667777).")
parser.add_argument("-s", "--aws_access_key_id", default='AKIAI3QMQLDCEB26ZWWQ', required=False,
                    help="Use a specific Amazon Web Services Access Key Id.")
parser.add_argument("-k", "--aws_secret_key", default='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', required=False,
                    help="Use a specific Amazon Web Services Secret Key.")
parser.add_argument("-b", "--s3_bucket", default='fallbot', required=False,
                    help="Use a specific Amazon Web Services S3 Bucket.")
parser.add_argument("-t", "--receiving_number", default='+447828883886', required=False,
                    help="Number to receive the alerts.")
parser.add_argument("-T", "--timestamp", default=datetime.datetime.now(), required=False,
                    help="Timestamp of event passed from Motion.")
parser.add_argument("-B", "--body", default='Auntie Pat has been found.', required=False,
                    help="Body of message you wish to send.")
parser.add_argument("-d", "--motion_target_dir", default='/home/pi/Desktop/Fallbot/images', required=False,
                    help="Directory where Motion is storing images from "
                         "motion capture.")
parser.add_argument("-i", "--num_of_images", default=1, required=False,
                    help="Number of image to send in an alert.")

# Configure our logging for the CLI output.
logging.basicConfig(level=logging.INFO, format="%(message)s")

# Present that CLI to the user when the Python file is executed.
if __name__ == "__main__":
    args = parser.parse_args()
    motion_alert = MotionAlert(**vars(args))
    motion_alert.send()