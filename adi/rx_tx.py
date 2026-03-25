# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from abc import ABCMeta, abstractmethod
from typing import List, Union

import iio
import numpy as np

import adi.compat as cl
from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.dds import dds

if cl._is_libiio_v1():
    from adi.compat import compat_libiio_v1_rx as crx
    from adi.compat import compat_libiio_v1_tx as ctx
else:
    from adi.compat import compat_libiio_v0_rx as crx
    from adi.compat import compat_libiio_v0_tx as ctx


def are_channels_complex(channels: Union[List[str], List[iio.Channel]]) -> bool:
    """Check if channels are complex or not

    Args:
        channels: List of channel names or iio.Channel objects
    """
    for channel in channels:
        if isinstance(channel, iio.Channel):
            channel = channel.id
        if channel.endswith("_i") or channel.endswith("_q"):
            return True
    return False


class phy(attribute):
    _ctrl: iio.Device = []

    def __del__(self):
        self._ctrl = []


class rx_tx_common(attribute):
    """Common functions for RX and TX"""

    _complex_data = False

    def _annotate(self, data, cnames: List[str], echans: List[int]):
        return {cnames[ec]: data[i] for i, ec in enumerate(echans)}


class rx_core(rx_tx_common, metaclass=ABCMeta):
    """Buffer handling for receive devices"""

    _rxadc: iio.Device = []
    _rx_channel_names: List[str] = []
    # Set to True if complex data for RX only, overrides _complex_data
    _rx_complex_data = None
    _rx_data_type = np.int16
    _rx_data_si_type = np.int16
    _rx_shift = 0
    _rx_buffer_size = 1024
    __rx_enabled_channels = [0]
    _rx_output_type = "raw"
    _rxbuf = None
    _rx_unbuffered_data = False
    _rx_annotated = False
    _rx_stack_interleaved = True  # Convert from channel to sample interleaved

    def __init__(self, rx_buffer_size=1024):
        N = 2 if self._complex_data else 1
        rx_enabled_channels = list(range(len(self._rx_channel_names) // N))
        self._num_rx_channels = len(self._rx_channel_names)
        self.rx_enabled_channels = rx_enabled_channels
        self.rx_buffer_size = rx_buffer_size

    @property
    def _complex_data(self) -> bool:
        """Data to/from device is quadrature (Complex).
        When True ADC channel pairs are used together and the
        rx method will generate complex data types.
        """
        if self._rx_complex_data is None:
            return super()._complex_data
        return self._rx_complex_data

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
        return self._rx_buffer_size

    @rx_buffer_size.setter
    def rx_buffer_size(self, value):
        self._rx_buffer_size = value

    @property
    def rx_enabled_channels(self) -> Union[List[int], List[str]]:
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
        self._rxbuf = None

    def __del__(self):
        self._rxbuf = []
        if hasattr("self", "_rxadc") and self._rxadc:
            for m in self._rx_channel_names:
                v = self._rxadc.find_channel(m)
                v.enabled = False
        self._rxadc = []

    def __get_rx_channel_scales(self):
        rx_scale = []
        for i in self.rx_enabled_channels:
            v = self._rxadc.find_channel(self._rx_channel_names[i])
            if "scale" in v.attrs:
                scale = self._get_iio_attr(self._rx_channel_names[i], "scale", False)
            else:
                scale = 1.0
            rx_scale.append(scale)
        return rx_scale

    def __get_rx_channel_offsets(self):
        rx_offset = []
        for i in self.rx_enabled_channels:
            v = self._rxadc.find_channel(self._rx_channel_names[i])
            if "offset" in v.attrs:
                offset = self._get_iio_attr(self._rx_channel_names[i], "offset", False)
            else:
                offset = 0.0
            rx_offset.append(offset)
        return rx_offset

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
            rx_scale = self.__get_rx_channel_scales()
            rx_offset = self.__get_rx_channel_offsets()

        for samp in range(self.rx_buffer_size):
            for i, m in enumerate(self.rx_enabled_channels):
                raw = self._get_iio_attr(
                    self._rx_channel_names[m], "raw", False, self._rxadc
                )
                if self._rx_output_type == "SI":
                    x[i][samp] = (raw + rx_offset[i]) * rx_scale[i]
                else:
                    x[i][samp] = raw

        return x

    def __rx_complex(self):
        x = self._rx_buffered_data()
        if len(x) % 2 != 0:
            raise Exception(
                "Complex data must have an even number of component channels"
            )
        out = [x[i] + 1j * x[i + 1] for i in range(0, len(x), 2)]
        # Don't return list if a single channel
        return out[0] if len(x) == 2 else out

    def __rx_non_complex(self):
        x = self._rx_buffered_data()
        if self._rx_output_type == "SI":
            rx_scale = self.__get_rx_channel_scales()
            rx_offset = self.__get_rx_channel_offsets()
            x = x if isinstance(x, list) else [x]
            x = [rx_scale[i] * (x[i] + rx_offset[i]) for i in range(len(x))]
        elif self._rx_output_type != "raw":
            raise Exception("_rx_output_type undefined")

        # Don't return list if a single channel
        return x[0] if len(self.rx_enabled_channels) == 1 else x

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

    @abstractmethod
    def _rx_init_channels(self):
        """Initialize RX channels"""
        raise NotImplementedError

    @abstractmethod
    def _rx_buffered_data(self):
        """Read data from RX buffer"""
        raise NotImplementedError


class tx_core(dds, rx_tx_common, metaclass=ABCMeta):
    """Buffer handling for transmit devices"""

    _tx_buffer_size = 1024
    _txdac: iio.Device = []
    _tx_channel_names: List[str] = []
    # Set to True if complex data for TX only, overrides _complex_data
    _tx_complex_data = None
    _tx_data_type = None
    _txbuf = None
    _output_byte_filename = "out.bin"
    _push_to_file = False
    _tx_cyclic_buffer = False

    def __init__(self, tx_cyclic_buffer=False):
        N = 2 if self._complex_data else 1
        tx_enabled_channels = list(range(len(self._tx_channel_names) // N))
        self._num_tx_channels = len(self._tx_channel_names)
        self.tx_enabled_channels = tx_enabled_channels
        self.tx_cyclic_buffer = tx_cyclic_buffer
        dds.__init__(self)

    def __del__(self):
        self._txbuf = []
        if hasattr("self", "_txdac") and self._txdac:
            for m in self._tx_channel_names:
                v = self._txdac.find_channel(m)
                v.enabled = False
        self._txdac = []

    @property
    def _complex_data(self):
        """Data to device is quadrature (Complex).
        When True DAC channel pairs are used together and the
        tx method will assume complex samples.
        """
        if self._tx_complex_data is None:
            return super()._complex_data
        return self._tx_complex_data

    @property
    def tx_cyclic_buffer(self):
        """tx_cyclic_buffer: Enable cyclic buffer for TX"""
        return self._tx_cyclic_buffer

    @tx_cyclic_buffer.setter
    def tx_cyclic_buffer(self, value):
        if self._txbuf:
            raise Exception(
                "TX buffer already created, buffer must be "
                "destroyed then recreated to modify tx_cyclic_buffer"
            )
        self._tx_cyclic_buffer = value

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
        self._txbuf = None

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

        if not self._tx_data_type:
            # Find channel data format
            chan_name = self._tx_channel_names[self.tx_enabled_channels[0]]
            chan = self._txdac.find_channel(chan_name, True)
            df = chan.data_format
            fmt = ("i" if df.is_signed is True else "u") + str(df.length // 8)
            fmt = ">" + fmt if df.is_be else fmt
            self._tx_data_type = np.dtype(fmt)

        if self._txbuf and self.tx_cyclic_buffer:
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
            data = np.empty(stride * len(data_np[0]), dtype=self._tx_data_type)
            for chan in data_np:
                i = np.real(chan)
                q = np.imag(chan)
                data[indx::stride] = i.astype(self._tx_data_type)
                data[indx + 1 :: stride] = q.astype(self._tx_data_type)
                indx = indx + 2
        else:
            if self._num_tx_channels_enabled == 1:
                data_np = [data_np]

            if len(data_np) != self._num_tx_channels_enabled:
                raise Exception("Not enough data provided for channel mapping")

            indx = 0
            stride = self._num_tx_channels_enabled
            data = np.empty(stride * len(data_np[0]), dtype=self._tx_data_type)
            for chan in data_np:
                data[indx::stride] = chan.astype(self._tx_data_type)
                indx = indx + 1

        if not self._txbuf:
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
            self._tx_buffer_push(data)

    @abstractmethod
    def _tx_buffer_push(self, data):
        """Push data to TX buffer.

        data: bytearray
        """
        raise NotImplementedError

    @abstractmethod
    def _tx_init_channels(self):
        """Initialize TX channels"""
        raise NotImplementedError


class rx(crx, rx_core):
    pass


class tx(ctx, tx_core):
    pass


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
