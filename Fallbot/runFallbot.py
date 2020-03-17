from socket import socket, gethostbyname, AF_INET, SOCK_DGRAM
import os

PORT_NUMBER = 5000
SIZE = 1024
hostName = gethostbyname( '0.0.0.0' )
mySocket = socket( AF_INET, SOCK_DGRAM )
mySocket.bind( (hostName, PORT_NUMBER) )

print ("Test server listening on port {0}\n".format(PORT_NUMBER))
while True:
    print("Ready")
    (data,addr) = mySocket.recvfrom(SIZE) # Waiting until it recives a message on the right port
    data = data.decode('utf-8') # Decoding the message
    print(data)
    if data == "Activate": # Checking if the message was the predetermined one
        os.system('sh /home/pi/Desktop/start1.sh')
