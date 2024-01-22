# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt

# Set up ADIS16480
dev = adi.adis16480(uri="ip:localhost", device_name="adis16480")


print("\nX acceleration: " + str(dev.accel_x_conv) + " m/s^2")
print("Y acceleration: " + str(dev.accel_y_conv) + " m/s^2")
print("Z acceleration: " + str(dev.accel_z_conv) + " m/s^2")

print("\nX angular velocity: " + str(dev.anglvel_x_conv) + " rad/s")
print("Y angular velocity: " + str(dev.anglvel_y_conv) + " rad/s")
print("Z angular velocity: " + str(dev.anglvel_z_conv) + " rad/s")

dev.sample_rate = 2000
dev.magn_x_filter_low_pass_3db_frequency = 100
dev.anglvel_y_calibscale = 30
dev.anglvel_x_calibbias = 100

print("Sampling frequency: " + str(dev.sample_rate))

print("Temperature raw value: " + str(dev.temp.raw))
print("Temperature scale value: " + str(dev.temp.scale))
print("Temperature offset value: " + str(dev.temp.offset))

print("X-axis gyro channel calibbias value: " + str(dev.anglvel_x_calibbias))
print("X-axis gyro channel calibscale value: " + str(dev.anglvel_y_calibscale))
print("X-axis magnetometer bandwidth: " + str(dev.magn_x_filter_low_pass_3db_frequency))