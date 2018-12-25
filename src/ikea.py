#!/usr/bin/python
# coding: utf-8

import configparser
import paho.mqtt.publish as publish

# Hack to allow relative import above top level package
import sys
import os
folder = os.path.dirname(os.path.abspath(__file__))  # noqa
sys.path.insert(0, os.path.normpath("%s/.." % folder))  # noqa

from pytradfri import Gateway
from pytradfri.api.libcoap_api import APIFactory
from pytradfri.error import PytradfriError
from pytradfri.util import load_json, save_json

import uuid
import argparse
import threading
import time

class Ikea:
    bri_max = 254.0

    def __init__(self, config_file):
        """
        args:
            logout (bool): Log out after each request or stay logged in for
                            faster requests when used in a cron job etc.
        """
        config = configparser.RawConfigParser()
        config.read(config_file)

        self.mqtt_ip = config.get('MQTT', 'ip')
        self.mqtt_port = config.getint('MQTT', 'port')

        self.bulb_pub = config.get('MQTT', 'bulb_pub')
        self.bulb_sub = config.get('MQTT', 'bulb_sub')
        self.bulb_status = config.get('MQTT', 'bulb_status')

        self.ikea_ip = config.get('IKEA', 'ip')
        self.ikea_secret = config.get('IKEA', 'secret')
        self.ikea_identity = config.get('IKEA', 'identity')
        self.ikea_key = config.get('IKEA', 'key')

        self._load_lights()

    def _load_lights(self):
        """
        Load status of all devices
        """
        api_factory = APIFactory(host=self.ikea_ip, psk_id=self.ikea_identity, psk=self.ikea_key)
        self.api = api_factory.request

        gateway = Gateway()

        devices_command = gateway.get_devices()
        devices_commands = self.api(devices_command)
        devices = self.api(devices_commands)

        lights = [dev for dev in devices if dev.has_light_control]

        self.lights = lights

    def bulb(self):
        """
        Publish the status of all bulbs
        """
        for light in self.lights:
            dim_level = 0
            if light.light_control.lights[0].state:
                dim_level = light.light_control.lights[0].dimmer
                # Convert 0 - 254 to 0 - 100
                dim_level = int(round(int(dim_level)/self.bri_max, 2)*100)
            publish.single(self.bulb_pub.format(name=light.name), dim_level, hostname=self.mqtt_ip, port=self.mqtt_port)
        return True


    def set_bulb_dim(self, name, dim_level):
        """
        args:
            name (string): name of bulb
            dim_level (boolean): Possible values:
                            0 - 100
        """
        # Convert 0-100 to 0-254
        dim_level = int((int(dim_level) / 100.0)*self.bri_max)
        #Find Bulb
        for light in self.lights:
            if name != light.name:
                continue
            dim_command = light.light_control.set_dimmer(dim_level)
            self.api(dim_command)
            return True
        return False

    def get_bulb_dim(self, name):
        """
        args:
            name (string): name of bulb
        """
        #Reload light status
        self._load_lights()
        #Find Bulb
        for light in self.lights:
            if name != light.name:
                continue
            dim_level = 0
            if light.light_control.lights[0].state:
                dim_level = light.light_control.lights[0].dimmer
                # Convert 0 - 254 to 0 - 100
                dim_level = int(round(int(dim_level)/self.bri_max, 2)*100)
            publish.single(self.bulb_pub.format(name=light.name), dim_level, hostname=self.mqtt_ip, port=self.mqtt_port)
            return True
        return False
