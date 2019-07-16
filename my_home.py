"""Starts a fake fan, lightbulb, garage door and a TemperatureSensor
"""
import logging
import signal
import random

from pyhap.accessory import Accessory, Bridge
from pyhap.accessory_driver import AccessoryDriver
from pyhap.const import (CATEGORY_FAN,
                         CATEGORY_LIGHTBULB,
                         CATEGORY_GARAGE_DOOR_OPENER,
                         CATEGORY_SENSOR)
from pyhap import camera


logging.basicConfig(level=logging.INFO, format="[%(module)s] %(message)s")


# Specify the audio and video configuration that your device can support
# The HAP client will choose from these when negotiating a session.
options = {
    "video": {
        "codec": {
            "profiles": [
                camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["BASELINE"],
                camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["MAIN"],
                camera.VIDEO_CODEC_PARAM_PROFILE_ID_TYPES["HIGH"]
            ],
            "levels": [
                camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE3_1'],
                camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE3_2'],
                camera.VIDEO_CODEC_PARAM_LEVEL_TYPES['TYPE4_0'],
            ],
        },
        "resolutions": [
            # Width, Height, framerate
            [320, 240, 15], # Required for Apple Watch
            [1024, 768, 30],
            [640, 480, 30],
            [640, 360, 30],
            [480, 360, 30],
            [480, 270, 30],
            [320, 240, 30],
            [320, 180, 30],
        ],
    },
    "audio": {
        "codecs": [
            {
                'type': 'OPUS',
                'samplerate': 24,
            },
            {
                'type': 'AAC-eld',
                'samplerate': 16
            }
        ],
    },
    "srtp": True,
    "address": "192.168.1.226",
}


class TemperatureSensor(Accessory):
    """Fake Temperature sensor, measuring every 3 seconds."""

    category = CATEGORY_SENSOR

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_temp = self.add_preload_service('TemperatureSensor')
        self.char_temp = serv_temp.configure_char('CurrentTemperature')

    @Accessory.run_at_interval(3)
    async def run(self):
        self.char_temp.set_value(random.randint(18, 26))


class FakeFan(Accessory):
    """Fake Fan, only logs whatever the client set."""

    category = CATEGORY_FAN

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add the fan service. Also add optional characteristics to it.
        serv_fan = self.add_preload_service(
            'Fan', chars=['RotationSpeed', 'RotationDirection'])

        self.char_rotation_speed = serv_fan.configure_char(
            'RotationSpeed', setter_callback=self.set_rotation_speed)
        self.char_rotation_direction = serv_fan.configure_char(
            'RotationDirection', setter_callback=self.set_rotation_direction)

    def set_rotation_speed(self, value):
        logging.debug("Rotation speed changed: %s", value)

    def set_rotation_direction(self, value):
        logging.debug("Rotation direction changed: %s", value)

class LightBulb(Accessory):
    """Fake lightbulb, logs what the client sets."""

    category = CATEGORY_LIGHTBULB

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        serv_light = self.add_preload_service('Lightbulb')
        self.char_on = serv_light.configure_char(
            'On', setter_callback=self.set_bulb)

    def set_bulb(self, value):
        logging.info("Bulb value: %s", value)

class GarageDoor(Accessory):
    """Fake garage door."""

    category = CATEGORY_GARAGE_DOOR_OPENER

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_preload_service('GarageDoorOpener')\
            .configure_char(
                'TargetDoorState', setter_callback=self.change_state)

    def change_state(self, value):
        logging.info("Bulb value: %s", value)
        self.get_service('GarageDoorOpener')\
            .get_characteristic('CurrentDoorState')\
            .set_value(value)

def get_bridge(driver):
    bridge = Bridge(driver, 'Bridge')

    bridge.add_accessory(LightBulb(driver, 'Lightbulb'))
    bridge.add_accessory(FakeFan(driver, 'Big Fan'))
    bridge.add_accessory(GarageDoor(driver, 'Garage'))
    bridge.add_accessory(TemperatureSensor(driver, 'Sensor'))
    bridge.add_accessory(camera.Camera(options, driver, "Camera"))

    return bridge


driver = AccessoryDriver(port=51826, persist_file='busy_home.state')
driver.add_accessory(accessory=get_bridge(driver))
signal.signal(signal.SIGTERM, driver.signal_handler)
driver.start()
