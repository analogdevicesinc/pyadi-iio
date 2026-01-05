# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager


class ltc2672(context_manager, attribute):
    """LTC2672 DAC"""

    _complex_data = False
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for LTC2672 class"""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ltc2672-16", "ltc2672-12"]

        self._ctrl = None
        self.channel = []

        if not device_name:
            device_name = compatible_parts[0]
        else:
            if device_name not in compatible_parts:
                raise Exception(
                    f"Not a compatible device: {device_name}. Supported device names"
                    f"are: {','.join(compatible_parts)}"
                )

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                break

        if not self._ctrl:
            raise Exception("Error in selecting matching device")

        self.output_bits = []
        for ch in self._ctrl.channels:
            name = ch.id
            self.output_bits.append(ch.data_format.bits)
            self.channel.append(self._channel(self._ctrl, name))

    @property
    def all_chns_span(self):
        """Get all channels span in mA"""
        return self._get_iio_dev_attr_str("all_chns_span")

    @property
    def all_chns_span_avail(self):
        """Get list of span options in mA"""
        return self._get_iio_dev_attr_str("all_chns_span_available")

    @all_chns_span.setter
    def all_chns_span(self, value):
        """Set all channels span"""
        if value in self.all_chns_span_avail:
            self._set_iio_dev_attr_str("all_chns_span", value)
        else:
            raise ValueError(
                "Error: span setting not supported \nUse one of: "
                "str(self.all_chns_span_avail)"
            )

    @property
    def all_chns_raw(self):
        """Get raw value"""
        return self._get_iio_dev_attr_str("all_chns_raw")

    @all_chns_raw.setter
    def all_chns_raw(self, value):
        """Set raw value"""
        self._set_iio_dev_attr_str("all_chns_raw", value)

    @property
    def all_chns_current(self):
        """Get current value in mA"""
        return self._get_iio_dev_attr_str("all_chns_current")

    @all_chns_current.setter
    def all_chns_current(self, value):
        """Set current value in mA"""
        self._set_iio_dev_attr_str("all_chns_current", value)

    @property
    def all_chns_powerdown(self):
        """Get powerdown value"""
        return self._get_iio_dev_attr_str("all_chns_powerdown")

    @property
    def all_chns_powerdown_avail(self):
        """Get powerdown options"""
        return self._get_iio_dev_attr_str("all_chns_powerdown_available")

    @all_chns_powerdown.setter
    def all_chns_powerdown(self, value):
        """Set all channels powerdown"""
        if value in self.all_chns_powerdown_avail:
            self._set_iio_dev_attr_str("all_chns_powerdown", value)
        else:
            raise ValueError(
                "Error: powerdown option not supported \nUse one of: "
                "str(self.all_chns_powerdown_avail)"
            )

    @property
    def mux(self):
        """Get mux setting value"""
        return self._get_iio_dev_attr_str("mux")

    @property
    def mux_avail(self):
        """Get mux setting options"""
        return self._get_iio_dev_attr_str("mux_available")

    @mux.setter
    def mux(self, value):
        """Set mux option"""
        if value in self.mux_avail:
            self._set_iio_dev_attr_str("mux", value)
        else:
            raise ValueError(
                "Error: mux setting not supported \nUse one of: " "str(self.mux_avail)"
            )

    @property
    def fault_detect(self):
        """Get fault condition if any"""
        return self._get_iio_dev_attr_str("fault_detect")

    @property
    def fault_detect_avail(self):
        """Get fault detect options"""
        return self._get_iio_dev_attr_str("fault_detect_available")

    class _channel(attribute):
        """LTC2672 channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """Get channel raw value"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            """Set channel raw value"""
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def scale(self):
            """Get channel scale"""
            return self._get_iio_attr(self.name, "scale", True)

        @property
        def offset(self):
            """get channel offset"""
            return self._get_iio_attr(self.name, "offset", True)

        @property
        def current(self):
            """Get channel current value in mA"""
            return self._get_iio_attr(self.name, "current", True)

        @current.setter
        def current(self, value):
            """Set channel current value in mA"""
            self._set_iio_attr(self.name, "current", True, str(Decimal(value)))

        @property
        def span(self):
            """Get channel span value"""
            return self._get_iio_attr_str(self.name, "span", True)

        @property
        def span_avail(self):
            """Get channel span options"""
            return self._get_iio_attr_str(self.name, "span_available", True)

        @span.setter
        def span(self, value):
            """Set channel span setting"""
            if value in self.span_avail:
                self._set_iio_attr(self.name, "span", True, value)
            else:
                raise ValueError(
                    "Error: span setting not supported \nUse one of: "
                    "str(self.span_avail)"
                )

        @property
        def powerdown(self):
            """Get channel powerdown"""
            return self._get_iio_attr_str(self.name, "powerdown", True)

        @property
        def powerdown_avail(self):
            """Get channel powerdown options"""
            return self._get_iio_attr_str(self.name, "powerdown_available", True)

        @powerdown.setter
        def powerdown(self, value):
            """Set channel powerdown setting"""
            if value in self.powerdown_avail:
                self._set_iio_attr(self.name, "powerdown", True, value)
            else:
                raise ValueError(
                    "Error: powerdown setting not supported \nUse one of: "
                    "str(self.powerdown_avail)"
                )
