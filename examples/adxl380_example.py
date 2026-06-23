# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi

my_dev_name = sys.argv[1]
my_uri = sys.argv[2]

print("uri: " + str(my_uri))

# Set up adxl380
my_acc = adi.adxl380(uri=my_uri, device_name=my_dev_name)
# my_acc.rx_buffer_size = 16
my_acc.rx_enabled_channels = [0, 1, 2]

print("\nChecking temperature channel...")
print("Temperature raw: " + str(my_acc.temp.raw))
print("Calculated Temperature: " + str(my_acc.to_degrees(my_acc.temp.raw)))


print("\nInitial sample frequency:")
print("Sample frequency: " + str(my_acc.sampling_frequency))

print("Single calculated acceleration values:")
print("\nX acceleration: " + str(my_acc.accel_x.raw * my_acc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(my_acc.accel_y.raw * my_acc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(my_acc.accel_z.raw * my_acc.accel_z.scale) + " m/s^2")

print("\nSetting sample frequencies to 1000 sps...")
my_acc.sampling_frequency = "{:.6f}".format(16000)
time.sleep(0.25)

print("Verifying new sample rate: " + str(my_acc.sampling_frequency))
print("Setting back to 4000 sps...")
my_acc.sampling_frequency = "{:.6f}".format(4000.0)
time.sleep(0.25)

my_acc.rx_output_type = "raw"
print("\nData using buffered rx(), raw:")
print(my_acc.rx())

cutoffs = my_acc.accel_x.filter_high_pass_3db_frequency_available
print("\nAvailable highpass cutoff frequencies: " + str(cutoffs))

print(
    "\nSetting highpass cutoff frequency to "
    + str(cutoffs[1])
    + " then taking a 2 second nap to settle..."
)
my_acc.accel_x.filter_high_pass_3db_frequency = "{:.6f}".format(cutoffs[1])
my_acc.accel_y.filter_high_pass_3db_frequency = "{:.6f}".format(cutoffs[1])
my_acc.accel_z.filter_high_pass_3db_frequency = "{:.6f}".format(cutoffs[1])

print(
    "\nX highpass cutoff frequency: "
    + str(my_acc.accel_x.filter_high_pass_3db_frequency)
)
print(
    "Y highpass cutoff frequency: " + str(my_acc.accel_y.filter_high_pass_3db_frequency)
)
print(
    "Z highpass cutoff frequency: " + str(my_acc.accel_z.filter_high_pass_3db_frequency)
)

time.sleep(2.0)

print(
    "\nAccelerations after highpass, should be close to zero if the adxl380 is sitting still...\n"
)
print("X acceleration: " + str(my_acc.accel_x.raw * my_acc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(my_acc.accel_y.raw * my_acc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(my_acc.accel_z.raw * my_acc.accel_z.scale) + " m/s^2")

print(
    "\nSetting highpass cutoff frequency back to zero, then taking a 4 second nap to settle..."
)
my_acc.accel_x.filter_high_pass_3db_frequency = "{:.6f}".format(0.0)
my_acc.accel_y.filter_high_pass_3db_frequency = "{:.6f}".format(0.0)
my_acc.accel_z.filter_high_pass_3db_frequency = "{:.6f}".format(0.0)

time.sleep(4.0)

print("\nAccelerations after highpass settling...")

print("X acceleration: " + str(my_acc.accel_x.raw * my_acc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(my_acc.accel_y.raw * my_acc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(my_acc.accel_z.raw * my_acc.accel_z.scale) + " m/s^2")

print("\nSetting offset for each axis...\n")
print("X offset set to: " + str(my_acc.accel_x.raw >> 4))
print("Y offset set to: " + str(my_acc.accel_y.raw >> 4))
print("Z offset set to: " + str(my_acc.accel_z.raw >> 4))

my_acc.accel_x.calibbias = "{:.6f}".format(my_acc.accel_x.raw >> 4)
my_acc.accel_y.calibbias = "{:.6f}".format(my_acc.accel_y.raw >> 4)
my_acc.accel_z.calibbias = "{:.6f}".format(my_acc.accel_z.raw >> 4)

print(
    "\nAccelerations after setting offset, should be close to zero if the adxl380 is sitting still...\n"
)
print("X acceleration: " + str(my_acc.accel_x.raw * my_acc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(my_acc.accel_y.raw * my_acc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(my_acc.accel_z.raw * my_acc.accel_z.scale) + " m/s^2")

print("\nSetting offset for each axis back to 0...")
my_acc.accel_x.calibbias = "{:.6f}".format(0.0)
my_acc.accel_y.calibbias = "{:.6f}".format(0.0)
my_acc.accel_z.calibbias = "{:.6f}".format(0.0)

del my_acc
