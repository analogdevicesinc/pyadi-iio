# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi

temp_sensor = adi.adt7420(uri="serial:COM24,57600,8N1")

print("Max Temperature Threshold = " + str(temp_sensor.temp.temp_max))
print("Min Temperature Threshold = " + str(temp_sensor.temp.temp_min))
print("Crit Temperature Threshold = " + str(temp_sensor.temp.temp_crit))
print("Hysteresis Temperature Setting = " + str(temp_sensor.temp.temp_hyst))

datapoints = 300
for i in range(datapoints):
    print(
        "Temperature Measurement " + str(i + 1) + " = " + str(temp_sensor.temp.temp_val)
    )
    time.sleep(0.1)
