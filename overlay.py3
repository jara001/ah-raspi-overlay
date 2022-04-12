#!/usr/bin/env python3
# overlay.py3
"""Arrowhead Compliant overlay."""

import os, subprocess


######################
# Exit sequence
######################

import signal

provider_mode = False
sequence_run = False

def exit_sequence(sig, frame):
    global sequence_run

    if sequence_run:
        return

    sequence_run = True

    # Ensure barrier dying
    os.system("pkill -f optic_barrier_sw_ah")

    # Turn off provider
    if provider_mode:
        Client.unregister_service(ProvidedService)

    # Clear display and bye
    display.fill(0)
    display.show()

    display.text("Bye!", 54, 12, True)
    display.show()

    time.sleep(1)

    display.fill(0)
    display.show()


signal.signal(signal.SIGTERM, exit_sequence)


######################
# Obtain IP address
######################

import socket

def get_ip():
    """Get IP address.

    Source: https://stackoverflow.com/questions/60656088/how-to-get-wireless-lan-adapter-wi-fi-ip-address-in-python
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


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
from PIL import ImageDraw
from PIL import ImageFont

arrowhead_logo = Image.open("arrowhead_logo.bmp")
xoffset = arrowhead_logo.width + 3

logo = Image.new("1", (display.width, display.height))
logo.paste(arrowhead_logo)

draw = ImageDraw.Draw(logo)
font = ImageFont.truetype("LiberationSans-Regular.ttf", size=7)

last_hash = str(subprocess.check_output("git log -1 --format=\"%h\"", shell = True))[2:-3]
dirty = "dirty" in str(subprocess.check_output("git describe --always --dirty", shell = True))

draw.text((128-4*len(last_hash), 24), last_hash.upper() if dirty else last_hash, fill = 255, font = font)

display.image(logo)

display.text("Arrowhead", xoffset, 0, True)
display.text("Overlay", xoffset, 8, True)
display.text("Loading", xoffset, 24, True)
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
    FindServer = "FindServer", True
    ProviderMode = "ProvideLap", True
    LocalMode = "Local only", True


MENU_DESCRIPTION = "Select mode:"

MENU_MOVE_LEFT = 19
MENU_MOVE_RIGHT = 26
MENU_SELECT = 21

DEFAULT_OPTION = MenuOptions.LocalMode
AUTO_SELECT_DELAY = 5

def show_menu():
    auto_start = False
    auto_time = AUTO_SELECT_DELAY

    display.fill_rect(xoffset, 16, 128, 32, False)
    display.text(MENU_DESCRIPTION, xoffset, 16, True)
    if auto_time > 0:
        auto_start = True
        display.text("%d" % auto_time, display.width - 6, 16, True)

    options = list(MenuOptions)
    index = options.index(DEFAULT_OPTION)

    update_status("< %s >" % options[index].value[0])

    while not (not GPIO.input(MENU_SELECT) and options[index].value[1]):
        redraw = False

        if GPIO.input(MENU_MOVE_LEFT):
            auto_start = False
            index = (index - 1) % len(options)
            redraw = True

        if GPIO.input(MENU_MOVE_RIGHT):
            auto_start = False
            index = (index + 1) % len(options)
            redraw = True

        if redraw:
            display.fill_rect(display.width - 6, 8, 128, 16, False)
            update_status("< %s >" % options[index].value[0])

        time.sleep(.1)

        if auto_start:
            auto_time -= .1
            display.fill_rect(display.width - 6, 8, 128, 16, False)
            display.text("%d" % auto_time, display.width - 6, 16, True)
            display.show()
            if auto_time <= 0:
                break

    display.fill_rect(xoffset, 16, 128, 32, False)

    return options[index]


######################
# Auto-Update sequence
######################

# Source: https://gist.github.com/skabber/1213826

return_code = subprocess.call("git fetch", shell = True)

if return_code == 0:
    latest = subprocess.check_output("git rev-list --max-count=1 master", shell = True)
    latest_remote = subprocess.check_output("git rev-list --max-count=1 origin/master", shell = True)

    if latest != latest_remote:
        update_status("Updating...")

        subprocess.check_output("git pull origin master", shell = True)

        update_status("Restarting...")
        time.sleep(.5)

        exit_sequence(signal.SIGTERM, None)


# SW C++
BRANCH = "devel/arrowhead-final"

return_code = subprocess.call("cd ~/f1tenth-scoreapp && git fetch", shell = True)

if return_code == 0:
    latest = subprocess.check_output("cd ~/f1tenth-scoreapp && git rev-list --max-count=1 %s" % BRANCH, shell = True)
    latest_remote = subprocess.check_output("cd ~/f1tenth-scoreapp && git rev-list --max-count=1 origin/%s" % BRANCH, shell = True)

    if latest != latest_remote:
        update_status("Updating SW...")

        subprocess.check_output("cd ~/f1tenth-scoreapp && git pull origin %s" % BRANCH, shell = True)

        update_status("Building...")

        return_code = subprocess.call("cd ~/f1tenth-scoreapp/barrier/optic_barrier_sw && mkdir -p build && cd build && cmake .. && make", shell = True)

        if return_code == 0:
            update_status("Updating binary...")

            subprocess.call("cp ~/f1tenth-scoreapp/barrier/optic_barrier_sw/build/optic_barrier_sw ~/optic_barrier_sw_ah", shell = True)

        else:
            update_status("Building failed.")
            time.sleep(1.5)


        update_status("Restarting...")
        time.sleep(.5)

        exit_sequence(signal.SIGTERM, None)


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

matches = []
provider_mode = False

if Client.id >= 0:
    update_status("ID: %d" % Client.id)

    time.sleep(1)

    option = show_menu()

    if option == MenuOptions.FindServer:

        update_status("Finding host...")

        while True:

            time.sleep(.5)

            success, matches = Client.orchestrate(Service)

            if not success:
                update_status("ID: %d O.fail" % Client.id)
            else:
                #update_status("ID: %d P: %d" % (Client.id, len(providers)))
                pass

            for i in range(9):
                if len(matches) > 0 or GPIO.input(26):
                    break
                time.sleep(.5)
            else:
                continue

            break

    elif option == MenuOptions.ProviderMode:
        update_status("Provider mode")

        Client.unregister_service(ProvidedService)
        provider_mode = Client.register_service(ProvidedService)

        time.sleep(.5)

        display.fill_rect(xoffset, 16, 128, 32, False)
        display.text(get_ip(), xoffset, 16, True)
        update_status("P:%d I:%d S:%d" % (Client.id, Interface.id, ProvidedService.id))

        while not GPIO.input(21):
            time.sleep(.1)


time.sleep(.5)


######################
# Run required application
######################

# We want to run it even when no providers are located (local version).
if len(matches) > 0:
    # When websocat fails, the barrier dies only when it tries to write something to the output.
    os.system("websocat -E --exec-sighup-on-stdin-close --text cmd:\"stdbuf -oL /home/pi/optic_barrier_sw_ah\" wss://%s/barrier/1 -H \"Authorization: %s\"" % (matches[0].get("provider").address, matches[0].get("service").metadata.get("authorization", "secret")))
elif provider_mode:
    update_status("Awaiting conn")
    os.system("sh activate-provider.sh ws://%s:%d" % (get_ip(), Client.port))
    os.system("websocat -E --text ws-listen:%s:%d reuse:cmd:\"stdbuf -oL /home/pi/optic_barrier_sw_ah\"" % (get_ip(), Client.port))
else:
    os.system("/home/pi/optic_barrier_sw_ah")


######################
# Clean exit the overlay
######################

exit_sequence(signal.SIGTERM, None)
