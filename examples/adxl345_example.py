# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi

# Set up ADXL345
myacc = adi.adxl345(uri="ip:192.168.1.232")
myacc.rx_output_type = "SI"
myacc.rx_buffer_size = 4
myacc.rx_enabled_channels = [0, 1, 2]

sfa = myacc.sampling_frequency_available
print("Sampling frequencies available:")
print(sfa)

print("\nX acceleration: " + str(myacc.accel_x.raw))
print("Y acceleration: " + str(myacc.accel_y.raw))
print("Z acceleration: " + str(myacc.accel_z.raw))

print("\nSample rate: " + str(myacc.sampling_frequency))

print("Setting sample rate to 12.5 sps...")
myacc.sampling_frequency = 12.5
time.sleep(0.25)

print("new sample rate: " + str(myacc.sampling_frequency))
myacc.sampling_frequency = 100.0  # Set back to default
print("\nData using unbuffered rx(), SI (m/s^2):")
print(myacc.rx())

myacc.rx_output_type = "raw"
print("\nData using unbuffered rx(), raw:")
print(myacc.rx())

del myacc
