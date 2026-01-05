# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.context_manager import context_manager
from adi.rx_tx import rx_def


class ad9213(rx_def, context_manager):
    """ AD9213 High-Speed ADC """

    _complex_data = False
    _rx_channel_names = ["voltage0"]
    _control_device_name = "axi-ad9213-rx-hpc"
    _rx_data_device_name = "axi-ad9213-rx-hpc"
    _device_name = ""
