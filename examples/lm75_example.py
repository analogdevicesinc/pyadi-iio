# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

# Set up LM75
my_temp_sensr = adi.lm75(uri=my_uri)

print("\nChecking temperature channel...")
print("Temperature raw: " + str(my_temp_sensr.input))
print(
    "Temperature in deg. Celsius: " + str(my_temp_sensr.to_degrees(my_temp_sensr.input))
)

print("\nUpdate interval: " + str(my_temp_sensr.update_interval))


print("\nMax threshold: " + str(my_temp_sensr.to_degrees(my_temp_sensr.max)))
print("Max hysteresis: " + str(my_temp_sensr.to_degrees(my_temp_sensr.max_hyst)))

print("\nSetting max threshold, hyst. to 30C, 25C...\n")

my_temp_sensr.max = my_temp_sensr.to_millidegrees(30.0)
my_temp_sensr.max_hyst = my_temp_sensr.to_millidegrees(25.0)

print("New thresholds:")
print("Max: " + str(my_temp_sensr.to_degrees(my_temp_sensr.max)))
print("Max hysteresis: " + str(my_temp_sensr.to_degrees(my_temp_sensr.max_hyst)))

del my_temp_sensr
