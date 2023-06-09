# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

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
