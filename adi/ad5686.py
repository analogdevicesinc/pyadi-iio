# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal
from enum import Enum

from adi.attribute import attribute
from adi.device_base import tx_chan_comp


class ad5686_channel(attribute):
    """AD5686 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl
        self._format = self._ctrl.find_channel(channel_name, True).data_format

    @property
    def raw(self):
        """AD5686 channel raw value"""
        return int(self._get_iio_attr_str(self.name, "raw", True, self._ctrl))

    @raw.setter
    def raw(self, value):
        value = max(0, min(int(value), (2 ** self._format.bits) - 1))
        self._set_iio_attr(self.name, "raw", True, value)

    @property
    def powerdown(self):
        """AD5686 channel powerdown value"""
        return self._get_iio_attr(self.name, "powerdown", True)

    @powerdown.setter
    def powerdown(self, val):
        """AD5686 channel powerdown value"""
        self._set_iio_attr(self.name, "powerdown", True, val)

    @property
    def powerdown_mode(self) -> "ad5686.powerdown_mode":
        """AD5686 channel powerdown mode value"""
        return ad5686.powerdown_mode(
            self._get_iio_attr_str(self.name, "powerdown_mode", True)
        )

    @powerdown_mode.setter
    def powerdown_mode(self, mode):
        """AD5686 channel powerdown value"""
        value = mode.value if isinstance(mode, ad5686.powerdown_mode) else mode
        self._set_iio_attr(self.name, "powerdown_mode", True, value)

    @property
    def powerdown_mode_available(self):
        """AD5686 channel available powerdown modes"""
        modes_str = self._get_iio_attr_str(self.name, "powerdown_mode_available", True)
        return [ad5686.powerdown_mode(m) for m in modes_str.split()]

    @property
    def scale(self) -> Decimal:
        """AD5686 channel scale(gain)"""
        return Decimal(self._get_iio_attr_str(self.name, "scale", True))

    @scale.setter
    def scale(self, value):
        self._set_iio_attr(self.name, "scale", True, value)

    @property
    def scale_available(self):
        """AD5686 channel available scale values"""
        scale_str = self._get_iio_attr_str(self.name, "scale_available", True)
        return [Decimal(s) for s in scale_str.split()]

    @property
    def voltage(self) -> float:
        """AD5686 channel value in Volts"""
        return float(self.raw * self.scale / 1000)

    @voltage.setter
    def voltage(self, val: float):
        """AD5686 channel value in Volts"""
        self.raw = int(1000 * Decimal(val) / self.scale)


class ad5686(tx_chan_comp):
    """ AD5686 DAC """

    class powerdown_mode(Enum):
        """AD5686 Powerdown Mode Enumeration"""

        PULLDOWN_1K = "1kohm_to_gnd"
        PULLDOWN_100K = "100kohm_to_gnd"
        TRISTATE = "three_state"

    class gain(Enum):
        """AD5686 Gain Mode Enumeration"""

        NORMAL = 1
        DOUBLE = 2

    compatible_parts = [
        "ad5686",
        "ad5310r",
        "ad5311r",
        "ad5313r",
        "ad5316r",
        "ad5317r",
        "ad5338r",
        "ad5671r",
        "ad5672r",
        "ad5673r",
        "ad5674",
        "ad5674r",
        "ad5675",
        "ad5675r",
        "ad5676",
        "ad5676r",
        "ad5677r",
        "ad5679",
        "ad5679r",
        "ad5681r",
        "ad5682r",
        "ad5683",
        "ad5683r",
        "ad5684",
        "ad5684r",
        "ad5685r",
        "ad5686r",
        "ad5687",
        "ad5687r",
        "ad5689",
        "ad5689r",
        "ad5691r",
        "ad5692r",
        "ad5693",
        "ad5693r",
        "ad5694",
        "ad5694r",
        "ad5695r",
        "ad5696",
        "ad5696r",
        "ad5697r",
    ]
    _complex_data = False
    _channel_def = ad5686_channel
    _device_name = ""

    def __init__(self, uri="", device_name="", device_index=0, trigger=None):
        super().__init__(uri, device_name, device_index)
        self._scales = self.channel[0].scale_available
        if trigger:
            self.set_tx_trigger(trigger)

    def set_gain(self, value: "ad5686.gain"):
        """Set the DAC output gain.

        Args:
            value:
                :class:`ad5686.gain` member selecting the output gain
                (``NORMAL`` or ``DOUBLE``). Only supported on devices that
                expose two entries in ``scale_available``.
        """
        if len(self._scales) != 2:
            raise ValueError("Cannot set gain on this device")

        self.channel[0].scale = (
            self._scales[1] if value == ad5686.gain.DOUBLE else self._scales[0]
        )
