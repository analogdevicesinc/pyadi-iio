# Copyright (C) 2023-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.device_base import rx_chan_comp


class max9611_channel_voltage_sense(attribute):
    """MAX9611 Voltage Sense Channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX9611 voltage-sense channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def input(self):
        """MAX9611 Voltage Sense Channel input value."""
        return self._get_iio_attr(self.name, "input", False)


class max9611_channel_voltage_input(attribute):
    """MAX9611 Voltage Input Channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX9611 voltage-input channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """MAX9611 Voltage Input Channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """MAX9611 Voltage Input Channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))

    @property
    def offset(self):
        """Voltage Input Channel offset."""
        return float(self._get_iio_attr_str(self.name, "offset", False))


class max9611_channel_power(attribute):
    """MAX9611 Power Channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX9611 power channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def input(self):
        """MAX9611 Power Channel input value."""
        return self._get_iio_attr(self.name, "input", False)

    @property
    def shunt_resistor(self):
        """MAX9611 Power Channel shunt resistor."""
        return float(self._get_iio_attr_str(self.name, "shunt_resistor", False))


class max9611_channel_current(attribute):
    """MAX9611 Current Channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX9611 current channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def input(self):
        """MAX9611 Current Channel input value."""
        return self._get_iio_attr(self.name, "input", False)

    @property
    def shunt_resistor(self):
        """MAX9611 Current Channel shunt resistor."""
        return float(self._get_iio_attr_str(self.name, "shunt_resistor", False))


class max9611_channel_temp(attribute):
    """MAX9611 Temperature Channel"""

    def __init__(self, ctrl, channel_name):
        """Initialize a MAX9611 temperature channel."""
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """MAX9611 Temperature Channel raw value."""
        return self._get_iio_attr(self.name, "raw", False)

    @property
    def scale(self):
        """MAX9611 Temperature Channel scale."""
        return float(self._get_iio_attr_str(self.name, "scale", False))


class max9611(rx_chan_comp):
    """AD611 Current-sense Amplifier with ADC"""

    _complex_data = False
    _device_name = ""
    _rx_unbuffered_data = True
    _rx_channel_names = ["voltage1", "temp"]
    # voltage0 (sense), power and current have no scale attribute, so keep them
    # out of the auto-populated channel list and attach them manually below.
    _ignore_channels = ["voltage0", "power", "current"]
    compatible_parts = ["max9611", "max9612"]

    def __post_init__(self):
        """Attach channels that have no scale attribute."""
        self.voltage0 = max9611_channel_voltage_sense(self._ctrl, "voltage0")
        self.power = max9611_channel_power(self._ctrl, "power")
        self.current = max9611_channel_current(self._ctrl, "current")

    def _channel_def(self, ctrl, name):
        if name == "voltage0":
            return max9611_channel_voltage_sense(ctrl, name)
        if name == "voltage1":
            return max9611_channel_voltage_input(ctrl, name)
        if name == "power":
            return max9611_channel_power(ctrl, name)
        if name == "current":
            return max9611_channel_current(ctrl, name)
        return max9611_channel_temp(ctrl, name)
