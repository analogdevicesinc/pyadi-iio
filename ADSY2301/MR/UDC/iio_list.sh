#!/bin/bash

echo "IIO Devices:"
for dev in /sys/bus/iio/devices/iio:device*; do
	  name=$(cat "$dev/name" 2>/dev/null)
	    echo "  $(basename $dev): $name"
    done
