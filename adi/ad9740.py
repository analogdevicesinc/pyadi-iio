# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad9740(tx, context_manager):
    """AD9740/AD9742/AD9744/AD9748 10/12/14/8-bit, 210 MSPS DAC

    Two IIO channels:
      altvoltage0: DDS tone generator (frequency, scale, phase)
      voltage0:    DMA data output (data_source, buffer)
    """

    _complex_data = False
    _device_name = "AD9740"

    def disable_dds(self):
        """Switch to DMA mode by setting data_source to 'normal'."""
        try:
            self.voltage0.data_source = "normal"
        except (AttributeError, OSError):
            pass

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad9740", "ad9742", "ad9744", "ad9748"]

        if not device_name:
            device_name = compatible_parts[0]
        elif device_name not in compatible_parts:
            raise Exception(
                f"Not a compatible device: {device_name}. "
                f"Supported: {','.join(compatible_parts)}"
            )

        self._ctrl = None
        self._txdac = None

        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                self._txdac = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        self.channel = []
        self.output_bits = []
        self._tx_channel_names = []

        for ch in self._ctrl.channels:
            name = ch._id
            output = ch._output
            self.output_bits.append(ch.data_format.bits)
            chan_obj = self._channel(self._ctrl, name, output)
            self.channel.append(chan_obj)
            if output:
                setattr(self, name, chan_obj)
            # Only voltage channels are valid for DMA buffer
            if name.startswith("voltage"):
                self._tx_channel_names.append(name)

        tx.__init__(self)

    class _channel(attribute):
        """AD9740 channel"""

        def __init__(self, ctrl, channel_name, output):
            self.name = channel_name
            self._ctrl = ctrl
            self._output = output

        def _has_attr(self, attr_name):
            try:
                ch = self._ctrl.find_channel(self.name, self._output)
                return attr_name in ch.attrs
            except Exception:
                return False

        @property
        def data_source(self):
            """Get data source: normal, dds, or ramp (voltage0 only)"""
            return self._get_iio_attr_str(self.name, "data_source", True)

        @data_source.setter
        def data_source(self, value):
            self._set_iio_attr(self.name, "data_source", True, value)

        @property
        def data_source_available(self):
            """Available data sources"""
            return self._get_iio_attr_str(self.name, "data_source_available", True)

        @property
        def frequency0(self):
            """DDS Tone 0 frequency in Hz (altvoltage0 only)"""
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
            radians = float(self._get_iio_attr_str(self.name, "phase0", True))
            return radians * 180.0 / 3.14159265359

        @phase0.setter
        def phase0(self, value):
            radians = float(value) * 3.14159265359 / 180.0
            self._set_iio_attr(self.name, "phase0", True, f"{radians:.5f}")

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
            radians = float(self._get_iio_attr_str(self.name, "phase1", True))
            return radians * 180.0 / 3.14159265359

        @phase1.setter
        def phase1(self, value):
            radians = float(value) * 3.14159265359 / 180.0
            self._set_iio_attr(self.name, "phase1", True, f"{radians:.5f}")
