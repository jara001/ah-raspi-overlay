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
# Arrowhead Logo
######################

from PIL import Image

logo = Image.new("1", (display.width, display.height))
logo.paste(Image.open("arrowhead_logo.bmp"))


display.image(logo)
display.show()
