#!/bin/sh
sleep 2s && kill $$ &
websocat -n -1 --text autoreconnect:"$1" -
