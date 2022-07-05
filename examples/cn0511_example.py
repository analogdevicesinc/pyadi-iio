# Copyright (C) 2019 Analog Devices, Inc.
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
import time

import adi
import numpy as np

# Set up CN0511. Replace URI with the actual uri of your CN0511 for remote access.
uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
rpi_sig_gen = adi.cn0511(uri=uri)

# Replace ambient temperature value with actual temperature for temperature
# calibration:
ambient_temp = 32.0  # set the ambient temperature

# Enable temperature measurements:
rpi_sig_gen.temperature_enable = True
print("Temperature read enabled: ", rpi_sig_gen.temperature_enable)

# Enable transmit:
rpi_sig_gen.tx_enable = True
print("Output enabled: ", rpi_sig_gen.tx_enable)

# Enable amplifier:
rpi_sig_gen.amp_enable = True
print("Amplifier enabled: ", rpi_sig_gen.amp_enable)

# Calibrate temperature:
rpi_sig_gen.temperature_cal = ambient_temp

# Read temperature:
temp = rpi_sig_gen.temperature
print("Chip Temperature: " + str(temp) + "°C")

# Set calibrated output [output_power_dbm, output_frequency_Hz]:
rpi_sig_gen.calibrated_output = [-20, 4000000000]
print(
    "Output power calibrated set to: " + str(rpi_sig_gen.calibrated_output[0]) + " dBm"
)
print("Output Frequency is set to: " + str(rpi_sig_gen.calibrated_output[1]) + " Hz")

print("Sleeping for 15 secs")
# sleep 15 sec
for i in range(15):
    print(".", end="", flush=True)
    time.sleep(1)
print(".")

# Disable reading temperature:
rpi_sig_gen.temperature_enable = False
print("Temperature read enabled: ", rpi_sig_gen.temperature_enable)

# Turn off amplifier and disable output:
print("Disabling the amplifier and output...")
rpi_sig_gen.amp_enable = False
print("Amplifier enabled: ", rpi_sig_gen.amp_enable)
rpi_sig_gen.tx_enable = False
print("Output enabled: ", rpi_sig_gen.tx_enable)
