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

from abc import ABCMeta, abstractmethod
from typing import List, Union

import iio

import numpy as np
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.dds import dds


class phy(attribute):
    _ctrl: iio.Device = []

    def __del__(self):
        self._ctrl = []


class rx_tx_common(attribute):
    """Common functions for RX and TX"""

    def _annotate(self, data, cnames: List[str], echans: List[int]):
        return {cnames[ec]: data[i] for i, ec in enumerate(echans)}


class rx(rx_tx_common):
    """Buffer handling for receive devices"""

    _rxadc: iio.Device = []
    _rx_channel_names: List[str] = []
    _complex_data = False
    _rx_data_type = np.int16
    _rx_data_si_type = np.int16
    _rx_mask = 0x0000
    _rx_shift = 0
    __rx_buffer_size = 1024
    __rx_enabled_channels = [0]
    _rx_output_type = "raw"
    __rxbuf = None
    _rx_unbuffered_data = False
    _rx_annotated = False

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
    def rx_channel_names(self) -> List[str]:
        """rx_channel_names: List of RX channel names"""
        return self._rx_channel_names

    @property
    def rx_annotated(self) -> bool:
        """rx_annotated: Set output data from rx() to be annotated"""
        return self._rx_annotated

    @rx_annotated.setter
    def rx_annotated(self, value: bool):
        """rx_annotated: Set output data from rx() to be annotated"""
        self._rx_annotated = bool(value)

    @property
    def rx_output_type(self) -> str:
        """rx_output_type: Set output data type from rx()"""
        return self._rx_output_type

    @rx_output_type.setter
    def rx_output_type(self, value: str):
        """rx_output_type: Set output data type from rx()"""
        if value not in ["raw", "SI"]:
            raise ValueError(f"Invalid rx_output_type: {value}. Must be raw or SI")
        self._rx_output_type = value

    @property
    def rx_buffer_size(self):
        """rx_buffer_size: Size of receive buffer in samples"""
        return self.__rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self.__rx_buffer_size = value

    @property
    def rx_enabled_channels(self) -> List[int]:
        """rx_enabled_channels: List of enabled channels (channel 1 is 0)

        Either a list of channel numbers or channel names can be used to set
        rx_enabled_channels. When channel names are used, they will be
        translated to channel numbers.
        """
        return self.__rx_enabled_channels

    @rx_enabled_channels.setter
    def rx_enabled_channels(self, value: Union[List[int], List[str]]):
        """rx_enabled_channels: List of enabled channels (channel 1 is 0)

        Either a list of channel numbers or channel names can be used to set
        rx_enabled_channels. When channel names are used, they will be
        translated to channel numbers.
        """
        if not value:
            raise Exception("rx_enabled_channels cannot be empty")
        if not isinstance(value, list):
            raise Exception("rx_enabled_channels must be a list")
        if not all(isinstance(x, int) for x in value) and not all(
            isinstance(x, str) for x in value
        ):
            raise Exception(
                "rx_enabled_channels must be a list of integers or "
                + "list of channel names",
            )

        if isinstance(value[0], str):
            indxs = []
            for cname in value:
                if cname not in self._rx_channel_names:
                    raise Exception(
                        f"Invalid channel name: {cname}. Must be one of {self._rx_channel_names}"
                    )
                indxs.append(self._rx_channel_names.index(cname))

            value = sorted(list(set(indxs)))
        else:
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
        self.__rxbuf = []
        if hasattr("self", "_rxadc") and self._rxadc:
            for m in self._rx_channel_names:
                v = self._rxadc.find_channel(m)
                v.enabled = False
        self._rxadc = []

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
        self.__rxbuf = iio.Buffer(self._rxadc, self.__rx_buffer_size, False)

    def __rx_unbuffered_data(self):
        x = []
        t = (
            self._rx_data_si_type
            if self._rx_output_type == "SI"
            else self._rx_data_type
        )
        for _ in range(len(self.rx_enabled_channels)):
            x.append(np.zeros(self.rx_buffer_size, dtype=t))

        # Get scalers first
        if self._rx_output_type == "SI":
            rx_scale = []
            rx_offset = []
            for i in self.rx_enabled_channels:
                v = self._rxadc.find_channel(self._rx_channel_names[i])
                if "scale" in v.attrs:
                    scale = self._get_iio_attr(
                        self._rx_channel_names[i], "scale", False
                    )
                else:
                    scale = 1.0

                if "offset" in v.attrs:
                    offset = self._get_iio_attr(
                        self._rx_channel_names[i], "offset", False
                    )
                else:
                    offset = 0.0
                rx_scale.append(scale)
                rx_offset.append(offset)

        for samp in range(self.rx_buffer_size):
            for i, m in enumerate(self.rx_enabled_channels):
                s = self._get_iio_attr(
                    self._rx_channel_names[m], "raw", False, self._rxadc
                )
                if self._rx_output_type == "SI":
                    x[i][samp] = rx_scale[i] * s + rx_offset[i]
                else:
                    x[i][samp] = s

        return x

    def __rx_complex(self):
        if not self.__rxbuf:
            self._rx_init_channels()
        self.__rxbuf.refill()
        chan = self._rxadc.find_channel(
            self._rx_channel_names[self.rx_enabled_channels[0]]
        )
        data = chan.read(self.__rxbuf)

        x = np.frombuffer(data, dtype=self._rx_data_type)
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

    def __multi_type_rx(self, data):
        """Process buffers with multiple data types"""
        # Process each channel at a time
        channel_bytes = []
        curated_rx_type = []
        for en_ch in self.rx_enabled_channels:
            channel_bytes += [np.dtype(self._rx_data_type[en_ch]).itemsize]
            curated_rx_type += [self._rx_data_type[en_ch]]
        offset = 0
        stride = sum(channel_bytes)
        sig = []
        for indx, chan_bytes in enumerate(channel_bytes):
            bar = bytearray()
            for bytesI in range(offset, len(data), stride):
                bar.extend(data[bytesI : bytesI + chan_bytes])

            sig.append(np.frombuffer(bar, dtype=curated_rx_type[indx]))
            offset += chan_bytes
        return sig

    def __rx_non_complex(self):
        if not self.__rxbuf:
            self._rx_init_channels()
        self.__rxbuf.refill()
        chan = self._rxadc.find_channel(
            self._rx_channel_names[self.rx_enabled_channels[0]]
        )
        data = chan.read(self.__rxbuf)

        if isinstance(self._rx_data_type, list):
            return self.__multi_type_rx(data)

        x = np.frombuffer(data, dtype=self._rx_data_type)
        if self._rx_mask != 0:
            x = np.bitwise_and(x, self._rx_mask)
        if self._rx_shift > 0:
            x = np.right_shift(x, self._rx_shift)
        elif self._rx_shift < 0:
            x = np.left_shift(x, -(self._rx_shift))

        sig = []
        stride = len(self.rx_enabled_channels)

        if self._rx_output_type == "raw":
            for c in range(stride):
                sig.append(x[c::stride])
        elif self._rx_output_type == "SI":
            rx_scale = []
            rx_offset = []
            for i in self.rx_enabled_channels:
                v = self._rxadc.find_channel(self._rx_channel_names[i])
                if "scale" in v.attrs:
                    scale = self._get_iio_attr(
                        self._rx_channel_names[i], "scale", False
                    )
                else:
                    scale = 1.0

                if "offset" in v.attrs:
                    offset = self._get_iio_attr(
                        self._rx_channel_names[i], "offset", False
                    )
                else:
                    offset = 0.0
                rx_scale.append(scale)
                rx_offset.append(offset)

            for c in range(stride):
                raw = x[c::stride]
                sig.append(raw * rx_scale[c] + rx_offset[c])
        else:
            raise Exception("_rx_output_type undefined")

        # Don't return list if a single channel
        if len(self.rx_enabled_channels) == 1:
            return sig[0]
        return sig

    def rx(self):
        """Receive data from hardware buffers for each channel index in
        rx_enabled_channels.

        returns: type=numpy.array or list of numpy.array
            An array or list of arrays when more than one receive channel
            is enabled containing samples from a channel or set of channels.
            Data will be complex when using a complex data device.
        """
        if self._rx_unbuffered_data:
            data = self.__rx_unbuffered_data()
        else:
            if self._complex_data:
                data = self.__rx_complex()
            else:
                data = self.__rx_non_complex()
        if self._rx_annotated:
            return self._annotate(
                data, self._rx_channel_names, self.rx_enabled_channels
            )
        return data


class tx(dds, rx_tx_common):
    """Buffer handling for transmit devices"""

    _tx_buffer_size = 1024
    _txdac: iio.Device = []
    _tx_channel_names: List[str] = []
    _complex_data = False
    __txbuf = None
    _output_byte_filename = "out.bin"
    _push_to_file = False

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
        self.__txbuf = []
        if hasattr("self", "_txdac") and self._txdac:
            for m in self._tx_channel_names:
                v = self._txdac.find_channel(m)
                v.enabled = False
        self._txdac = []

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
    def tx_channel_names(self):
        """tx_channel_names: Names of the transmit channels"""
        return self._tx_channel_names

    @property
    def tx_enabled_channels(self):
        """tx_enabled_channels: List of enabled channels (channel 1 is 0)

        Either a list of channel numbers or channel names can be used to set
        tx_enabled_channels. When channel names are used, they will be
        translated to channel numbers.
        """
        return self.__tx_enabled_channels

    @tx_enabled_channels.setter
    def tx_enabled_channels(self, value):
        """tx_enabled_channels: List of enabled channels (channel 1 is 0)

        Either a list of channel numbers or channel names can be used to set
        tx_enabled_channels. When channel names are used, they will be
        translated to channel numbers.
        """
        if not value:
            self.__tx_enabled_channels = value
            return
        if not isinstance(value, list):
            raise Exception("tx_enabled_channels must be a list")
        if not all(isinstance(x, int) for x in value) and not all(
            isinstance(x, str) for x in value
        ):
            raise Exception(
                "tx_enabled_channels must be a list of integers or "
                + "list of channel names",
            )

        if isinstance(value[0], str):
            indxs = []
            for cname in value:
                if cname not in self._tx_channel_names:
                    raise Exception(
                        f"Invalid channel name: {cname}. Must be one of {self._tx_channel_names}"
                    )
                indxs.append(self._tx_channel_names.index(cname))

            value = sorted(list(set(indxs)))
        else:
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

    def tx(self, data_np=None):
        """Transmit data to hardware buffers for each channel index in
        tx_enabled_channels.

        args: type=numpy.array or list of numpy.array
            An array or list of arrays when more than one transmit channel
            is enabled containing samples from a channel or set of channels.
            Data must be complex when using a complex data device.
        """
        if not self.__tx_enabled_channels and data_np:
            raise Exception(
                "When tx_enabled_channels is None or empty,"
                + " the input to tx() must be None or empty or not provided"
            )
        if not self.__tx_enabled_channels:
            # Set TX DAC to zero source
            for chan in self._txdac.channels:
                if chan.output:
                    chan.attrs["raw"].value = "0"
                    return
            raise Exception("No DDS channels found for TX, TX zeroing does not apply")

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
                "Buffer length different than data length. "
                "Cannot change buffer length on the fly"
            )

        # Send data to buffer
        if self._push_to_file:
            f = open(self._output_byte_filename, "ab")
            f.write(bytearray(data))
            f.close()
        else:
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


class shared_def(context_manager, metaclass=ABCMeta):
    """Shared components for rx and tx metaclasses."""

    _device_name = ""  # String available in context name

    @property
    @abstractmethod
    def _complex_data(self) -> None:
        """Data to/from device is quadrature (Complex).
        When True ADC channel pairs are used together and the
        rx method will generate complex data types.
        Raises:
            NotImplementedError: Method not implemented
        """
        raise NotImplementedError  # pragma: no cover

    @property
    @abstractmethod
    def _control_device_name(self) -> None:
        """Name of driver used for primary attribute control.
        This is the default IIO device used to address properties
        """
        raise NotImplementedError  # pragma: no cover

    def __handle_init_args(self, args, kwargs):
        # Handle Older API and Newer API
        if len(args) > 0 and len(kwargs) > 0:
            raise Exception("Cannot use both positional and keyword arguments")
        if len(args) > 1 or len(kwargs) > 1:
            raise Exception("Too many arguments")

        if len(args) == 1:
            if isinstance(args[0], (iio.Context, str)):
                return args[0]
            else:
                raise Exception("Invalid argument. Input must be a string or a context")

        if len(kwargs) == 1:
            kws = ["uri", "uri_ctx"]
            for key in kwargs:
                if key not in kws:
                    raise Exception(f"Invalid keyword argument. Valid are: {kws}")
                if not isinstance(kwargs[key], iio.Context) and not isinstance(
                    kwargs[key], str
                ):
                    if key == "uri":
                        raise Exception(
                            "Invalid argument. Input must be a string for uri"
                        )
                    else:
                        raise Exception(
                            "Invalid argument. Input must be a string or a context for uri_ctx"
                        )
                return kwargs[key]

        return None  # Auto detect

    # def __init__(self, uri_ctx: Union[str, iio.Context] = None) -> None:
    def __init__(
        self, *args: Union[str, iio.Context], **kwargs: Union[str, iio.Context]
    ) -> None:

        # Handle Older API and Newer APIs
        uri_ctx = self.__handle_init_args(args, kwargs)

        # Handle context
        if isinstance(uri_ctx, iio.Context):
            self._ctx = uri_ctx
            self.uri = ""
        elif uri_ctx:
            self.uri = uri_ctx
            context_manager.__init__(self, uri_ctx, self._device_name)
        else:
            required_devices = [self._rx_data_device_name, self._control_device_name]
            contexts = iio.scan_contexts()
            self._ctx = None
            for c in contexts:
                ctx = iio.Context(c)
                devs = [dev.name for dev in ctx.devices]
                if all(dev in devs for dev in required_devices):
                    self._ctx = iio.Context(c)
                    break
            if not self._ctx:
                raise Exception("No context could be found for class")

        # Set up devices
        if self._control_device_name:
            self._ctrl = self._ctx.find_device(self._control_device_name)
            if not self._ctrl:
                raise Exception(
                    f"No device found with name {self._control_device_name}"
                )

    def __post_init__(self):
        pass


class rx_def(shared_def, rx, context_manager, metaclass=ABCMeta):
    """Template metaclass for rx only device specific interfaces."""

    """Names of rx data channels.
    List of strings with names of channels.
    If not defined all channels with scan elements will
    be populated as available channels.
    """
    _rx_channel_names = None

    @property
    @abstractmethod
    def _rx_data_device_name(self) -> None:
        """Name of driver used for receiving data.
        This is the IIO device used collect data from.
        """
        raise NotImplementedError  # pragma: no cover

    __run_rx_post_init__ = True

    def __init__(
        self, *args: Union[str, iio.Context], **kwargs: Union[str, iio.Context]
    ) -> None:

        shared_def.__init__(self, *args, **kwargs)

        if self._rx_data_device_name:
            self._rxadc = self._ctx.find_device(self._rx_data_device_name)
            if not self._rxadc:
                raise Exception(
                    f"No device found with name {self._rx_data_device_name}"
                )

        # Set up channels
        if self._rxadc and self._rx_channel_names is None:
            self._rx_channel_names = [
                chan.id for chan in self._rxadc.channels if chan.scan_element
            ]

            if not self._rx_channel_names:
                raise Exception(f"No scan elements found for device {self._rxadc.name}")

        rx.__init__(self)

        if self.__run_rx_post_init__:
            self.__post_init__()


class tx_def(shared_def, tx, context_manager, metaclass=ABCMeta):
    """Template metaclass for rx only device specific interfaces."""

    """Names of tx data channels.
    List of strings with names of channels.
    If not defined all channels with scan elements will
    be populated as available channels.
    """
    _tx_channel_names = None

    @property
    @abstractmethod
    def _tx_data_device_name(self) -> None:
        """Name of driver used for transmitting data.
        This is the IIO device used collect data from.
        """
        raise NotImplementedError  # pragma: no cover

    __run_tx_post_init__ = True

    def __init__(
        self, *args: Union[str, iio.Context], **kwargs: Union[str, iio.Context]
    ) -> None:

        shared_def.__init__(self, *args, **kwargs)

        if self._tx_data_device_name:
            self._txdac = self._ctx.find_device(self._tx_data_device_name)
            if not self._txdac:
                raise Exception(
                    f"No device found with name {self._tx_data_device_name}"
                )

        # Set up channels
        if self._txdac and self._tx_channel_names is None:
            self._tx_channel_names = [
                chan.id for chan in self._rxadc.channels if chan.scan_element
            ]

            if not self._tx_channel_names:
                raise Exception(f"No scan elements found for device {self._rxadc.name}")

        tx.__init__(self)

        if self.__run_tx_post_init__:
            self.__post_init__()


class rx_tx_def(tx_def, rx_def):
    """Template metaclass for rx and tx device specific interfaces."""

    __run_rx_post_init__ = False
    __run_tx_post_init__ = False

    def __init__(
        self, *args: Union[str, iio.Context], **kwargs: Union[str, iio.Context]
    ) -> None:

        rx_def.__init__(self, *args, **kwargs)
        tx_def.__init__(self, *args, **kwargs)

        self.__post_init__()
