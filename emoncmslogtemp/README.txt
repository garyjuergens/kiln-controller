SETUP THE SERVICE

cp log_temp.py /tmp
chmod 775 log_temp.py
cp log_temp.sh /etc/init.d
chmod 744 /etc/init.d/log_temp.sh

setup the service:
sudo update-rc.d log_temp.sh defaults



This published to a "TST" queue in MQTT 


in node red, create a two box flow, mqtt INPUT , to emoncms output

The mqtt input is configured:
server: 
connection localhost , port 1883
secuirty emonpi emonpi2016 (or as changed)
Topic: tst
QoS 2
Name "tst"


The EMONCMS output:
Server:
Base url : https://emoncms.org/
api key : your api key
name: emoncms
NODE: the number of the input created below "25"
Name: Emoncms


Login, look at your inputs

Create an input on emoncms.org website:
https://emoncms.org//input/post.json?&apikey=YOURAPIKEY

Find the input number.

create a feed on emoncms.org from the input above:
select the input just created
click the spanner/wrench next to it, 
log to feed will be selected, set desired name, ADD

