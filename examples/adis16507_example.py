# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi
import matplotlib.pyplot as plt
import numpy as np

# Set up ADIS16507
imu = adi.adis16507(uri="ip:analog")

imu.rx_output_type = "SI"
imu.rx_enabled_channels = [0, 1, 2, 3, 4, 5]
imu.sample_rate = 1024
imu.rx_buffer_size = 100

for _ in range(100):
    data = imu.rx()
    plt.clf()
    for i, d in enumerate(data):
        plt.plot(d, label=imu._rx_channel_names[i])
    plt.legend()
    plt.show(block=False)
    plt.pause(0.1)
