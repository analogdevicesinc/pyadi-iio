# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse
import time

import adi

# Optionally pass URI as command line argument with -u option,
# else use default to "ip:analog.local"
parser = argparse.ArgumentParser(description="ADXL355 Example Script")
parser.add_argument(
    "-u",
    default=["ip:analog.local"],
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
args = parser.parse_args()
my_uri = args.u[0]

print("uri: " + str(my_uri))

# Set up ADXL355
my_acc = adi.adxl355(uri=my_uri)
my_acc.rx_buffer_size = 32
my_acc.rx_enabled_channels = [0, 1, 2]

print("\nChecking temperature channel...")
print("Temperature raw: " + str(my_acc.temp.raw))
print("Calculated Temperature: " + str(my_acc.to_degrees(my_acc.temp.raw)))

# print("\nCurrent Timestamp: " + str(my_acc.current_timestamp_clock))
# Not enabled as of Kuiper 2022_r2, and not implemented in no-OS

sfa = my_acc.accel_x.sampling_frequency_available
print("\nSampling frequencies available:")
print(sfa)

print("\nInitial sample frequency:")
print("X Sample frequency: " + str(my_acc.accel_x.sampling_frequency))
print("Y Sample frequency: " + str(my_acc.accel_y.sampling_frequency))
print("Z Sample frequency: " + str(my_acc.accel_z.sampling_frequency))

print("Single calculated acceleration values:")
print("\nX acceleration: " + str(my_acc.accel_x.raw * my_acc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(my_acc.accel_y.raw * my_acc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(my_acc.accel_z.raw * my_acc.accel_z.scale) + " m/s^2")

print("\nSetting sample frequencies to 1000 sps...")
my_acc.accel_x.sampling_frequency = "{:.6f}".format(sfa[2])
my_acc.accel_y.sampling_frequency = "{:.6f}".format(sfa[2])
my_acc.accel_z.sampling_frequency = "{:.6f}".format(sfa[2])
time.sleep(0.25)

print("Verifying new sample rate: " + str(my_acc.accel_x.sampling_frequency))
print("Setting back to 4000 sps...")
my_acc.accel_x.sampling_frequency = "{:.6f}".format(4000.0)
my_acc.accel_y.sampling_frequency = "{:.6f}".format(4000.0)
my_acc.accel_z.sampling_frequency = "{:.6f}".format(4000.0)
time.sleep(0.25)

print("\nData using buffered rx(), SI (m/s^2):")
my_acc.rx_output_type = "SI"
print(my_acc.rx())

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
    "\nAccelerations after highpass, should be close to zero if the ADXL355 is sitting still...\n"
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
    "\nAccelerations after setting offset, should be close to zero if the ADXL355 is sitting still...\n"
)
print("X acceleration: " + str(my_acc.accel_x.raw * my_acc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(my_acc.accel_y.raw * my_acc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(my_acc.accel_z.raw * my_acc.accel_z.scale) + " m/s^2")

print("\nSetting offset for each axis back to 0...")
my_acc.accel_x.calibbias = "{:.6f}".format(0.0)
my_acc.accel_y.calibbias = "{:.6f}".format(0.0)
my_acc.accel_z.calibbias = "{:.6f}".format(0.0)

del my_acc
