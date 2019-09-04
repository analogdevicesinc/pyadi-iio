# Copyright (C) 2019 Analog Devices, Inc.
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

from typing import List

import iio

import numpy as np
from adi.attribute import attribute
from adi.dds import dds


class phy(attribute):
    _ctrl: iio.Device = []

    def __del__(self):
        self._ctrl = []


class rx(attribute):
    """ Buffer handling for receive devices """

    _rxadc: iio.Device = []
    _rx_channel_names: List[str] = []
    _complex_data = False
    __rxbuf = None

    def __init__(self, rx_buffer_size=1024):
        if self._complex_data:
            N = 2
        else:
            N = 1
        rx_enabled_channels = list(range(len(self._rx_channel_names) // N))
        self._num_rx_channels = len(self._rx_channel_names)
        self.rx_enabled_channels = rx_enabled_channels
        self.rx_buffer_size = rx_buffer_size

    @property
    def rx_buffer_size(self):
        """rx_buffer_size: Size of receive buffer in samples"""
        return self.__rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self.__rx_buffer_size = value

    @property
    def rx_enabled_channels(self):
        """rx_enabled_channels: List of enabled channels (channel 1 is 0)"""
        return self.__rx_enabled_channels

    @rx_enabled_channels.setter
    def rx_enabled_channels(self, value):
        if self._complex_data:
            if max(value) > ((self._num_rx_channels) / 2 - 1):
                raise Exception("RX mapping exceeds available channels")
        else:
            if max(value) > ((self._num_rx_channels) - 1):
                raise Exception("RX mapping exceeds available channels")
        self.__rx_enabled_channels = value

    @property
    def _num_rx_channels_enabled(self):
        return len(self.__rx_enabled_channels)

    def __del__(self):
        self.__rxbuf = []
        self._rxadc = []

    def _rx_init_channels(self):
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
        self.__rxbuf = iio.Buffer(self._rxadc, self.__rx_buffer_size, False)

    def __rx_complex(self):
        if not self.__rxbuf:
            self._rx_init_channels()
        self.__rxbuf.refill()
        data = self.__rxbuf.read()
        x = np.frombuffer(data, dtype=np.int16)
        indx = 0
        sig = []
        stride = len(self.rx_enabled_channels) * 2
        for _ in range(stride // 2):
            sig.append(x[indx::stride] + 1j * x[indx + 1 :: stride])
            indx = indx + 2
        # Don't return list if a single channel
        if indx == 2:
            return sig[0]
        return sig

    def __rx_non_complex(self):
        if not self.__rxbuf:
            self._rx_init_channels()
        self.__rxbuf.refill()
        data = self.__rxbuf.read()
        x = np.frombuffer(data, dtype=np.int16)
        sig = []
        stride = len(self.rx_enabled_channels)
        for c in range(stride):
            sig.append(x[c::stride])
        # Don't return list if a single channel
        if len(self.rx_enabled_channels) == 1:
            return sig[0]
        return sig

    def rx(self):
        if self._complex_data:
            return self.__rx_complex()
        else:
            return self.__rx_non_complex()


class tx(dds, attribute):
    """ Buffer handling for transmit devices """

    _tx_buffer_size = 1024
    _txdac: iio.Device = []
    _tx_channel_names: List[str] = []
    _complex_data = False
    __txbuf = None

    def __init__(self, tx_cyclic_buffer=False):
        if self._complex_data:
            N = 2
        else:
            N = 1
        tx_enabled_channels = list(range(len(self._tx_channel_names) // N))
        self._num_tx_channels = len(self._tx_channel_names)
        self.tx_enabled_channels = tx_enabled_channels
        self.tx_cyclic_buffer = tx_cyclic_buffer
        dds.__init__(self)

    def __del__(self):
        self._txdac = []

    @property
    def tx_cyclic_buffer(self):
        """tx_cyclic_buffer: Enable cyclic buffer for TX"""
        return self.__tx_cyclic_buffer

    @tx_cyclic_buffer.setter
    def tx_cyclic_buffer(self, value):
        self.__tx_cyclic_buffer = value

    @property
    def _num_tx_channels_enabled(self):
        return len(self.tx_enabled_channels)

    @property
    def tx_enabled_channels(self):
        """tx_enabled_channels: List of enabled channels (channel 1 is 0)"""
        return self.__tx_enabled_channels

    @tx_enabled_channels.setter
    def tx_enabled_channels(self, value):
        if self._complex_data:
            if max(value) > ((self._num_tx_channels) / 2 - 1):
                raise Exception("TX mapping exceeds available channels")
        else:
            if max(value) > ((self._num_tx_channels) - 1):
                raise Exception("TX mapping exceeds available channels")
        self.__tx_enabled_channels = value

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
        self.__txbuf = iio.Buffer(
            self._txdac, self._tx_buffer_size, self.__tx_cyclic_buffer
        )

    def tx(self, data_np):
        if self._complex_data:
            if self._num_tx_channels_enabled == 1:
                data_np = [data_np]

            if len(data_np) != self._num_tx_channels_enabled:
                raise Exception("Not enough data provided for channel mapping")

            indx = 0
            stride = self._num_tx_channels_enabled * 2
            data = np.empty(stride * len(data_np[0]), dtype=np.int16)
            for chan in data_np:
                i = np.real(chan)
                q = np.imag(chan)
                data[indx::stride] = i.astype(int)
                data[indx + 1 :: stride] = q.astype(int)
                indx = indx + 2
        else:
            if self._num_tx_channels_enabled == 1:
                data_np = [data_np]

            if len(data_np) != self._num_tx_channels_enabled:
                raise Exception("Not enough data provided for channel mapping")

            indx = 0
            stride = self._num_tx_channels_enabled
            data = np.empty(stride * len(data_np[0]), dtype=np.int16)
            for chan in data_np:
                data[indx::stride] = chan.astype(int)
                indx = indx + 1

        if not self.__txbuf:
            self.disable_dds()
            self._tx_buffer_size = len(data) // stride
            self._tx_init_channels()

        if len(data) // stride != self._tx_buffer_size:
            raise Exception(
                "Buffer length different than data length. Cannot change buffer length on the fly"
            )

        # Send data to buffer
        self.__txbuf.write(bytearray(data))
        self.__txbuf.push()


class rx_tx(rx, tx, phy):
    def __init__(self):
        rx.__init__(self)
        tx.__init__(self)

    def __del__(self):
        rx.__del__(self)
        tx.__del__(self)
        phy.__del__(self)
