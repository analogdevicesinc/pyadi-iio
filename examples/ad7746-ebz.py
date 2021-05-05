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

import sys
from time import sleep

import adi

VIN = "voltage0"
VIN_VDD = "voltage1"
TEMP_INT = "temp0"
TEMP_EXT = "temp1"
CIN1 = "capacitance0"
CIN1_DIFF = "capacitance0-capacitance2"
CIN2 = "capacitance1"
CIN2_DIFF = "capacitance1-capacitance3"

# Set up AD7746
dev = adi.ad7746(uri="serial:/dev/ttyACM0,115200,8n1", device_name="ad7746")
dev.channel[CIN1].offset = 66

input("[CALIB] 1. Remove the ruler and press ENTER. ")
m = dev.channel[CIN1].raw
input("[CALIB] 2. Place ruler to 51mm (2inch) and press ENTER.")
M = dev.channel[CIN1].raw

mm = (M - m) / 51

print(
    "[DEMO] Move the ruler around, its position will is read and displayed every 2 seconds.\n"
)

while True:
    capData = dev.channel[CIN1].raw
    capData -= m
    capData /= mm
    temperature = dev.channel[TEMP_INT].input
    temperature /= 1000.0
    print("Position: {} mm, Temperature: {} *C".format(int(capData), temperature))
    sleep(2)
