#!/usr/bin/env python3
# generate_images.py3
"""Generate simulated screen images for the documentation."""

######################
# Imports & Globals
######################

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

import adafruit_framebuf

WIDTH = 128
HEIGHT = 32


######################
# SimulatedScreen class
######################

class SimulatedScreen(adafruit_framebuf.FrameBuffer):

    def __init__(self, width, height):
        self.buffer = bytearray(round(width * height / 8))

        super(SimulatedScreen, self).__init__(self.buffer, width, height, buf_format=adafruit_framebuf.MVLSB)

        self.image_index = 0

    def show(self):
        self.save()

    def save(self, status = ""):
        screen = Image.new("1", (self.width, self.height))

        for y in range(self.height):
            for x in range(self.width):
                if self.pixel(x, y):
                    screen.putpixel((x, y), 1)
                else:
                    screen.putpixel((x, y), 0)

        if status == "":
            screen.save("screen_%d.bmp" % self.image_index)
        else:
            screen.save("screen_%s.bmp" % status.replace(".", "").replace(":", "").replace("<", "").replace(">", "").replace("/", "_").replace(" ", "_").lower())

        self.image_index += 1


######################
# Create display
######################

display = SimulatedScreen(WIDTH, HEIGHT)

arrowhead_logo = Image.open("arrowhead_logo.bmp")
xoffset = arrowhead_logo.width + 3

logo = Image.new("1", (display.width, display.height))
logo.paste(arrowhead_logo)

display.image(logo)


######################
# Utilities
######################

def update_status(status, save_name = ""):
    display.fill_rect(xoffset, 24, 128, 32, False)
    display.text(status, xoffset, 24, True)

    if save_name == "":
        display.save(status)
    else:
        display.save(save_name)


######################
# Generate images
######################

# Loading screen
display.text("Arrowhead", xoffset, 0, True)
display.text("Overlay", xoffset, 8, True)
display.text("Loading...", xoffset, 24, True)

display.show()


# Git updates (overlay)
update_status("Updating...")


# Git updates (barrier)
update_status("Updating SW...")
update_status("Building...")
update_status("Updating binary...")
update_status("Building failed.")


# Restart after update
update_status("Restarting...")


# AHCore Discovery
update_status("Obtaining ID...")


## AHCore Discovery failed
update_status(" << FAILED >>")


## AHCore Discovery success
update_status("ID: %d" % 7)


# Main menu
display.fill_rect(xoffset, 16, 128, 32, False)
display.text("Select mode:", xoffset, 16, True)
update_status("< %s >" % "FindServer".center(10))


display.fill_rect(xoffset, 16, 128, 32, False)
display.text("Select mode:", xoffset, 16, True)
display.text("%d" % 5, display.width - 6, 16, True)
update_status("< %s >" % "FindServer".center(10), "findserver_with_countdown")

# Other menu options
update_status("< %s >" % "ProvideLap".center(10))
update_status("< %s >" % "Local only".center(10))
update_status("< %s >" % "bfed32c".center(10))


# Mode 1 Find Server
update_status("Finding host...")

# M1 Unable to orchestrate
update_status("ID: %d O.fail" % 7)

# M1 Multiple hosts
display.fill_rect(xoffset, 16, 128, 32, False)
display.text("Use provider:", xoffset, 16, True)
update_status("< %s >" % "scoreapp".center(10))

# M1 Multiple endpoints
display.fill_rect(xoffset, 16, 128, 32, False)
display.text("Select endp:", xoffset, 16, True)
update_status("< %s >" % "barrier/1".center(10))


# Mode 2 Provide lap
update_status("Provider mode")

update_status("P:%d I:%d S:%d" % (7, 2, 16))

# M2 Awaiting connection
update_status("Awaiting conn")



# Bye!
display.fill(0)

display.text("Bye!", 54, 12, True)
display.show()
