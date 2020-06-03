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

from abc import abstractproperty
from typing import List

import iio

import numpy as np
from adi.attribute import attribute
from adi.dds import dds


def enable_channel(channel):
    """ Enable IIO channel """
    channel.enabled = True


class Phy(attribute):  # pylint disable=R0903
    """ Control device handler """

    @abstractproperty
    def _ctrl(self) -> iio.Device:
        pass


class Meta(type):
    """ Rx and Tx metaclass
        This class is used to initialize contexts at startup
        and setup Rx and Tx appropriately
    """

    def __call__(cls, *args, **kwargs):
        instance = super().__call__(*args, **kwargs)
        tree = cls.mro()
        if any(x is Rx for x in tree):
            Rx.__init_rx__(instance)
        if any(x is Tx for x in tree):
            Tx.__init_tx__(instance)
        return instance


class Rx(attribute, metaclass=Meta):
    """ Buffer handling for receive devices """

    @abstractproperty
    def _rxadc(self) -> iio.Device:
        pass

    @abstractproperty
    def _rx_channel_names(self) -> List[str]:
        pass

    _complex_data = False
    _rx_data_type = np.int16
    _rx_data_si_type = np.int16
    _rx_mask = 0x0000
    _rx_shift = 0
    _num_rx_channels = 0
    rx_output_type = "raw"
    __rxbuf = None
    __rx_buffer_size = 16
    __rx_enabled_channels = []
    _rx_unbuffered_data = False

    def __init_rx__(self, rx_buffer_size=1024):
        chan_per_out_chan = 2 if self._complex_data else 1
        rx_enabled_channels = list(
            range(len(self._rx_channel_names) // chan_per_out_chan)
        )
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

    def rx_destroy_buffer(self):
        """rx_destroy_buffer: Clears RX buffer"""
        self.__rxbuf = None

    def __del__(self):
        if self.__rxbuf:
            del self.__rxbuf

    def _rx_init_channels(self):
        for chan_name in self._rx_channel_names:
            chan = self._rxadc.find_channel(chan_name)
            chan.enabled = False

        if self._complex_data:
            for chan_index in self.rx_enabled_channels:
                enable_channel(
                    self._rxadc.find_channel(self._rx_channel_names[chan_index * 2])
                )
                enable_channel(
                    self._rxadc.find_channel(self._rx_channel_names[chan_index * 2 + 1])
                )
        else:
            for chan_index in self.rx_enabled_channels:
                enable_channel(
                    self._rxadc.find_channel(self._rx_channel_names[chan_index])
                )
        self.__rxbuf = iio.Buffer(self._rxadc, self.__rx_buffer_size, False)

    def __rx_unbuffered_data(self):
        channel_data = []
        chan_type = (
            self._rx_data_si_type if self.rx_output_type == "SI" else self._rx_data_type
        )
        for _ in range(len(self.rx_enabled_channels)):
            channel_data.append(np.zeros(self.rx_buffer_size, dtype=chan_type))

        # Get scalers first
        if self.rx_output_type == "SI":
            rx_scale = []
            rx_offset = []
            for i in self.rx_enabled_channels:
                chan = self._rxadc.find_channel(self._rx_channel_names[i])
                if "scale" in chan.attrs:
                    scale = self._get_iio_attr(
                        self._rx_channel_names[i], "scale", False
                    )
                else:
                    scale = 1.0

                if "offset" in chan.attrs:
                    offset = self._get_iio_attr(
                        self._rx_channel_names[i], "offset", False
                    )
                else:
                    offset = 0.0
                rx_scale.append(scale)
                rx_offset.append(offset)

        for samp in range(self.rx_buffer_size):
            for channel_data_index, channel_index in enumerate(
                self.rx_enabled_channels
            ):
                raw_data = self._get_iio_attr(
                    self._rx_channel_names[channel_index], "raw", False, self._rxadc
                )
                if self.rx_output_type == "SI":
                    channel_data[channel_data_index][samp] = (
                        rx_scale[channel_data_index] * raw_data
                        + rx_offset[channel_data_index]
                    )
                else:
                    channel_data[channel_data_index][samp] = raw_data

        return channel_data

    def __rx_complex(self):
        if not self.__rxbuf:
            self._rx_init_channels()
        self.__rxbuf.refill()
        data_coded = self.__rxbuf.read()
        data = np.frombuffer(data_coded, dtype=self._rx_data_type)
        indx = 0
        sig = []
        stride = len(self.rx_enabled_channels) * 2
        for _ in range(stride // 2):
            sig.append(data[indx::stride] + 1j * data[indx + 1 :: stride])
            indx = indx + 2
        # Don't return list if a single channel
        if indx == 2:
            return sig[0]
        return sig

    def __rx_non_complex(self):
        if not self.__rxbuf:
            self._rx_init_channels()
        self.__rxbuf.refill()
        data_coded = self.__rxbuf.read()
        data = np.frombuffer(data_coded, dtype=self._rx_data_type)
        if self._rx_mask != 0:
            data = np.bitwise_and(data, self._rx_mask)
        if self._rx_shift > 0:
            data = np.right_shift(data, self._rx_shift)
        elif self._rx_shift < 0:
            data = np.left_shift(data, -(self._rx_shift))

        sig = []
        stride = len(self.rx_enabled_channels)

        if self.rx_output_type == "raw":
            for offset in range(stride):
                sig.append(data[offset::stride])
        elif self.rx_output_type == "SI":
            rx_scale = []
            rx_offset = []
            for i in self.rx_enabled_channels:
                chan = self._rxadc.find_channel(self._rx_channel_names[i])
                if "scale" in chan.attrs:
                    scale = self._get_iio_attr(
                        self._rx_channel_names[i], "scale", False
                    )
                else:
                    scale = 1.0

                if "offset" in chan.attrs:
                    offset = self._get_iio_attr(
                        self._rx_channel_names[i], "offset", False
                    )
                else:
                    offset = 0.0
                rx_scale.append(scale)
                rx_offset.append(offset)

            for offset in range(stride):
                raw = data[offset::stride]
                sig.append(raw * rx_scale[offset] + rx_offset[offset])
        else:
            raise Exception("rx_output_type undefined")

        # Don't return list if a single channel
        if len(self.rx_enabled_channels) == 1:
            return sig[0]
        return sig

    def rx(self):  # pylint: disable=C0103
        """ Receive data from hardware buffers for each channel index in
            rx_enabled_channels.

            returns: type=numpy.array or list of numpy.array
                An array or list of arrays when more than one receive channel
                is enabled containing samples from a channel or set of channels.
                Data will be complex when using a complex data device.
        """
        if self._rx_unbuffered_data:
            return self.__rx_unbuffered_data()
        if self._complex_data:
            return self.__rx_complex()
        return self.__rx_non_complex()


class Tx(dds, attribute, metaclass=Meta):
    """ Buffer handling for transmit devices """

    @abstractproperty
    def _txdac(self) -> iio.Device:
        pass

    @abstractproperty
    def _tx_channel_names(self) -> List[str]:
        pass

    _tx_buffer_size = 1024
    _complex_data = False
    _num_tx_channels = 0
    __txbuf = None
    __tx_enabled_channels: List[int] = []
    __tx_cyclic_buffer = False

    def __init_tx__(self, tx_cyclic_buffer=False):
        chan_per_out_chan = 2 if self._complex_data else 1
        tx_enabled_channels = list(
            range(len(self._tx_channel_names) // chan_per_out_chan)
        )
        self._num_tx_channels = len(self._tx_channel_names)
        self.tx_enabled_channels = tx_enabled_channels
        self.tx_cyclic_buffer = tx_cyclic_buffer
        dds.__init__(self)

    def __del__(self):
        if self.__txbuf:
            del self.__txbuf

    @property
    def tx_cyclic_buffer(self):
        """tx_cyclic_buffer: Enable cyclic buffer for TX"""
        return self.__tx_cyclic_buffer

    @tx_cyclic_buffer.setter
    def tx_cyclic_buffer(self, value):
        if self.__txbuf:
            raise Exception(
                "TX buffer already created, buffer must be "
                "destroyed then recreated to modify tx_cyclic_buffer"
            )
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

    def tx_destroy_buffer(self):
        """tx_destroy_buffer: Clears TX buffer"""
        self.__txbuf = None

    def _tx_init_channels(self):
        if self._complex_data:
            for chan_index in self.tx_enabled_channels:
                enable_channel(
                    self._txdac.find_channel(
                        self._tx_channel_names[chan_index * 2], True
                    )
                )
                enable_channel(
                    self._txdac.find_channel(
                        self._tx_channel_names[chan_index * 2 + 1], True
                    )
                )
        else:
            for chan_index in self.tx_enabled_channels:
                enable_channel(
                    self._txdac.find_channel(self._tx_channel_names[chan_index], True)
                )
        self.__txbuf = iio.Buffer(
            self._txdac, self._tx_buffer_size, self.__tx_cyclic_buffer
        )

    def tx(self, data_np):  # pylint: disable=C0103
        """ Transmit data to hardware buffers for each channel index in
            tx_enabled_channels.

            args: type=numpy.array or list of numpy.array
                An array or list of arrays when more than one transmit channel
                is enabled containing samples from a channel or set of channels.
                Data must be complex when using a complex data device.
        """
        if self.__txbuf and self.tx_cyclic_buffer:
            raise Exception(
                "TX buffer has been submitted in cyclic mode. "
                "To push more data the tx buffer must be destroyed first."
            )

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
                q = np.imag(chan)  # pylint: disable=C0103
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
                "Buffer length different than data length. "
                "Cannot change buffer length on the fly"
            )

        # Send data to buffer
        self.__txbuf.write(bytearray(data))
        self.__txbuf.push()


class RxTx(Rx, Tx, Phy):  # pylint: disable=W0223
    """ Combined RX and TX base class for DDS and buffer management"""

    def __del__(self):
        Rx.__del__(self)
        Tx.__del__(self)
