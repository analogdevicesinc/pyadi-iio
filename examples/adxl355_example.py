# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import adi

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
print("uri: " + str(my_uri))

# Set up ADXL355
myacc = adi.adxl355(uri=my_uri)
myacc.rx_buffer_size = 32
myacc.rx_enabled_channels = [0, 1, 2]

print("\nChecking temperature channel...")
print("Temperature raw: " + str(myacc.temp.raw))
print("Calculated Temperature: " + str(myacc.to_degrees(myacc.temp.raw)))

print("\nCurrent Timestamp: " + str(myacc.current_timestamp_clock))

sfa = myacc.accel_x.sampling_frequency_available
print("\nSampling frequencies available:")
print(sfa)

print("\nInitial sample frequency:")
print("X Sample frequency: " + str(myacc.accel_x.sampling_frequency))
print("Y Sample frequency: " + str(myacc.accel_y.sampling_frequency))
print("Z Sample frequency: " + str(myacc.accel_z.sampling_frequency))

print("Single raw acceleration values:")
print("\nX acceleration: " + str(myacc.accel_x.raw * myacc.accel_x.scale) + " m/s^2")
print("Y acceleration: " + str(myacc.accel_y.raw * myacc.accel_y.scale) + " m/s^2")
print("Z acceleration: " + str(myacc.accel_z.raw * myacc.accel_z.scale) + " m/s^2")

print("\nSetting sample frequencies to 1000 sps...")
myacc.accel_x.sampling_frequency = sfa[2]
myacc.accel_y.sampling_frequency = sfa[2]
myacc.accel_z.sampling_frequency = sfa[2]
time.sleep(0.25)

print("Verifying new sample rate: " + str(myacc.accel_x.sampling_frequency))
print("Setting back to 4000 sps...")
myacc.accel_x.sampling_frequency = 4000.0
myacc.accel_y.sampling_frequency = 4000.0
myacc.accel_z.sampling_frequency = 4000.0  # Set back to default
time.sleep(0.25)

print("\nData using buffered rx(), SI (m/s^2):")
myacc.rx_output_type = "SI"
print(myacc.rx())

myacc.rx_output_type = "raw"
print("\nData using buffered rx(), raw:")
print(myacc.rx())

cutoffs = myacc.accel_x.filter_high_pass_3db_frequency_available
print("\nX available highpass cutoff frequencies: " + str(cutoffs))

print(
    "Setting highpass cutoff frequency to "
    + str(cutoffs[1])
    + " then taking a nap to settle..."
)
myacc.accel_x.filter_high_pass_3db_frequency = cutoffs[1]
myacc.accel_y.filter_high_pass_3db_frequency = cutoffs[1]
myacc.accel_z.filter_high_pass_3db_frequency = cutoffs[1]

print(
    "\nX highpass cutoff frequency: "
    + str(myacc.accel_x.filter_high_pass_3db_frequency)
)
print(
    "Y highpass cutoff frequency: " + str(myacc.accel_y.filter_high_pass_3db_frequency)
)
print(
    "Z highpass cutoff frequency: " + str(myacc.accel_z.filter_high_pass_3db_frequency)
)

time.sleep(2.0)
print("\nAccelerations after highpass, should be close to zero if the")
print("ADXL355 is sitting still...")
print("X acceleration: " + str(myacc.accel_x.raw))
print("Y acceleration: " + str(myacc.accel_y.raw))
print("Z acceleration: " + str(myacc.accel_z.raw))

print("\nSetting highpass cutoff frequency back to zero...")
myacc.accel_x.filter_high_pass_3db_frequency = 0.0000
myacc.accel_y.filter_high_pass_3db_frequency = 0.0000
myacc.accel_z.filter_high_pass_3db_frequency = 0.0000

del myacc
