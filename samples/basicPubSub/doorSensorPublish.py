#fix for the imports
import os
import sys
import AWSIoTPythonSDK
sys.path.insert(0, os.path.dirname(AWSIoTPythonSDK.__file__))
# Now the import statement should work
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient

#old imports
#from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
#import sys

import logging
import time
import getopt
import datetime
import RPi.GPIO as io # import the GPIO library we just installed but call it "io"


# Custom MQTT message callback
def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

# Usage
usageInfo = """Usage:
Use certificate based mutual authentication:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -c <certFilePath> -k <privateKeyFilePath>
Use MQTT over WebSocket:
python basicPubSub.py -e <endpoint> -r <rootCAFilePath> -w
Type "python basicPubSub.py -h" for available options.
"""
# Help info
helpInfo = """-e, --endpoint
	Your AWS IoT custom endpoint
-r, --rootCA
	Root CA file path
-c, --cert
	Certificate file path
-k, --key
	Private key file path
-w, --websocket
	Use MQTT over WebSocket
-h, --help
	Help information
"""

# Read in command-line parameters
useWebsocket = False
host = "" # your device endpoint 
rootCAPath = "" # your root CA path
certificatePath = "" # your certificate path
privateKeyPath = "" # your private key path
try:
	opts, args = getopt.getopt(sys.argv[1:], "hwe:k:c:r:", ["help", "endpoint=", "key=","cert=","rootCA=", "websocket"])
	if len(opts) == 0:
	raise getopt.GetoptError("No input parameters!")
	for opt, arg in opts:
	if opt in ("-h", "--help"):
	print(helpInfo)
	exit(0)
	if opt in ("-e", "--endpoint"):
	host = arg
	if opt in ("-r", "--rootCA"):
	rootCAPath = arg
	if opt in ("-c", "--cert"):
	certificatePath = arg
	if opt in ("-k", "--key"):
	privateKeyPath = arg
	if opt in ("-w", "--websocket"):
	useWebsocket = True
except getopt.GetoptError:
	print(usageInfo)
	exit(1)

# Missing configuration notification
missingConfiguration = False
if not host:
	print("Missing '-e' or '--endpoint'")
	missingConfiguration = True
if not rootCAPath:
	print("Missing '-r' or '--rootCA'")
	missingConfiguration = True
if not useWebsocket:
	if not certificatePath:
	print("Missing '-c' or '--cert'")
	missingConfiguration = True
	if not privateKeyPath:
	print("Missing '-k' or '--key'")
	missingConfiguration = True
if missingConfiguration:
	exit(2)

# Configure logging
logger = None
if sys.version_info[0] == 3:
	logger = logging.getLogger("core")  # Python 3
else:
	logger = logging.getLogger("AWSIoTPythonSDK.core")  # Python 2
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

# Init AWSIoTMQTTClient
myAWSIoTMQTTClient = None
if useWebsocket:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub", useWebsocket=True)
	myAWSIoTMQTTClient.configureEndpoint(host, 443)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath)
else:
	myAWSIoTMQTTClient = AWSIoTMQTTClient("basicPubSub")
	myAWSIoTMQTTClient.configureEndpoint(host, 8883)
	myAWSIoTMQTTClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

# AWSIoTMQTTClient connection configuration
myAWSIoTMQTTClient.configureAutoReconnectBackoffTime(1, 32, 20)
myAWSIoTMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
myAWSIoTMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
myAWSIoTMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
myAWSIoTMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
myAWSIoTMQTTClient.connect()
#myAWSIoTMQTTClient.subscribe("sdk/test/Python", 1, customCallback)
#myAWSIoTMQTTClient.subscribe("iotbutton/+",1, customCallback)
#time.sleep(2)

# GPIO mode set to BCM, will take GPIO number
io.setmode(io.BCM) 
 
# The GPIO pin number you are using
door_pin = 23 

# The built-in pull-up resistor
io.setup(door_pin, io.IN, pull_up_down=io.PUD_UP)  # activate input with PullUp
 

# Initialize door
door = 0

# To keep track of how many loops have executed
loop_count = 0

command_str = ""

# The topic to publish to
topic = ""

# Number of seconds in between each loop
delay_s = 60
sensor_name = "fridge door"
status = ""

try:
    while True:
        # If switch is open
        if io.input(door_pin):
            loop_count += 1
            status = "open"
            timestamp = datetime.datetime.now()
            print('Door open at {:%Y-%m-%d %H:%M:%S}'.format(timestamp));
            msg = '"Device": "{:s}", "Status": "{:s}", "Time": "{}" "Loop": "{}"'.format(sensor_name, status, timestamp, loop_count)
            msg = '{'+msg+'}'
            myAWSIoTMQTTClient.publish(topic, msg, 1)
            door = 0 
            time.sleep(delay_s) 
        # If switch is closed
        if (io.input(door_pin)==False and door!=1):
            status = "closed"
            print("Door closed");
            door = 1 
except KeyboardInterrupt:
    pass
print("Exiting the loop");
myAWSIoTMQTTClient.disconnect()
print("Disconnected from AWS")