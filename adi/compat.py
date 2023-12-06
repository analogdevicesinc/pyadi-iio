# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
"""Compatibility module for libiio v1.X."""

from typing import Any

import iio


class compat_libiio:
    """Compatibility class for libiio v1.X."""

    def __is_libiio_v1(self):
        """Check is we are using >= v1.X."""
        v = iio.version
        return v[0] >= 1

    def _setup_v1_rx(self):
        """Setup for libiio v1.X RX side."""
        self._rx_buffer_mask = None
        self.__rx_stream = None
        self._rx_buffer_num_blocks = 4

    def _setup_v1_tx(self):
        """Setup for libiio v1.X TX side."""
        self._tx_buffer_mask = None
        self.__tx_stream = None
        self._tx_buffer_num_blocks = 4

    def __getattr__(self, __name: str) -> Any:
        if __name in ["_rx_init_channels", "_tx_init_channels", "__tx_buffer_push"]:
            if self.__is_libiio_v1():
                return getattr(self, f"_{__name}_v1")
            else:
                return getattr(self, f"_{__name}")

    def _rx_init_channels_v1(self):
        if not self._rx_buffer_mask:
            self._rx_buffer_mask = iio.ChannelsMask(self._rxadc)

        channels = []
        if self._complex_data:
            for m in self.rx_enabled_channels:
                v = self._rxadc.find_channel(self._rx_channel_names[m * 2])
                channels.append(v)
                v = self._rxadc.find_channel(self._rx_channel_names[m * 2 + 1])
                channels.append(v)
        else:
            for m in self.rx_enabled_channels:
                v = self._rxadc.find_channel(self._rx_channel_names[m])
                channels.append(v)

        self._rx_buffer_mask.channels = channels

        self.__rxbuf = iio.Buffer(self._rxadc, self._rx_buffer_mask)
        self.__rx_stream = iio.Stream(
            buffer=self.__rxbuf,
            nb_blocks=self._rx_buffer_num_blocks,
            samples_count=self.rx_buffer_size,
        )

    def _tx_init_channels_v1(self):
        if not self._tx_buffer_mask:
            self._tx_buffer_mask = iio.ChannelsMask(self._txdac)

        channels = []
        if self._complex_data:
            for m in self.tx_enabled_channels:
                v = self._txdac.find_channel(self._tx_channel_names[m * 2], True)
                channels.append(v)
                v = self._txdac.find_channel(self._tx_channel_names[m * 2 + 1], True)
                channels.append(v)
        else:
            for m in self.tx_enabled_channels:
                v = self._txdac.find_channel(self._tx_channel_names[m], True)
                channels.append(v)

        self._tx_buffer_mask.channels = channels

        self.__txbuf = iio.Buffer(self._txdac, self._tx_buffer_mask)
        self.__block_tx = iio.Block(self.__txbuf, self._tx_buffer_size)

    def __tx_buffer_push_v1(self, data):
        """Push data to TX buffer.

        data: bytearray
        """
        self.__block_tx.write(data)
        self.__block_tx.enqueue(None, self.__tx_cyclic_buffer)
        self.__txbuf.enabled = True
