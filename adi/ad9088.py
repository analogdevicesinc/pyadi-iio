# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.ad9084 import ad9084


class ad9088(ad9084):
    """AD9088 Mixed-Signal Front End (MxFE)."""

    def __init__(
        self,
        uri="",
        rx1_device_name="axi-ad9088-rx-hpc",
        rx2_device_name="axi-ad9088-rx-b",
        tx1_device_name="axi-ad9088-tx-hpc",
        tx2_device_name="axi-ad9088-tx-b",
    ):
        """Create a new instance of the AD9088 MxFE."""
        # rx1_device_name is used as the name for the control device and
        # the RX1/TX1 data device.
        #
        # Args:
        #     uri: URI of device
        #     rx1_device_name: Name of RX1 device driver. Default is 'axi-ad9088-rx-hpc'
        #     rx2_device_name: Name of RX2 device driver. Default is 'axi-ad9088-rx-b'
        #     tx1_device_name: Name of TX1 device driver. Default is 'axi-ad9088-tx-hpc'
        #     tx2_device_name: Name of TX2 device driver. Default is 'axi-ad9088-tx-b'
        super().__init__(
            uri, rx1_device_name, rx2_device_name, tx1_device_name, tx2_device_name,
        )
