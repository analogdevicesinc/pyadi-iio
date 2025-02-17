# Copyright (C) 2022-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import numpy as np

from adi.context_manager import context_manager
from adi.rx_tx import rx


class sha_dev(rx, context_manager):

    """sha_dev family devices"""

    _device_name = ""
    _rx_data_type = np.int32
    _complex_data = False
    _rx_channel_names = ["voltage0"]

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["sha3-reader"]

        self._ctrl = None

        # Selecting the device_index-th device from the xxx2387 family as working device.
        for device in self._ctx.devices:
            if device.name == device_name:
                    self._ctrl = device
                    self._rxadc = device

        rx.__init__(self)
