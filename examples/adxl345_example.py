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

sfa = myacc.sampling_frequency_available
print("Sampling frequencies available:")
print(sfa)

xg = myacc.to_g(myacc.accel_x)
yg = myacc.to_g(myacc.accel_y)
zg = myacc.to_g(myacc.accel_z)

print("X acceleration: " + str(xg))
print("Y acceleration: " + str(yg))
print("Z acceleration: " + str(zg))

xsf = myacc.accel_x.sampling_frequency
ysf = myacc.accel_y.sampling_frequency
zsf = myacc.accel_z.sampling_frequency

print("X sample rate: " + str(xsf))
print("Y sample rate: " + str(ysf))
print("Z sample rate: " + str(zsf))
print("Setting only Z channel sample rate to 12.5 sps...")
myacc.accel_z.sampling_frequency = 12.5
time.sleep(0.25)
xsf = myacc.accel_x.sampling_frequency
ysf = myacc.accel_y.sampling_frequency
zsf = myacc.accel_z.sampling_frequency

print("new X sample rate: " + str(xsf))
print("new Y sample rate: " + str(ysf))
print("new Z sample rate: " + str(zsf))
myacc.accel_z.sampling_frequency = 100.0  # Set back to default

del myacc
