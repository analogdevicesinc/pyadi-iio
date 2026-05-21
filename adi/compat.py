# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
"""Compatibility module for libiio v1.X."""

from typing import List, Union

import iio
import numpy as np


def _is_libiio_v1() -> bool:
    """Check is we are using >= v1.X."""
    v = iio.version
    return v[0] >= 1


class compat_libiio_v1_rx:
    """Compatibility class for libiio v1.X RX."""

    _rx_buffer_mask = None
    _rx_stream = None
    _rx_buffer_num_blocks = 4

    def _rx_init_channels(self):
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

        self._rxbuf = self._rxadc.get_buffer()
        self._rx_stream = iio.Stream(
            buffer=self._rxbuf,
            mask=self._rx_buffer_mask,
            samples_count=self.rx_buffer_size,
            nb_blocks=self._rx_buffer_num_blocks,
        )

    def _rx_buffered_data(self):
        if not self._rx_stream:
            self._rx_init_channels()

        block = next(self._rx_stream)

        data_channel_interleaved = []
        for chan in self._rx_buffer_mask.channels:
            bytearray_data = chan.read(block)
            # create format strings
            df = chan.data_format
            fmt = ("i" if df.is_signed is True else "u") + str(df.length // 8)
            fmt = ">" + fmt if df.is_be else fmt
            data_channel_interleaved.append(np.frombuffer(bytearray_data, dtype=fmt))

        return data_channel_interleaved


class compat_libiio_v1_tx:
    """Compatibility class for libiio v1.X TX."""

    _tx_buffer_mask = None
    _tx_stream = None
    _tx_buffer_num_blocks = 4
    _tx_block = None
    _tx_buf_stream = None

    def _tx_init_channels(self):
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

        self._txbuf = self._txdac.get_buffer()
        if not self._tx_cyclic_buffer:
            self._tx_stream = iio.Stream(
                buffer=self._txbuf,
                mask=self._tx_buffer_mask,
                samples_count=self._tx_buffer_size,
                nb_blocks=self._tx_buffer_num_blocks,
            )
        else:
            self._tx_buf_stream = self._txbuf.open(self._tx_buffer_mask)
            self._tx_block = iio.Block(self._tx_buf_stream, self._tx_buffer_size)

    def _tx_buffer_push(self, data):
        """Push data to TX buffer.

        data: bytearray
        """
        if self._tx_cyclic_buffer:
            self._tx_block.write(data)
            self._tx_block.enqueue(None, self._tx_cyclic_buffer)
            self._tx_buf_stream.started = True
        else:
            block = next(self._tx_stream)
            block.write(data)


class compat_libiio_v0_rx:
    """Compatibility class for libiio v0.X RX."""

    def _rx_init_channels(self):
        for m in self._rx_channel_names:
            v = self._rxadc.find_channel(m)
            if not v:
                raise Exception(f"Channel {m} not found")
            v.enabled = False

        if self._complex_data:
            for m in self.rx_enabled_channels:
                v = self._rxadc.find_channel(self._rx_channel_names[m * 2])
                v.enabled = True
                v = self._rxadc.find_channel(self._rx_channel_names[m * 2 + 1])
                v.enabled = True
        else:
            for m in self.rx_enabled_channels:
                v = self._rxadc.find_channel(self._rx_channel_names[m])
                v.enabled = True
        self._rxbuf = iio.Buffer(self._rxadc, self._rx_buffer_size, False)

    def _rx_buffered_data(self) -> Union[List[np.ndarray], np.ndarray]:
        """_rx_buffered_data: Read data from RX buffer

        Returns:
            List of numpy arrays containing the data from the RX buffer that are
            channel interleaved
        """
        if not self._rxbuf:
            self._rx_init_channels()
        try:
            self._rxbuf.refill()
        except Exception:
            # libiio 0.x's `iio_buffer_destroy` calls `network_close` which
            # reads `iio_device_get_id(dev)` to build the "CLOSE <dev>" iiod
            # command. If the owning iio.Context is finalized before the
            # iio.Buffer — which can happen under Python's cycle collector
            # when refs form cycles (pytest fixtures, traceback locals,
            # etc.) — that id pointer dangles and the command is built
            # from freed memory. We've caught it as a SIGSEGV in the
            # buffer destructor; see iiod-client.c:651 +
            # network.c:network_close + buffer.c:106.
            #
            # The fix is to destroy the buffer NOW, while the device is
            # still alive, instead of letting it ride along to gc time
            # where ordering is undefined.
            del self._rxbuf
            self._rxbuf = None
            raise

        data_channel_interleaved = []
        ecn = []
        if self._complex_data:
            for m in self.rx_enabled_channels:
                ecn.extend(
                    (self._rx_channel_names[m * 2], self._rx_channel_names[m * 2 + 1])
                )
        else:
            ecn = [self._rx_channel_names[m] for m in self.rx_enabled_channels]

        for name in ecn:
            chan = self._rxadc.find_channel(name)
            bytearray_data = chan.read(self._rxbuf)  # Do local type conversion
            # create format strings
            df = chan.data_format
            fmt = ("i" if df.is_signed is True else "u") + str(df.length // 8)
            fmt = ">" + fmt if df.is_be else fmt
            data_channel_interleaved.append(np.frombuffer(bytearray_data, dtype=fmt))

        return data_channel_interleaved


class compat_libiio_v0_tx:
    """Compatibility class for libiio v0.X TX."""

    def _tx_init_channels(self):
        if self._complex_data:
            for m in self.tx_enabled_channels:
                v = self._txdac.find_channel(self._tx_channel_names[m * 2], True)
                v.enabled = True
                v = self._txdac.find_channel(self._tx_channel_names[m * 2 + 1], True)
                v.enabled = True
        else:
            for m in self.tx_enabled_channels:
                v = self._txdac.find_channel(self._tx_channel_names[m], True)
                v.enabled = True
        self._txbuf = iio.Buffer(
            self._txdac, self._tx_buffer_size, self._tx_cyclic_buffer
        )

    def _tx_buffer_push(self, data):
        self._txbuf.write(bytearray(data))
        self._txbuf.push()
