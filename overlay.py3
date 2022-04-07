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
