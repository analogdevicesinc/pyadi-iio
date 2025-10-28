# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad9740(tx, context_manager):
    """AD9740/AD9742/AD9744/AD9748 10/12/14/8-bit, 210 MSPS DAC with DDS support"""

    _complex_data = False
    _device_name = "AD9740"

    def disable_dds(self):
        """Override DDS disable to use data_source attribute instead.

        AD9740 uses data_source control, not the standard DDS raw attribute.
        When switching to DMA mode, set data_source to 'normal'.
        """
        # Set data source to normal (DMA mode)
        if hasattr(self, 'channel') and len(self.channel) > 0:
            try:
                self.channel[0].data_source = "normal"
            except (AttributeError, OSError):
                # If data_source doesn't work, just pass
                # (driver might already be in correct mode)
                pass

    def __init__(self, uri="", device_name=""):
        """Constructor for AD9740 driver class"""

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = [
            "ad9740",  # 10-bit DAC
            "ad9742",  # 12-bit DAC
            "ad9744",  # 14-bit DAC
            "ad9748",  # 8-bit DAC
        ]

        self._ctrl = None
        self._txdac = None

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(
                    f"Not a compatible device: {device_name}. Supported device names "
                    f"are: {','.join(compatible_parts)}"
                )

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._txdac = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        if not self._txdac:
            raise Exception("Error in selecting matching device")

        self.output_bits = []
        self.channel = []
        self._tx_channel_names = []
        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            self.output_bits.append(ch.data_format.bits)
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name, output))
            if output is True:
                setattr(self, name, self._channel(self._ctrl, name, output))

        tx.__init__(self)

    class _channel(attribute):
        """AD9740 channel"""

        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        @property
        def sample_rate(self):
            """Sample rate of the DAC (from backend)
            Note: AD9740 driver doesn't expose sampling_frequency attribute,
            so we return a default value. Override if needed."""
            try:
                return self._get_iio_attr(self.name, "sampling_frequency", True)
            except (KeyError, OSError):
                # Attribute doesn't exist, return default (210 MHz from ADF4351)
                return 210000000

        @sample_rate.setter
        def sample_rate(self, value):
            """Set sample rate - may not be supported by all backends"""
            try:
                self._set_iio_attr(self.name, "sampling_frequency", True, value)
            except (KeyError, OSError):
                # Attribute doesn't exist, silently ignore
                pass

        @property
        def raw(self):
            """Get channel raw value
            DAC code in the range 0-16383 (14-bit)"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            """Set channel raw value"""
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def data_source(self):
            """Get/Set data source: normal, dds, or ramp"""
            return self._get_iio_attr_str(self.name, "data_source", True)

        @data_source.setter
        def data_source(self, value):
            """Set data source (normal, dds, ramp)"""
            self._set_iio_attr(self.name, "data_source", True, value)

        @property
        def data_source_available(self):
            """Available data sources"""
            return self._get_iio_attr_str(self.name, "data_source_available", True)

        # DDS Tone 0 controls
        @property
        def frequency0(self):
            """DDS Tone 0 frequency in Hz"""
            return int(self._get_iio_attr(self.name, "frequency0", True))

        @frequency0.setter
        def frequency0(self, value):
            self._set_iio_attr(self.name, "frequency0", True, str(int(value)))

        @property
        def scale0(self):
            """DDS Tone 0 scale (0.0 to 1.0)"""
            return float(self._get_iio_attr_str(self.name, "scale0", True))

        @scale0.setter
        def scale0(self, value):
            self._set_iio_attr(self.name, "scale0", True, str(Decimal(value).real))

        @property
        def phase0(self):
            """DDS Tone 0 phase in degrees"""
            # Kernel returns phase in radians as a decimal string
            radians = float(self._get_iio_attr_str(self.name, "phase0", True))
            return radians * 180.0 / 3.14159265359  # Convert to degrees

        @phase0.setter
        def phase0(self, value):
            """Set phase in degrees"""
            # Convert degrees to radians for kernel
            radians = float(value) * 3.14159265359 / 180.0
            self._set_iio_attr(self.name, "phase0", True, f"{radians:.5f}")

        # DDS Tone 1 controls
        @property
        def frequency1(self):
            """DDS Tone 1 frequency in Hz"""
            return int(self._get_iio_attr(self.name, "frequency1", True))

        @frequency1.setter
        def frequency1(self, value):
            self._set_iio_attr(self.name, "frequency1", True, str(int(value)))

        @property
        def scale1(self):
            """DDS Tone 1 scale (0.0 to 1.0)"""
            return float(self._get_iio_attr_str(self.name, "scale1", True))

        @scale1.setter
        def scale1(self, value):
            self._set_iio_attr(self.name, "scale1", True, str(Decimal(value).real))

        @property
        def phase1(self):
            """DDS Tone 1 phase in degrees"""
            # Kernel returns phase in radians as a decimal string
            radians = float(self._get_iio_attr_str(self.name, "phase1", True))
            return radians * 180.0 / 3.14159265359  # Convert to degrees

        @phase1.setter
        def phase1(self, value):
            """Set phase in degrees"""
            # Convert degrees to radians for kernel
            radians = float(value) * 3.14159265359 / 180.0
            self._set_iio_attr(self.name, "phase1", True, f"{radians:.5f}")
