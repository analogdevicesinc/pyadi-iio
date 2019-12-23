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
