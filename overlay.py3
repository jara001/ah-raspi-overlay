#!/usr/bin/env python3
# overlay.py3
"""Arrowhead Compliant overlay."""

######################
# Display
######################

from board import SCL, SDA
import busio
import adafruit_ssd1305

i2c = busio.I2C(SCL, SDA)

display = adafruit_ssd1305.SSD1305_I2C(128, 32, i2c)

# Clear the display
display.fill(0)
display.show()


######################
# Arrowhead Logo / Splash
######################

from PIL import Image

arrowhead_logo = Image.open("arrowhead_logo.bmp")

logo = Image.new("1", (display.width, display.height))
logo.paste(arrowhead_logo)

display.image(logo)
xoffset = arrowhead_logo.width + 3

display.text("Arrowhead", xoffset, 0, True)
display.text("Overlay", xoffset, 8, True)
display.text("Loading...", xoffset, 24, True)
display.show()


######################
# Arrowhead Configuration
######################

from aclpy.client.client_pkcs12 import ArrowheadClient
from aclpy.interface import ArrowheadInterface
from aclpy.server import ArrowheadServer
from aclpy.service import ArrowheadService

exec(open("ahconf.py", "rb").read())
"""Expected contents:
Server = ArrowheadServer(
    address = AH_CORE_IP_ADDRESS,
)

Interface = ArrowheadInterface(
    name = NAME_OF_THE_INTERFACE,
)

Service = ArrowheadService(
    name = NAME_OF_THE_SERVICE,
)

ProvidedService = ArrowheadService(
    name = NAME_OF_THE_SERVICE,
)

Client = ArrowheadClient(
    name = NAME_OF_THE_SYSTEM,
    address = SYSTEM_IP_ADDRESS,
    port = SYSTEM_PORT,
    pubfile = PATH_TO_PUB_FILE,
    p12file = PATH_TO_P12_FILE,
    p12pass = PASS_TO_P12_FILE,
    cafile = PATH_TO_CA_FILE,
    server = Server,
    interfaces = [Interface],
)
"""


######################
# Display utilities
######################

def update_status(status):
    display.fill_rect(xoffset, 24, 128, 32, False)
    display.text(status, xoffset, 24, True)
    display.show()


######################
# GPIO Buttons
######################

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

GPIO.setup(19, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(26, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)


######################
# Menu
######################

from enum import Enum

class MenuOptions(Enum):
    FindServer = "FindServer"
    ProviderMode = "ProvideLap"
    LocalMode = "Local only"


MENU_DESCRIPTION = "Select mode:"

MENU_MOVE_LEFT = 19
MENU_MOVE_RIGHT = 26
MENU_SELECT = 21

def show_menu():
    display.fill_rect(xoffset, 16, 128, 32, False)
    display.text(MENU_DESCRIPTION, xoffset, 16, True)

    options = list(MenuOptions)
    index = 0

    update_status("< %s >" % options[0].value)

    while not GPIO.input(MENU_SELECT):
        redraw = False

        if GPIO.input(MENU_MOVE_LEFT):
            index = (index - 1) % len(options)
            redraw = True

        if GPIO.input(MENU_MOVE_RIGHT):
            index = (index + 1) % len(options)
            redraw = True

        if redraw:
            update_status("< %s >" % options[index].value)

        time.sleep(.1)

    display.fill_rect(xoffset, 16, 128, 32, False)

    return options[index]


######################
# Arrowhead Sequence
######################

import time

update_status("Obtaining ID...")

try:
    Client.obtain_id()

except Exception as e:
    print (e)
    update_status(" << FAILED >>")

providers = []
provider_mode = False

if Client.id >= 0:
    update_status("ID: %d" % Client.id)

    time.sleep(1)

    update_status("Finding host...")

    while True:

        time.sleep(.5)

        success, providers = Client.orchestrate(Service)

        if not success:
            update_status("ID: %d O.fail" % Client.id)
        else:
            #update_status("ID: %d P: %d" % (Client.id, len(providers)))
            pass

        for i in range(9):
            if len(providers) > 0 or GPIO.input(19) or GPIO.input(26):
                if GPIO.input(19):
                    update_status("Provider mode")

                    Client.unregister_service(ProvidedService)
                    provider_mode = Client.register_service(ProvidedService)
                break
            time.sleep(.5)
        else:
            continue

        break

time.sleep(.5)


######################
# Run required application
######################

import os

# We want to run it even when no providers are located (local version).
if len(providers) > 0:
    os.system("websocat --text cmd:\"stdbuf -oL /home/pi/optic_barrier_sw_ah\" wss://%s/barrier/1 -H \"Authorization: secret\"" % providers[0].address)
elif provider_mode:
    update_status("Awaiting conn")
    os.system("websocat -E --text ws-listen:127.0.0.1:%d reuse:cmd:\"stdbuf -oL /home/pi/optic_barrier_sw_ah\"" % (Client.port))
else:
    os.system("/home/pi/optic_barrier_sw_ah")


######################
# Turn off provider
######################

if provider_mode:
    Client.unregister_service(ProvidedService)


######################
# Clear display and bye
######################

display.fill(0)
display.show()

display.text("Bye!", 54, 12, True)
display.show()

time.sleep(1)

display.fill(0)
display.show()
