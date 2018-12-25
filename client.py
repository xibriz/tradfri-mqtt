#!/usr/bin/python
# coding: utf-8

import os
main_base = os.path.dirname(__file__)
config_file = os.path.join(main_base, "config", "prod.cfg")

import paho.mqtt.client as mqtt
import re
import threading
from src import ikea

ikea = ikea.Ikea(config_file=config_file)

base = u'^{}$'

rg_bulb_set = re.compile(base.format(ikea.bulb_sub.format(name='(.*?)').replace('/','\\/')), re.U)
rg_bulb_status = re.compile(base.format(ikea.bulb_status.format(name='(.*?)').replace('/','\\/')), re.U)

status_delay = 10.0

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	#print("Connected with result code "+str(rc))

	# Subscribing in on_connect() means that if we lose the connection and
	# reconnect then subscriptions will be renewed.
	client.subscribe("ikea/#")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
	#print(msg.topic+" "+str(msg.payload))
	m = rg_bulb_set.search(msg.topic)
	if m:
		ikea.set_bulb_dim(m.group(1), msg.payload)

	m = rg_bulb_status.search(msg.topic)
	if m:
		ikea.get_bulb_dim(m.group(1))



client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(ikea.mqtt_ip, ikea.mqtt_port, 60)

# Publish the status of all devices
ikea.bulb()

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()

