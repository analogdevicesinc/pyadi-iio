# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

VIN = "voltage0"
VIN_VDD = "voltage1"
TEMP_INT = "temp0"
TEMP_EXT = "temp1"
CIN1 = "capacitance0"
CIN1_DIFF = "capacitance0-capacitance2"
CIN2 = "capacitance1"
CIN2_DIFF = "capacitance1-capacitance3"


def cap_attributes(dev, ch):
    print(ch)
    val = dev.channel[ch].raw
    print("\traw: {}".format(val))
    val = dev.channel[ch].scale
    print("\tscale: {}".format(val))
    val = dev.channel[ch].sampling_frequency
    print("\tsampling_frequency: {}".format(val))
    val = dev.channel[ch].sampling_frequency_available
    print("\tsampling_frequency_available: {}".format(val))
    val = dev.channel[ch].calibbias
    print("\tcalibbias: {}".format(val))
    val = dev.channel[ch].calibscale
    print("\tcalibscale: {}".format(val))


# Set up AD7746
dev = adi.ad7746(uri="serial:/dev/ttyACM0,115200,8n1", device_name="ad7746")
# dev = adi.ad7746(uri="ip:192.168.1.10", device_name="ad7746")

cap_attributes(dev, CIN1)
cap_attributes(dev, CIN1_DIFF)
cap_attributes(dev, CIN2)
cap_attributes(dev, CIN2_DIFF)

print("Changing sampling frequency to 50")
dev.channel[CIN1].sampling_frequency = 50

print("Changing calibbias to 12345")
dev.channel[CIN1].calibbias = 12345

print("Changing calibscale to 1.5")
dev.channel[CIN1].calibscale = 1.5

cap_attributes(dev, CIN1)
cap_attributes(dev, CIN1_DIFF)
cap_attributes(dev, CIN2)
cap_attributes(dev, CIN2_DIFF)

print("Calibbias calibration...")
dev.channel[CIN1].calibbias_calibration()
print("Calibscale calibration...")
dev.channel[CIN1].calibscale_calibration()

print("Temperature (internal): {}".format(dev.channel[TEMP_INT].input))
print("Temperature (external): {}".format(dev.channel[TEMP_EXT].input))
