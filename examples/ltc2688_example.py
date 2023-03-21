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

dither_raw_test = 8192  # dither raw value
dither_freq_test = 16384  # dither frequency
dither_phase_test = (
    1.5708  # dither phase. available options: 0, 1.5708, 3.14159, 4.71239
)

# indices of standard channels
# ch1 expected value = -3.9V
# ch2 expected value = 0V
# even number channel = 1.249V
# odd number channel = 0.624V
standard_channels = [1, 4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15]
toggle_channels = [2, 7]
dither_channels = [0, 3]

# Device initialization
try:
    myDAC = adi.ltc2688(uri="ip:169.254.8.72")

    for ch in myDAC.channel_names:
        ch_object = eval("myDAC." + str(ch))
        id_num = int(ch[7:])
        if id_num in toggle_channels:
            ch_object.raw0 = 0
            ch_object.raw1 = 0
            ch_object.toggle_en = 0
            if id_num == 7:
                print("Channel: " + str(ch) + " function: " + "sw toggle")
            else:
                print("Channel: " + str(ch) + " function: " + "hw toggle")
        elif id_num in dither_channels:
            ch_object.dither_en = 0
            if id_num == 3:
                ch_object.raw = 32768
            else:
                ch_object.raw = 0
            print("Channel: " + str(ch) + " function: " + "dither")
        else:
            ch_object.raw = 0
            print("Channel: " + str(ch) + " function: " + "standard")

except Exception as e:
    print(str(e))
    print("Failed to open LTC2688 device")
    sys.exit(0)

print("")
print("")


# Basic DAC output setting function
try:
    print("Basic DAC output configuration.")

    for ch in myDAC.channel_names:
        ch_object = eval("myDAC." + str(ch))
        id_num = int(ch[7:])

        if id_num in standard_channels:
            if id_num % 2 == 0:
                ch_object.raw = test_raw1
            else:
                ch_object.raw = test_raw2

            print("Channel: " + str(ch) + " set to: " + str(ch_object.raw))

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
    for ch in myDAC.channel_names:
        ch_object = eval("myDAC." + str(ch))
        id_num = int(ch[7:])

        if id_num in toggle_channels:
            ch_object.raw0 = toggle1
            ch_object.raw1 = toggle2

            print(
                "Channel: "
                + str(ch)
                + " set to: "
                + str(ch_object.raw0)
                + str(" (raw0)  ")
                + str(ch_object.raw1)
                + str(" (raw1)  ")
            )

            # Toggles between 1.6V and 3.1V
            if id_num == 7:  # software toggle enable
                print("Software enabled toggle.")
                print("")
                ch_object.toggle_en = 1
                for j in range(8):
                    ch_object.toggle_state = not (ch_object.toggle_state)
                    print("Toggling...")
                    time.sleep(1)
                ch_object.toggle_en = 0

            else:  # TGPx toggle enable
                print("Hardware enabled toggle. Supply clock at TGP1 pin.")
                print("")
                ch_object.toggle_en = 1
                time.sleep(2)
                ch_object.toggle_en = 0

            print("")

    time.sleep(2)

except Exception as e:
    print(str(e))
    print("Failed to write to LTC2688 DAC")
    sys.exit(0)


# Dither output for enabled channels
# Monitor outputs at VOUT0 and VOUT3
try:
    print("Dither output feature.")
    for ch in myDAC.channel_names:
        ch_object = eval("myDAC." + str(ch))
        id_num = int(ch[7:])

        if id_num in dither_channels:
            print("Dither enabled at channel: " + str(ch))
            ch_object.dither_raw = dither_raw_test
            ch_object.dither_frequency = dither_freq_test
            ch_object.dither_phase = dither_phase_test

            print(
                "Dither Settings of: "
                + str(ch_object.dither_raw)
                + str(" (raw),  ")
                + str(ch_object.dither_offset)
                + str(" (offset),  ")
                + str(ch_object.dither_frequency)
                + str(" (frequency),  ")
                + str(ch_object.dither_phase)
                + str(" (phase).  ")
            )

            ch_object.dither_en = 1
            time.sleep(5)
            ch_object.dither_en = 0

            print("")

except Exception as e:
    print(str(e))
    print("Failed to write to LTC2688 DAC")
    sys.exit(0)
