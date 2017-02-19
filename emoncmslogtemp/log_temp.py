#!/usr/bin/env python	
import os
import time
import logging
import logging.handlers
import argparse
import sys
import paho.mqtt.client as mqtt

LOG_FILENAME="/tmp/log_temp.log"
LOG_LEVEL = logging.INFO # or DEBUG WARNING

# Define and parse command line arguments
parser = argparse.ArgumentParser(description="My simple Python log_temp service")
parser.add_argument("-l", "--log", help="file to write log to (default '" + LOG_FILENAME + "')")

# If the log file is specified on the command line then override the default
args = parser.parse_args()
if args.log:
        LOG_FILENAME = args.log



# Configure logging to log to a file, making a new file at midnight and keeping the last 3 day's data
# Give the logger a unique name (good practice)
logger = logging.getLogger(__name__)
# Set the log level to LOG_LEVEL
logger.setLevel(LOG_LEVEL)
# Make a handler that writes to a file, making a new file at midnight and keeping 3 backups
handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME, when="midnight", backupCount=3)
# Format each log message like this
formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
# Attach the formatter to the handler
handler.setFormatter(formatter)
# Attach the handler to the logger
logger.addHandler(handler)

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
        def __init__(self, logger, level):
                """Needs a logger and a logger level."""
                self.logger = logger
                self.level = level

        def write(self, message):
                # Only log if there is a message (not just a new line)
                if message.rstrip() != "":
                        self.logger.log(self.level, message.rstrip())

# Replace stdout with logging to file at INFO level
sys.stdout = MyLogger(logger, logging.INFO)
# Replace stderr with logging to file at ERROR level
sys.stderr = MyLogger(logger, logging.ERROR)


os.system('modprobe w1-therm')
top_temp = '/sys/bus/w1/devices/3b-2cd8065da3dc/w1_slave'
bottom_temp = '/sys/bus/w1/devices/3b-6cd8065da97b/w1_slave'

def read_temp_raw(device):
        f = open(device, 'r')
        lines = f.readlines()
        f.close()
        return lines

def read_temp(device):
        lines = read_temp_raw(device)
        while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw()
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 1000.0
                return temp_c

def main():
	global bottom_tempc
	global top_tempc
        device=top_temp
        top_tempc = read_temp(device)
        #top_tempf = top_tempc * 9.0 / 5.0 + 32.0
        device=bottom_temp
        bottom_tempc=read_temp(device)
        #bottom_tempf = bottom_tempc * 9.0 / 5.0 + 32.0


while True:
        main()
 	top_bot = str(top_tempc)  + "," + str(bottom_tempc)
	
	# PUBLISH TO MQTT
        mqttc = mqtt.Client("temp")
        mqttc.username_pw_set("emonpi","emonpinewpassword")
        #mqttc.connect("IP ADDRESS OF THE PI", PORT OF NO, 60)
        mqttc.connect("10.0.1.15", 1883, 60)
        #mqttc.loop_start()
        mqttc.publish("tst",   str(top_bot) )
	logger.info("Sending TOP and BOTTOM Temps to emoncms: " + str(top_bot))
        time.sleep(20)

	

