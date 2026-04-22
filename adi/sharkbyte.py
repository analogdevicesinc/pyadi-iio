# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

from adi.hmcad15xx import hmcad15xx


class sharkbyte(object):
    """Sharkbyte Multi-ADC Manager

    Manages synchronized data capture from two HMCAD15xx ADCs using TDD-based
    DMA synchronization.

    Parameters:
        uri: type=string
            URI of the hardware platform (e.g., "ip:192.168.2.1")
        device1_name: type=string
            Device name for first ADC (default: "axi_adc1_hmcad15xx")
        device2_name: type=string
            Device name for second ADC (default: "axi_adc2_hmcad15xx")
        enable_tddn: type=bool (optional)
            If True, create a TDD controller for DMA synchronization.
            The TDD controller will be available as the 'tddn' attribute.
            The rx() method will trigger TDD sync before capture.
    """

    __rx_buffer_size_multi = 2 ** 14

    def __init__(
        self,
        uri="",
        device1_name="axi_adc1_hmcad15xx",
        device2_name="axi_adc2_hmcad15xx",
        enable_tddn=False,
    ):
        """Initialize sharkbyte multi-ADC manager"""

        self._dma_show_arming = False
        self._rx_initialized = False
        self.tddn = None

        # Create TDD controller if enabled
        if enable_tddn:
            from adi.tddn import tddn

            self.tddn = tddn(uri)

        # Create both ADC devices
        self.dev1 = hmcad15xx(uri=uri, device_name=device1_name)
        self.dev2 = hmcad15xx(uri=uri, device_name=device2_name)

        # Set kernel buffers to 1 for both devices
        for dev in [self.dev1, self.dev2]:
            dev._rxadc.set_kernel_buffers_count(1)

    @property
    def rx_buffer_size(self):
        """rx_buffer_size: Size of receive buffer in samples for both devices"""
        return self.__rx_buffer_size_multi

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        """Set rx_buffer_size for both ADC devices"""
        self.__rx_buffer_size_multi = value
        self.dev1.rx_buffer_size = value
        self.dev2.rx_buffer_size = value

    @property
    def rx_enabled_channels(self):
        """rx_enabled_channels: List of enabled channels for both devices"""
        return {
            "dev1": self.dev1.rx_enabled_channels,
            "dev2": self.dev2.rx_enabled_channels,
        }

    @rx_enabled_channels.setter
    def rx_enabled_channels(self, value):
        """Set rx_enabled_channels for both devices

        Args:
            value: Either a list (applied to both devices) or a dict with 'dev1' and 'dev2' keys
        """
        if isinstance(value, dict):
            if "dev1" in value:
                self.dev1.rx_enabled_channels = value["dev1"]
            if "dev2" in value:
                self.dev2.rx_enabled_channels = value["dev2"]
        else:
            # Apply the same channel list to both devices
            self.dev1.rx_enabled_channels = value
            self.dev2.rx_enabled_channels = value

    def __rx_dma_arm(self):
        """Arm DMAs for synchronized capture"""
        for dev in [self.dev1, self.dev2]:
            if self._dma_show_arming:
                print(f"--DMA ARMING-- {dev._device_name}")
            dev.rx_sync_start = "arm"
            if self._dma_show_arming:
                print(f"--DMA ARMED-- {dev._device_name}")

    def __trigger_tdd_sync(self):
        """Trigger TDD synchronization pulse if TDD object is available"""
        if self.tddn:
            time.sleep(
                0.01
            )  # Short delay to ensure DMAs are armed before triggering sync
            self.tddn.sync_soft = 1

    def rx_destroy_buffer(self):
        """Destroy RX buffers for both devices"""
        for dev in [self.dev1, self.dev2]:
            dev.rx_destroy_buffer()

    def rx(self):
        """Receive synchronized data from both ADC devices

        This method:
        1. Arms both DMAs for synchronized capture
        2. Destroys and recreates buffers
        3. Triggers TDD sync (if tddn object was provided)
        4. Captures data from both devices

        Returns:
            tuple: (data_dev1, data_dev2)
                data_dev1: numpy array or list of arrays from device 1
                data_dev2: numpy array or list of arrays from device 2
        """
        if not self._rx_initialized:
            self._rx_initialized = True

        # Arm DMAs
        self.__rx_dma_arm()

        # Recreate all buffers for synchronized capture
        for dev in [self.dev1, self.dev2]:
            dev.rx_destroy_buffer()
            dev._rx_init_channels()

        # Trigger TDD sync if available
        self.__trigger_tdd_sync()

        # Capture data from both devices
        rx_data1 = self.dev1.rx()
        rx_data2 = self.dev2.rx()

        return rx_data1, rx_data2
