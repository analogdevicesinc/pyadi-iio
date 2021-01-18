# Copyright (C) 2020 Analog Devices, Inc.
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

""" Example of how to use the adar1000 class """

import adi

# Create device handle for a single ADAR1000 with the channels configured in a 1x4 array.
# Instantiation arguments:
#     chip_id: Must match the ADAR1000 label in the device tree. Defaults to "csb1_chip1"
#
#     array_element_map: Maps the array elements to a 1x4 array. See below:
#         (El. #1)    (El. #2)    (El. #3)    (El. #4)
#
#     channel_element_map: Maps the ADAR1000's channels to the array elements. See below:
#         Ch. #1 -> El. #2
#         Ch. #2 -> El. #1
#         Ch. #3 -> El. #4
#         Ch. #4 -> El. #3
device = adi.adar1000(
    chip_id="csb1_chip1",
    array_element_map=[[1, 2, 3, 4]],
    channel_element_map=[2, 1, 4, 3],
)

DEVICE_MODE = "rx"
if DEVICE_MODE == "rx":
    # Configure the device for Rx mode
    device.mode = "rx"

    SELF_BIASED_LNAs = True
    if SELF_BIASED_LNAs:
        # Allow the external LNAs to self-bias
        device.lna_bias_out_enable = False
    else:
        # Set the external LNA bias
        device.lna_bias_on = -0.7

    # Enable the Rx path for each channel
    for channel in device.channels:
        channel.rx_enable = True

# Configure the device for Tx mode
else:
    device.mode = "tx"

    # Enable the Tx path for each channel and set the external PA bias
    for channel in device.channels:
        channel.tx_enable = True
        channel.pa_bias_on = -1.1

# Set the array phases to 10°, 20°, 30°, and 40° and the gains to 0x67.
for channel in device.channels:
    # Set the gain and phase depending on the device mode
    if device.mode == "rx":
        channel.rx_phase = channel.array_element_number * 10
        channel.rx_gain = 0x67
    else:
        channel.tx_phase = channel.array_element_number * 10
        channel.tx_gain = 0x67

# Latch in the new gains & phases
if device.mode == "rx":
    device.latch_rx_settings()
else:
    device.latch_tx_settings()
