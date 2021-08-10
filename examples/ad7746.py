# Copyright (C) 2021 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
