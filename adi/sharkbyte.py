# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.hmcad15xx import hmcad15xx
from adi.sync_start import sync_start
import time


class sharkbyte(sync_start):
    """Sharkbyte Multi-ADC Manager

    Manages synchronized data capture from two HMCAD15xx ADCs using
    software-based DMA synchronization via util_ext_sync.

    Parameters:
        uri: type=string
            URI of the hardware platform (e.g., "ip:192.168.2.1")
        device1_name: type=string
            Device name for first ADC (default: "axi_adc1_hmcad15xx")
            This device's util_ext_sync module provides the sync signal for both DMAs
        device2_name: type=string
            Device name for second ADC (default: "axi_adc2_hmcad15xx")
    """

    __rx_buffer_size_multi = 2 ** 14

    def __init__(
        self,
        uri="",
        device1_name="axi_adc1_hmcad15xx",
        device2_name="axi_adc2_hmcad15xx",
        show_dma_arming = False
    ):
        """Initialize sharkbyte multi-ADC manager"""

        self._dma_show_arming = show_dma_arming

        # Create both ADC devices
        self.dev1 = hmcad15xx(uri=uri, device_name=device1_name)
        self.dev2 = hmcad15xx(uri=uri, device_name=device2_name)

        # Set _rxadc for sync_start base class to use dev1
        self._rxadc = self.dev1._rxadc

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

    def rx_destroy_buffer(self):
        """Destroy RX buffers for both devices"""
        for dev in [self.dev1, self.dev2]:
            dev.rx_destroy_buffer()

    def rx(self):
        """Receive synchronized data from both ADC devices

        This method follows the ad9084 sync_start workflow:
        1. ARM dev1's DMA (controls both DMAs via util_ext_sync)
        2. Verify armed state
        3. Destroy and recreate buffers
        4. TRIGGER_MANUAL to start synchronized capture
        5. Verify auto-disarmed state
        6. Capture data from both devices

        Returns:
            tuple: (data_dev1, data_dev2)
                data_dev1: numpy array or list of arrays from device 1
                data_dev2: numpy array or list of arrays from device 2
        """

        # Step 1: Destroy and recreate buffers
        if self._dma_show_arming:
            print("--DESTROYING/RECREATING BUFFERS--", flush=True)
        for dev in [self.dev1, self.dev2]:
            dev.rx_destroy_buffer()
            dev._rx_init_channels()

        # Step 2: ARM dev1's DMA
        if self._dma_show_arming:
            print("--ARMING dev1--", flush=True)
        self.rx_sync_start = "arm"

        # Step 3: Verify armed state
        dev1_state = self.rx_sync_start
        if self._dma_show_arming:
            print(f"--ARM CHECK-- dev1: {dev1_state}", flush=True)

        if dev1_state != "arm":
            raise Exception(f"Unexpected SYNC status after ARM: dev1={dev1_state}")

        # Step 4: TRIGGER_MANUAL
        if self._dma_show_arming:
            print("--TRIGGER_MANUAL on dev1--", flush=True)
        self.rx_sync_start = "trigger_manual"

        # Step 5: Capture data
        if self._dma_show_arming:
            print("--CAPTURING DATA--", flush=True)
        rx_data1 = self.dev1.rx()
        rx_data2 = self.dev2.rx()

        if self._dma_show_arming:
            print("--CAPTURE COMPLETE--", flush=True)

        # Step 6: Explicitly disarm to reset state for next capture
        if self._dma_show_arming:
            print("--DISARMING after capture--", flush=True)
        self.rx_sync_start = "disarm"

        return rx_data1, rx_data2
