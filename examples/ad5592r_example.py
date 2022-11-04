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
from adi.context_manager import context_manager

# Set up AD5592R/AD5593R
myad5592r = adi.ad5592r(uri="")

# Write votalge value for each channel
for ch in myad5592r.channel:
    if ch._output:  # We only write if it is an output channel
        mV = input(f"Enter desired voltage for channel {ch.name} in mV: ")
        ch.raw = float(mV) / float(ch.scale)

# Read each channels and its parameters
print(myad5592r.channel)
for ch in myad5592r.channel:
    print("***********************")  # Just a separator for easier serial read
    print("Channel Name: ", ch.name)  # Channel Name
    print("is Output? ", ch._output)  # True = Output/Write/DAC, False = Input/Read/ADC
    print(
        "Channel Scale: ", ch.scale
    )  # Channel Scale can be 0.610351562 or 0.610351562*2
    print("Channel Raw Value: ", float(ch.raw))  # Channel Raw Value

    # Print Temperature in Celsius
    if ch.name == "temp":
        T = ((ch.raw + ch.offset) * ch.scale) / 1000
        print("Channel Temperature (C): ", float(T))
    # Print Real Voltage in mV
    else:
        print(
            "Channel Real Value (mV): ", float(ch.raw * ch.scale)
        )  # Channel Raw Value
