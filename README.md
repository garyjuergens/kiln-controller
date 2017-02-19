# kiln-controller
Raspberry Pi python script to read max31850s and control SSR's to fire an electric kiln.

Running on US, 240vAC, three wire single phase aka split phase.

Raspberry Pi Kiln Controller, running on an emonpi raspberry pi. Two Maximum Integrated Circuits 38150s are connected to the GPIO header, as well as two SSRs', and threa "software runnning" LED.

The Software running LED, green, is on GPIO 25.
The relays are connected to GPIO 20.
Two other LED's are installed, RED, connected to the relay power, showing heating on.
And a Blue LED connected to the 5v power of the Pi, indicating power is on.


USAGE:
update config.py desiredmax, to set desired max temperature,  outgoing email user, gmail pasword, etc

Run with:
sudo python RAMP.py

or via nohup:
nohup sudo python -u RAMP.py > ./log/test.log &

Inspired by:
http://mdpub.com/kilncont/index.html
and
https://www.raspberrypi.org/blog/wifi-controlled-pottery-kiln/

MOVE one-wire thermocouple driver default gpio port, as its not compatible with emonpi:
move one-wire default gpis
https://www.raspberrypi.org/forums/viewtopic.php?p=518859#p518859
/boot/config.txt
dtoverlay=w1-gpio,gpiopin=<GPIO NUMBER>


KILN CONTROLLER SOFTWARE FEATURES:
1) email start/stop/off/cool 
2) Create csv logfile with gathered data for plotting
3) control kiln to max temp, including RAMP and HOLD, ascent, and descent

OTHER SOFWARE IN PLAY:
emonpi, running its software sweet: Node-red, mqtt, emoncms.org, etc
Created a pi service to always log kiln temps measured (kiln on or off) to emoncms
 that is in emoncmslogtemp directory as log_temp.sh and log_temp.py


OVERALL PROJECT GOALS
pi to control: 
*emonpi
*monitor house temp/humidity
*monitor outdoor house/humidity
*kiln
*garage security camera


NOTES:
you have to enable "less secure apps" in your gmail account for this to email:
https://support.google.com/accounts/answer/6010255?hl=en

TODO:
make program a reable input array / file of temp's-Times at temps- Ramps
  or fix the ontime issue if something else is running
Make temp at time computed.. and ramp temp more soothly..
add pi display
add pi camera
add photo blog of ceramics going into the kiln
add read of emonpi for adding to logfile 
email when coolenough to open
check if python RAMP.py is out there, don't start if it is
run DRY.py then RAMP.py?
remove config file?
set back to read only filesystems

PARTS:
kiln, craigslist, paragon A-88B, 25.9 Amps, 6226 Watts, max temp 2300

emonpi
https://shop.openenergymonitor.com/emonpi-3/
Ordered without the case and with the additional 100A Current Sensor, with teh US plug, 

Two EMONTh's.. 
one inside the house, with additional sensor purchased (measure house temp, high and low in the room)
one outside
https://shop.openenergymonitor.com/emonth-v2-temperature-humidity-node/

Reliable Power Supply : Apple ipad 12w power block
http://www.apple.com/us-hed/shop/product/MD836LL/A/apple-12w-usb-power-adapter?fnode=91


maximum Integrated 38150, thermocouple amplifier, A/D convertedr
https://www.amazon.com/gp/product/B01BU72CZ2/ref=oh_aui_detailpage_o07_s00?ie=UTF8&psc=1

Solid State Relays's (SSR), digikey:
Digikey Part Number: CC1082-ND
Crydom Co
Relay SSR 50A 240AC
https://www.digikey.com/product-detail/en/crydom-co/D2450-10/CC1082-ND/221775

Ethernet passthrough connector
Digi-key part number, APC1766-ND
Amphenol PCD
https://www.digikey.com/product-detail/en/amphenol-pcd/RCP-5SPFFH-TCU7001/APC1766-ND/5253168


Heat Sink
ebay
Aluminum no name 8-1/4x 4-1/8 x 1-3/4
Sold by southbendindustrial

heat sink compound
https://www.amazon.com/gp/product/B0044NI2M2/ref=oh_aui_detailpage_o01_s00?ie=UTF8&psc=1


Enclossure 
BUD Industried NF-6614
13-57/64 x 15 49/64 x 6 51/64
https://www.amazon.com/gp/product/B005T5JK2U/ref=oh_aui_detailpage_o01_s01?ie=UTF8&psc=1

DPST Switch, from main to outlet to power the pi, other pole may be used on other main in the future:
https://www.amazon.com/gp/product/B019GTQB1C/ref=oh_aui_detailpage_o04_s00?ie=UTF8&psc=1


blue LED (connected to the pi, 5v):
https://www.amazon.com/gp/product/B00FO3B2CS/ref=oh_aui_detailpage_o05_s00?ie=UTF8&psc=1

green LED (connected to the GPIO 26), Software running indicator
https://www.amazon.com/gp/product/B00FO3B232/ref=oh_aui_detailpage_o05_s01?ie=UTF8&psc=1

red LED (indicating heater on)
https://www.amazon.com/gp/product/B013U3EEPU/ref=oh_aui_detailpage_o03_s00?ie=UTF8&psc=1


Pi SD card:
https://www.amazon.com/gp/product/B01HU3Q6F2/ref=oh_aui_detailpage_o00_s00?ie=UTF8&psc=1



switch to toggle power override/software control 
https://www.amazon.com/gp/product/B00A151RJM/ref=oh_aui_detailpage_o09_s00?ie=UTF8&psc=1

