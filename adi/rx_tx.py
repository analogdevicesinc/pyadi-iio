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

import numpy as np
from adi.dds import dds
from adi.attribute import attribute
import iio


class phy(attribute):
    ctrl = []

    def __del__(self):
        self.ctrl = []


class rx(attribute):
    """ Buffer handling for receive devices """

    rxadc = []
    rx_channel_names = []
    rxbuf = None

    def __init__(self, rx_enabled_channels, rx_buffer_size=1024):
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
        if self.complex_data:
            if max(value) > ((self.num_rx_channels) / 2 - 1):
                raise Exception("RX mapping exceeds available channels")
        else:
            if max(value) > ((self.num_rx_channels) - 1):
                raise Exception("RX mapping exceeds available channels")
        self.__rx_enabled_channels = value

    @property
    def num_rx_channels_enabled(self):
        return len(self.__rx_enabled_channels)

    def __del__(self):
        self.rxbuf = []
        self.rxadc = []

    def init_channels(self):
        if self.complex_data:
            for map in self.rx_enabled_channels:
                v = self.rxadc.find_channel(self.rx_channel_names[map * 2])
                v.enabled = True
                v = self.rxadc.find_channel(self.rx_channel_names[map * 2 + 1])
                v.enabled = True
        else:
            for map in self.rx_enabled_channels:
                v = self.rxadc.find_channel(self.rx_channel_names[map])
                v.enabled = True
        self.rxbuf = iio.Buffer(self.rxadc, self.__rx_buffer_size, False)

    def rx_complex(self):
        if not self.rxbuf:
            self.init_channels(False)
        self.rxbuf.refill()
        data = self.rxbuf.read()
        x = np.frombuffer(data, dtype=np.int16)
        indx = 0
        sig = []
        l = len(self.rx_enabled_channels) * 2
        for c in range(l // 2):
            sig.append(x[indx::l] + 1j * x[indx + 1 :: l])
            indx = indx + 2
        # Don't return list if a single channel
        if indx == 2:
            return sig[0]
        return sig

    def rx_non_complex(self):
        if not self.rxbuf:
            self.init_channels(False)
        self.rxbuf.refill()
        data = self.rxbuf.read()
        x = np.frombuffer(data, dtype=np.int16)
        indx = 0
        sig = []
        l = len(self.__rx_enabled_channels)
        for c in range(l):
            sig.append(x[c::l])
        # Don't return list if a single channel
        if self.__rx_enabled_channels == 1:
            return sig[0]
        return sig

    def rx(self):
        if self.complex_data:
            return self.rx_complex()
        else:
            return self.rx_non_complex()


class tx(dds, attribute):
    """ Buffer handling for receive devices """

    txdac = []
    tx_channel_names = []
    tx_buffer_size = 1024
    txbuf = None

    def __init__(self, tx_enabled_channels, tx_cyclic_buffer=False):
        self.tx_enabled_channels = tx_enabled_channels
        self.tx_cyclic_buffer = tx_cyclic_buffer
        dds.__init__(self)

    def __del__(self):
        self.txdac = []

    @property
    def tx_cyclic_buffer(self):
        """tx_cyclic_buffer: Enable cyclic buffer for TX"""
        return self.__tx_cyclic_buffer

    @tx_cyclic_buffer.setter
    def tx_cyclic_buffer(self, value):
        self.__tx_cyclic_buffer = value

    @property
    def num_tx_channels_enabled(self):
        return len(self.tx_enabled_channels)

    @property
    def tx_enabled_channels(self):
        """tx_enabled_channels: List of enabled channels (channel 1 is 0)"""
        return self.__tx_enabled_channels

    @tx_enabled_channels.setter
    def tx_enabled_channels(self, value):
        if self.complex_data:
            if max(value) > ((self.num_tx_channels) / 2 - 1):
                raise Exception("TX mapping exceeds available channels")
        else:
            if max(value) > ((self.num_tx_channels) - 1):
                raise Exception("TX mapping exceeds available channels")
        self.__tx_enabled_channels = value

    def init_channels(self):
        if self.complex_data:
            for map in self.tx_enabled_channels:
                v = self.txdac.find_channel(self.tx_channel_names[map * 2], True)
                v.enabled = True
                v = self.txdac.find_channel(self.tx_channel_names[map * 2 + 1], True)
                v.enabled = True
        else:
            for map in self.tx_enabled_channels:
                v = self.txdac.find_channel(self.tx_channel_names[map])
                v.enabled = True
        self.txbuf = iio.Buffer(
            self.txdac, self.tx_buffer_size, self.__tx_cyclic_buffer
        )

    def tx(self, data_np):
        if self.complex_data:
            if self.num_tx_channels_enabled == 1:
                data_np = [data_np]

            if len(data_np) != self.num_tx_channels_enabled:
                raise Exception("Not enough data provided for channel mapping")

            indx = 0
            l = self.num_tx_channels_enabled * 2
            data = np.empty(l * len(data_np[0]), dtype=np.int16)
            for chan in data_np:
                i = np.real(chan)
                q = np.imag(chan)
                data[indx::l] = i.astype(int)
                data[indx + 1 :: l] = q.astype(int)
                indx = indx + 2
        else:
            if self.num_tx_channels_enabled == 1:
                data_np = [data_np]
            indx = 0
            l = self.num_tx_channels_enabled
            iq = np.empty(l * len(data_np), dtype=np.int16)
            for chan in data_np:
                data[indx::l] = chan.astype(int)
                indx = indx + 1

        if not self.txbuf:
            self.disable_dds()
            self.tx_buff_length = len(data)
            self.init_channels(True)

        if len(data) != self.tx_buff_length:
            raise

        # Send data to buffer
        self.txbuf.write(bytearray(data))
        self.txbuf.push()


class rx_tx(rx, tx, phy):

    complex_data = False

    def __init__(self, rx_enabled_channels, tx_enabled_channels):
        self.num_rx_channels = len(self.rx_channel_names)
        self.num_tx_channels = len(self.tx_channel_names)
        rx.__init__(self, rx_enabled_channels)
        tx.__init__(self, tx_enabled_channels)

    def __del__(self):
        rx.__del__(self)
        tx.__del__(self)
        phy.__del__(self)

    def init_channels(self, istx=False):
        if istx:
            tx.init_channels(self)
        else:
            rx.init_channels(self)
