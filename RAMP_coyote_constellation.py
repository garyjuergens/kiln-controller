import os
import sys
import config
import glob
import time
import RPi.GPIO as GPIO
import logging
import datetime
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders

# SET THE CONFIG desiredmax  TO 1150


## TODO
# email when coolenough to open
# check if python RAMP.py is out there, don't start if it is
# run DRY.py then RAMP.py?
# remove config file?
# set back to read only filesystems
# clone image, make disk bitter
# make program a reable input array / file
#   or fix the ontime issue if something else is running





## LOGFILE FORMAT
#MINUTES,CURRENT_TEMP_TOP, CURRENT_TEMP_BOTTOM, DESIRED TEMP, START TEMP, MAX TOP TEMP, MAX BOTTOM TEMP, RELAY ON TIME

GPIO.setwarnings(False)

logger = logging.getLogger('RAMP.py')
filename = "log_temps_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
config.logfilename = filename
filenamewithpath = "/home/pi/kiln/log/log_temps_" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log"
scriptname = os.path.basename(sys.argv[0])
scriptnamewithpath = "/home/pi/kiln/" + os.path.basename(sys.argv[0])
starttime = datetime.datetime.now()
global runtime
runtime = starttime - starttime
hdlr = logging.FileHandler('/home/pi/kiln/log/' + filename )
formatter = logging.Formatter("%(message)s")
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

GPIO.setmode(GPIO.BCM)
# GPIO 20 = RELAYS ON, RED LED on
# GPIO 26 = Green LED on
GPIO.setup(20, GPIO.OUT)
GPIO.setup(26, GPIO.OUT)
GPIO.output(26,1)
os.system('modprobe w1-gpio')
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

def hold(holdhere,top_tempc):
        print "  HOLD CHECK config.holdc: ", config.holdc, " tempC: ", top_tempc
	state20 = GPIO.input(20)
	print " STATE OF PIN 20: " + str(state20)
	global ontime
	global runtime
	global offtime
        # TOO COLD
        if top_tempc <= config.holdc - 1:
		# ALREADY ON
		if (int(state20) == 1):
			print " KILN already on"
        		print "  TOTAL ELECTRICTY ON TIME, prior to this cycle: ", runtime
 		else:
                	print " TOO COLD AND PRESENTLY OFF: top_tempc <= config.holdc -1: ", top_tempc, " <= ", config.holdc-1
                	GPIO.output(20,1)
			ontime = datetime.datetime.now()
                	print " TURNED IT ON AT: ", ontime
        		print "  TOTAL ELECTRICTY ON TIME, prior to this cycle: ", runtime
	# TOO HOT
        else:
		if (int(state20) == 1):
                	print "  TO HOT AND PRESENTLY ON, TURN IT OFF, KILN IS: ", top_tempc
                	GPIO.output(20,0)
			offtime = datetime.datetime.now()
                	print " Turned it off at: ", offtime
			runtime = runtime + (offtime - ontime)
        		print "  TOTAL ELECTRICITY ON TIME, runtime: ", runtime
		else:		
			print " ALREADY OFF"
                	GPIO.output(20,0)
        		print "  TOTAL ELECTRICITY ON TIME: ", runtime

def main():
        print "######################################"
	global bottom_tempc
	global top_tempc
        device=top_temp
        top_tempc = read_temp(device)
        top_tempf = top_tempc * 9.0 / 5.0 + 32.0
        device=bottom_temp
        bottom_tempc=read_temp(device)
        bottom_tempf = bottom_tempc * 9.0 / 5.0 + 32.0
        timenow = datetime.datetime.now()
        time_difference = timenow - starttime
        print "Time since start: ", time_difference
        time_on_in_minutes = int(((timenow - starttime).total_seconds())/60)
        time_on = time_on_in_minutes
        print "  TOP Celcius degrees: ", top_tempc, " Farenheit: ",top_tempf
        print "  BOTTOM Celcius degrees: ", bottom_tempc, " Farenheit: ",bottom_tempf
        print "  Time on in minutes: ", time_on
        #SAVE THE STARTING TEMP
        if config.starttemp == 1234567.999:
                config.starttemp = top_tempc
		
	# email that kiln has started, notify of desired max
	if config.startmailsent == 0:
		config.startmailsent = 1 
		toaddrs = config.recipients
		msg = MIMEMultipart()
		msg['From'] = config.fromaddr
		msg['Subject'] = "KILN MAIL, started firing."
		body = "\n".join([
       		"Kiln just started..",
       		" "
       		"...starting temperature: %s\xb0C"%config.starttemp,
       		"...desired maximum temperature: %s\xb0C"%config.desiredmax,
       		" ",
       		" ",
       		"scriptfile attached. ",
       		" ",
       		" ",
       		" " ])
		msg.attach(MIMEText(body, 'plain'))
		attachment = open(scriptnamewithpath, "rb")

		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % scriptname)
		msg.attach(part)

		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(config.fromaddr, config.gmailpassword)
		text = msg.as_string()
		server.sendmail(config.fromaddr, toaddrs, text)
		server.quit()
	

        #SAVE THE MAX TEMP
        if config.maxtoptemp < top_tempc:
                config.maxtoptemp = top_tempc
        if config.maxbottomtemp < bottom_tempc:
                config.maxbottomtemp = bottom_tempc

        # SAVE THE TIME THE MAX IS REACHED
        if top_tempc > config.desiredmax and config.timemaxreached is None:
                config.timemaxreached = datetime.datetime.now()



        print "  Starting temp in Celcius: ", config.starttemp
        print "  MAX measured temp in Celcius: ", config.maxtoptemp
        if config.timemaxreached is not None:
                print "  Time max reached: ", config.timemaxreached
                timenow2 = datetime.datetime.now()
                time_diff = timenow2 - config.timemaxreached
                print "Time since max: ", time_diff
                config.minutessincemax = int(((timenow2-config.timemaxreached).total_seconds())/60)


        # LOG ONLY EVERY MINUTE
        #if time_on_in_minutes != config.lastloggedminute:
        config.lastloggedminute = time_on_in_minutes
        logthis = str(time_on) + "," + str(time_difference) + "," + str(top_tempc) + ","+ str(bottom_tempc) + "," +str(config.holdc) + "," + str(config.starttemp) + "," + str(config.maxtoptemp) + ","+ str(config.maxbottomtemp) + "," + str(runtime)
        logger.info( logthis )

        # FIRE FIRE FIRE!
        if time_on < 30:
                config.holdc = 40
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 30 and time_on <60 and config.maxtoptemp < config.desiredmax:
                config.holdc = 50
                holdhere = config.holdc
               	hold(holdhere,top_tempc)
        elif time_on >= 60 and time_on <90 and config.maxtoptemp < config.desiredmax:
                config.holdc = 80 
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 90 and time_on <120 and config.maxtoptemp < config.desiredmax:
                config.holdc = 100
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 120 and time_on <126 and config.maxtoptemp < config.desiredmax:
                config.holdc = 140
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 126 and time_on <132 and config.maxtoptemp < config.desiredmax:
                config.holdc = 170
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 132 and time_on <147 and config.maxtoptemp < config.desiredmax:
                config.holdc = 183
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 147 and time_on <162 and config.maxtoptemp < config.desiredmax:
                config.holdc = 208
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 162 and time_on <177 and config.maxtoptemp < config.desiredmax:
                config.holdc = 250
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 177 and time_on <192 and config.maxtoptemp < config.desiredmax:
                config.holdc = 293
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 192 and time_on <207 and config.maxtoptemp < config.desiredmax:
                config.holdc = 340
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 207 and time_on <222 and config.maxtoptemp < config.desiredmax:
                config.holdc = 387
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 222 and time_on <237 and config.maxtoptemp < config.desiredmax:
                config.holdc = 420
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 237 and time_on <244 and config.maxtoptemp < config.desiredmax:
                config.holdc = 450 
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 244 and time_on <252 and config.maxtoptemp < config.desiredmax:
                config.holdc = 481
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 252 and time_on <267 and config.maxtoptemp < config.desiredmax:
                config.holdc = 530
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 267 and time_on <275 and config.maxtoptemp < config.desiredmax:
                config.holdc = 550
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 275 and time_on <282 and config.maxtoptemp < config.desiredmax:
                config.holdc = 575
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 282 and time_on <298 and config.maxtoptemp < config.desiredmax:
                config.holdc = 625
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 298 and time_on <312 and config.maxtoptemp < config.desiredmax:
                config.holdc = 669
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 312 and time_on <327 and config.maxtoptemp < config.desiredmax:
                config.holdc = 716
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 327 and time_on <342 and config.maxtoptemp < config.desiredmax:
                config.holdc = 763
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 342 and time_on <357 and config.maxtoptemp < config.desiredmax:
                config.holdc = 812
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 357 and time_on <362 and config.maxtoptemp < config.desiredmax:
                config.holdc = 830
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 362 and time_on <372 and config.maxtoptemp < config.desiredmax:
                config.holdc = 859
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 372 and time_on < 387 and config.maxtoptemp < config.desiredmax:
                config.holdc = 905
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 387 and time_on < 402 and config.maxtoptemp < config.desiredmax:
                config.holdc = 953
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 402 and time_on < 412 and config.maxtoptemp < config.desiredmax:
                config.holdc = 986
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 412 and time_on < 422 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1016
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 422 and time_on < 432 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1050
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 432 and time_on < 442 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1080
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 442 and time_on < 452 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1090
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 452 and time_on < 462 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1110
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 462 and time_on < 472 and config.maxtoptemp < config.desiredmax:
                config.holdc = 11125
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 472 and time_on < 482 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1135
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 482 and time_on < 492 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1145
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        elif time_on >= 492 and time_on < 502 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1148
                holdhere = config.holdc
                hold(holdhere,top_tempc)
	# ATTAIN MAX (1150) - coyote constellation
        elif time_on >= 502 and time_on < 802 and config.maxtoptemp < config.desiredmax:
                config.holdc = 1150
                holdhere = config.holdc
                hold(holdhere,top_tempc)
        # MAX ATTAINED, HOLD and RAMP DOWN
        elif config.minutessincemax<15 and config.maxtoptemp >= config.desiredmax:
                config.holdc = config.desiredmax
                holdhere = config.holdc
                print "Holding at max for 15 minutes: ", config.holdc
                hold(holdhere,top_tempc)
		# email that kiln has reached max temp, attach log so far
		if config.donemailsent == 0:
			config.donemailsent = 1 
			toaddrs = config.recipients
			msg = MIMEMultipart()
			msg['From'] = config.fromaddr
			msg['Subject'] = "KILN MAIL, max reached."
			body = "\n".join([
       			"Kiln just reached Maximum temperature!!!!!",
       			" "
       			"...maximum top temperature: %s\xb0C"%config.maxtoptemp,
       			"...maximum bottom temperature: %s\xb0C"%config.maxbottomtemp,
       			"...Total relay runtime: %s"%runtime,
       			"...Time maximum temp was reached: %s"%config.timemaxreached,
       			" ",
       			" ",
       			"Logfile attached. ",
			" ",
			"logfile format: MINUTES,CURRENT_TEMP_TOP, CURRENT_TEMP_BOTTOM, DESIRED TEMP, START TEMP, MAX TOP TEMP, MAX BOTTOM TEMP, RELAY ON TIME",
       			" ",
       			" ",
       			" " ])
			msg.attach(MIMEText(body, 'plain'))
			attachment = open(filenamewithpath, "rb")

			part = MIMEBase('application', 'octet-stream')
			part.set_payload((attachment).read())
			encoders.encode_base64(part)
			part.add_header('Content-Disposition', "attachment; filename= %s" % config.logfilename)
			msg.attach(part)

			server = smtplib.SMTP('smtp.gmail.com', 587)
			server.starttls()
			server.login(config.fromaddr, config.gmailpassword )
			text = msg.as_string()
			server.sendmail(config.fromaddr, toaddrs, text)
			server.quit()
			
        elif config.minutessincemax>=15 and config.minutessincemax < 36 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1124
                holdhere = config.holdc
                print "Holding at 1124 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=36 and config.minutessincemax < 46 and config.maxtoptemp >= config.desiredmax:
                config.holdc =  1114
                holdhere = config.holdc
                print "Holding at 1114 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=46 and config.minutessincemax < 56 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1104
                holdhere = config.holdc
                print "Holding at 1104 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=56 and config.minutessincemax < 66 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1094
                holdhere = config.holdc
                print "Holding at 1094 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=66 and config.minutessincemax < 76 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1084
                holdhere = config.holdc
                print "Holding at 1084 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=76 and config.minutessincemax < 86 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1074
                holdhere = config.holdc
                print "Holding at 1074 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=86 and config.minutessincemax < 96 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1064
                holdhere = config.holdc
                print "Holding at 1064 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=96 and config.minutessincemax < 106 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1054
                holdhere = config.holdc
                print "Holding at 1054 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>= 106 and config.minutessincemax < 116  and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1044
                holdhere = config.holdc
                print "Holding at 1044 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=116 and config.minutessincemax < 126 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1034
                holdhere = config.holdc
                print "Holding at 1034 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=126 and config.minutessincemax < 136 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1024
                holdhere = config.holdc
                print "Holding at 1024 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=136 and config.minutessincemax < 146 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1014
                holdhere = config.holdc
                print "Holding at 1014 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=146 and config.minutessincemax < 156 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 1004
                holdhere = config.holdc
                print "Holding at 1004 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=156 and config.minutessincemax < 166 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 994
                holdhere = config.holdc
                print "Holding at 994 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=166 and config.minutessincemax < 176 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 984
                holdhere = config.holdc
                print "Holding at 984 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=176 and config.minutessincemax < 186 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 974
                holdhere = config.holdc
                print "Holding at 974 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=186 and config.minutessincemax < 196 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 964
                holdhere = config.holdc
                print "Holding at 964 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=196 and config.minutessincemax < 206 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 954
                holdhere = config.holdc
                print "Holding at 954 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=206 and config.minutessincemax < 216 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 944
                holdhere = config.holdc
                print "Holding at 944 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=216 and config.minutessincemax < 226 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 934
                holdhere = config.holdc
                print "Holding at 934 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=226 and config.minutessincemax < 236 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 924
                holdhere = config.holdc
                print "Holding at 924 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=236 and config.minutessincemax <246  and config.maxtoptemp >= config.desiredmax:
                config.holdc = 914
                holdhere = config.holdc
                print "Holding at 914 for 10 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=246 and config.minutessincemax < 276 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 884
                holdhere = config.holdc
                print "Holding at 884 for 30 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=276 and config.minutessincemax < 306 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 854
                holdhere = config.holdc
                print "Holding at 854 for 30 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=306 and config.minutessincemax < 336 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 824
                holdhere = config.holdc
                print "Holding at 824 for 30 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=336 and config.minutessincemax < 366 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 794
                holdhere = config.holdc
                print "Holding at 794 for 30 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        elif config.minutessincemax>=366 and config.minutessincemax < 396 and config.maxtoptemp >= config.desiredmax:
                config.holdc = 760
                holdhere = config.holdc
                print "Holding at 760 for 30 minutes: ", config.holdc
                hold(holdhere,top_tempc)
        else:
                config.holdc = 1
                holdhere = config.holdc
                print "TURNED OFF, Holding at: ", config.holdc
                hold(holdhere,top_tempc)
		GPIO.output(26,0)

		#email that the kiln is off
		fromaddr = config.fromaddr
		recipients = config.recipients
		toaddrs = config.recipients
		msg = MIMEMultipart()
		msg['From'] = config.fromaddr
		msg['Subject'] = "KILN MAIL, kiln is off."

		body = "\n".join([
       		"Maximum temperature reached, KILN IS OFF and cooling now, just a few more hours till Christmas!",
       		" "
       		"...maximum top temperature: %s\xb0C"%config.maxtoptemp,
       		"...maximum bottom temperature: %s\xb0C"%config.maxbottomtemp,
       		"...Total relay runtime: %s"%runtime,
       		"...Time maximum temp was reached: %s"%config.timemaxreached,
       		" ",
       		" ",
       		"Logfile and scriptfile attached. ",
		" ",
		"logfile format: MINUTES,CURRENT_TEMP_TOP, CURRENT_TEMP_BOTTOM, DESIRED TEMP, START TEMP, MAX TOP TEMP, MAX BOTTOM TEMP, RELAY ON TIME",
       		" ",
       		" ",
       		" " ])
 
		msg.attach(MIMEText(body, 'plain'))
		attachment = open(filenamewithpath, "rb")

		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % config.logfilename)
		msg.attach(part)

		attachment = open(scriptnamewithpath, "rb")
		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % scriptname)
		msg.attach(part)

 
		server = smtplib.SMTP('smtp.gmail.com', 587)
		server.starttls()
		server.login(config.fromaddr, config.gmailpassword )
		text = msg.as_string()
		server.sendmail(config.fromaddr, toaddrs, text)
		server.quit()
		quit()


while True:
        main()
	print "BOTTOM TEMP: ", bottom_tempc
	print "TOP TEMP:", top_tempc
        time.sleep(2)

	

