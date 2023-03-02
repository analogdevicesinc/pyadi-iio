# Copyright (C) 2023 Analog Devices, Inc.
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

test_raw1 = 16384  # Test raw DAC code
test_raw2 = 8192  # Test raw DAC code

toggle1 = 41210  # 1st toggle value
toggle2 = 21410  # 2nd toggle value

dither_raw_test = 4100  # dither raw value
dither_off_test = 2100  # dither offset
dither_freq_test = 16384  # dither frequency
dither_phase_test = (
    1.5708  # dither phase. available options: 0, 1.5708, 3.14159, 4.71239
)

# indices of standard channels
# ch1 expected value = -3.9V
# even number channel = 1.249V
# odd number channel = 0.624V
standard_channels = [1, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]

# Device initialization
try:
    myDAC = adi.ltc2688(uri="ip:analog.local")

    for ch in myDAC._ctrl.channels:
        name = ch.id
        if "toggle_en" in ch.attrs:
            ch.raw0 = 0
            ch.raw1 = 0
            ch.toggle_en = 0
            if "symbol" in ch.attrs:
                print("Channel: " + name + " function: " + "sw toggle")
            else:
                print("Channel: " + name + " function: " + "hw toggle")
        elif "dither_en" in ch.attrs:
            ch.dither_en = 0
            ch.raw = 0
            print("Channel: " + name + " function: " + "dither")
        else:
            ch.raw = 0
            print("Channel: " + name + " function: " + "standard")

except Exception as e:
    print(str(e))
    print("Failed to open LTC2688 device")
    sys.exit(0)

print("")
print("")

# Basic DAC output setting function
try:
    print("Basic DAC output configuration.")
    for ch in range(0, 8):
        if hasattr(myDAC.channel[(ch * 2)], "raw"):
            if (ch * 2) in standard_channels:
                myDAC.channel[(ch * 2)].raw = test_raw1
                print(
                    "Channel: "
                    + str(myDAC.channel[(ch * 2)].name)
                    + " set to: "
                    + str(myDAC.channel[(ch * 2)].raw)
                )

        if hasattr(myDAC.channel[(ch * 2 + 1)], "raw"):
            if (ch * 2 + 1) in standard_channels:
                myDAC.channel[(ch * 2) + 1].raw = test_raw2
                print(
                    "Channel: "
                    + str(myDAC.channel[(ch * 2) + 1].name)
                    + " set to: "
                    + str(myDAC.channel[(ch * 2) + 1].raw)
                )

        time.sleep(0.05)

    time.sleep(3)

except Exception as e:
    print(str(e))
    print("Failed to write to LTC2688 DAC")
    sys.exit(0)

print("")
print("")

# Toggling Output for toggle enabled channels
try:
    print("DAC output toggling feature.")
    for ch in myDAC.channel:
        if hasattr(ch, "toggle_en"):
            ch.raw0 = toggle1
            ch.raw1 = toggle2

            print(
                "Channel: "
                + str(ch.name)
                + " set to: "
                + str(ch.raw0)
                + str(" (raw0)  ")
                + str(ch.raw1)
                + str(" (raw1)  ")
            )

            # Toggles between 1.6V and 3.1V
            if hasattr(ch, "symbol"):  # software toggle enable
                print("Software enabled toggle.")
                print("")
                for j in range(8):
                    ch.symbol = not (ch.symbol)
                    time.sleep(1)

            else:  # TGPx toggle enable
                print("Hardware enabled toggle. Supply clock at TGP1 pin.")
                print("")
                ch.toggle_en = 1
                time.sleep(2)
                ch.toggle_en = 0

    time.sleep(2)

except Exception as e:
    print(str(e))
    print("Failed to write to LTC2688 DAC")
    sys.exit(0)

print("")
print("")

# Dither output for enabled channels
# Monitor outputs at VOUT0 and VOUT3
try:
    print("Dither output feature.")
    for ch in myDAC.channel:
        if hasattr(ch, "dither_en"):
            print("Dither enabled at channel: " + str(ch.name))
            ch.dither_raw = dither_raw_test
            # ch.dither_offset = dither_off_test # cannot write value
            ch.dither_frequency = dither_freq_test
            ch.dither_phase = dither_phase_test

            print(
                "Dither Settings of: "
                + str(ch.dither_raw)
                + str(" (raw),  ")
                + str(ch.dither_offset)
                + str(" (offset),  ")
                + str(ch.dither_frequency)
                + str(" (frequency),  ")
                + str(ch.dither_phase)
                + str(" (phase).  ")
            )

            ch.dither_en = 1
            time.sleep(5)
            ch.dither_en = 0

except Exception as e:
    print(str(e))
    print("Failed to write to LTC2688 DAC")
    sys.exit(0)
