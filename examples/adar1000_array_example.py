# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

""" Example of how to use the adar1000_array class """

import adi

# Create handle for an array of 4 ADAR1000s with the channels configured in a 4x4 array.
#
# Instantiation arguments:
#     chip_ids: Must match the ADAR1000 labels in the device tree
#
#     device_map: Maps the ADAR1000s to their location in the array. See below:
#         (ADAR1000 #1)    (ADAR1000 #2)
#         (ADAR1000 #3)    (ADAR1000 #4)
#
#     element_map: Maps the element numbers in the array. See below:
#         (El. #1)    (El. #2)    (El. #3)    (El. #4)
#         (El. #5)    (El. #6)    (El. #7)    (El. #8)
#         (El. #9)    (El. #10)   (El. #11)   (El. #12)
#         (El. #13)   (El. #14)   (El. #15)   (El. #16)
#
#     device_element_map: Maps the ADAR1000s to specific elements in the array, in channel order. See below:
#         ADAR1000 #1:
#             Ch. #1 -> El. #5
#             Ch. #2 -> El. #6
#             Ch. #3 -> El. #2
#             Ch. #4 -> El. #1
#         ADAR1000 #2:
#             Ch. #1 -> El. #7
#             Ch. #2 -> El. #8
#             Ch. #3 -> El. #4
#             Ch. #4 -> El. #3
#         ADAR1000 #3:
#             Ch. #1 -> El. #13
#             Ch. #2 -> El. #14
#             Ch. #3 -> El. #10
#             Ch. #4 -> El. #9
#         ADAR1000 #4:
#             Ch. #1 -> El. #15
#             Ch. #2 -> El. #16
#             Ch. #3 -> El. #12
#             Ch. #4 -> El. #11
array = adi.adar1000_array(
    chip_ids=["csb1_chip1", "csb1_chip2", "csb1_chip3", "csb1_chip4"],
    device_map=[[1, 2], [3, 4]],
    element_map=[[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]],
    device_element_map={
        1: [5, 6, 2, 1],
        2: [7, 8, 4, 3],
        3: [13, 14, 10, 9],
        4: [15, 16, 12, 11],
    },
)

# Set the array frequency to 12GHz and the element spacing to 12.5mm so that the array can be accurately steered
array.frequency = 12e9
array.element_spacing = 0.0125

ARRAY_MODE = "rx"
if ARRAY_MODE == "rx":
    # Configure the array for Rx
    for device in array.devices.values():
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

# Configure the array for Tx mode
else:
    for device in array.devices.values():
        device.mode = "tx"

        # Enable the Tx path for each channel and set the external PA bias
        for channel in device.channels:
            channel.pa_bias_on = -1.1
            channel.tx_enable = True

# Steer the Rx array to 10° azimuth and 45° elevation
if ARRAY_MODE == "rx":
    array.steer_rx(azimuth=10, elevation=45)

    # Set the element gains to 0x67
    for element in array.elements.values():
        element.rx_gain = 0x67

    # Latch in the new gains
    array.latch_rx_settings()

# Steer the Tx array to 10° azimuth and 45° elevation
else:
    array.steer_tx(azimuth=10, elevation=45)

    # Set the element gains to 0x67
    for element in array.elements.values():
        element.tx_gain = 0x67

    # Latch in the new gains
    array.latch_tx_settings()
