# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi

# pass URI as command line argument
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None

# Set up ADXL31x
# Example: python3 adxl313_example.py serial:/dev/ttyACM0
myacc = adi.adxl313(uri=my_uri)
myacc.rx_buffer_size = 32
myacc.rx_enabled_channels = [0, 1, 2]

my_dev = myacc._device_name
print("Using device's " + my_dev + " settings.")

sfa = myacc.accel_x.sampling_frequency_available
print("\nSample frequencies available:")
print(sfa)

print("\nInitial sample frequency:")
print("Sample frequency: " + str(myacc.accel_x.sampling_frequency))

ra = myacc.accel_x.range_available
print("\nRanges available:")
print(ra)

print("\nInitial range:")
print("Range: " + str(myacc.accel_y.range))

sa = myacc.accel_x.scale_available
print("\nScales available:")
print(sa)

print("\nInitial scale:")
print("Scale: " + str(myacc.accel_z.scale))

print("\nSingle raw acceleration values:")
print("X acceleration: " + str(myacc.accel_x.raw * myacc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(myacc.accel_y.raw * myacc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(myacc.accel_z.raw * myacc.accel_z.scale) + " m/s^2")

print("\nSetting sample frequency to 800 sps...")
myacc.accel_y.sampling_frequency = sfa[7]
time.sleep(0.25)

print("Verifying new sample frequency: " + str(myacc.accel_x.sampling_frequency))
print("Setting back to 100 sps...")
myacc.accel_z.sampling_frequency = 100.0  # Set back to default
time.sleep(0.25)
print("Current sample frequency: " + str(myacc.accel_x.sampling_frequency))

if my_dev != "ADXL314":

    print("\nSetting scale to max value...")
    myacc.accel_x.scale = sa[0]
    time.sleep(0.25)

    print("\nCurrent scale:")
    print("Scale: " + str(myacc.accel_x.scale))

print("\nData using buffered rx(), SI (m/s^2):")
myacc.rx_output_type = "SI"
print(myacc.rx())

myacc.rx_output_type = "raw"
print("\nData using buffered rx(), raw:")
print(myacc.rx())

if my_dev != "ADXL314":

    print("\nSetting scale to min value...")
    myacc.accel_x.scale = sa[1]
    time.sleep(0.25)

    print("\nCurrent scale:")
    print("Scale: " + str(myacc.accel_y.scale))

    print("\nData using buffered rx(), SI (m/s^2):")
    myacc.rx_output_type = "SI"
    print(myacc.rx())

    myacc.rx_output_type = "raw"
    print("\nData using buffered rx(), raw:")
    print(myacc.rx())

del myacc
