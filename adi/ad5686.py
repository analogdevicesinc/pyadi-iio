# Copyright (C) 2019-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal
from enum import Enum

import numpy as np

from adi.attribute import attribute
from adi.device_base import tx_chan_comp


class ad5686_channel(attribute):
    """AD5686 channel"""

    def __init__(self, ctrl, channel_name):
        self.name = channel_name
        self._ctrl = ctrl

    @property
    def raw(self):
        """AD5686 channel raw value"""
        return int(self._get_iio_attr_str(self.name, "raw", True, self._ctrl))

    @raw.setter
    def raw(self, value):
        self._set_iio_attr(self.name, "raw", True, str(int(value)))

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
    def powerdown_mode(self, mode: "ad5686.powerdown_mode"):
        """AD5686 channel powerdown value"""
        self._set_iio_attr_str(self.name, "powerdown_mode", True, mode.value)

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
    def voltage(self) -> Decimal:
        """AD5686 channel value in Volts"""
        return self.raw * self.scale / 1000

    @voltage.setter
    def voltage(self, val):
        """AD5686 channel value in Volts"""
        self.raw = int(1000 * Decimal(str(val)) / self.scale)


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
        "ad5686",
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

    def __init__(self, uri="", device_name="", device_index=0, trigger_name=None):
        super().__init__(uri, device_name, device_index)
        self._format = self._ctrl.find_channel(self.channel[0].name, True).data_format
        self._scales = self.channel[0].scale_available
        if trigger_name:
            self.set_trigger(trigger_name)

    def _tx_voltage_format(self, scale, voltage_np):
        raw = np.clip(voltage_np * 1000 / scale, 0, (2 ** self.nbits) - 1).astype(
            np.uint16
        )
        return raw << self._format.shift

    def tx_voltage(self, voltage_np, channels=None):
        """Transmit voltage values through the DAC. The voltage is clipped to
        the valid range based on the current scale and resolution settings.

        :param voltage_np:
            numpy.array of voltage values, list of numpy.array or dict of channel
            index to numpy.array.
        :param channels:
            Optional channel index or list of channel indices to transmit to.
            If not specified, tx_enabled_channels will not be modified and the
            current configuration will be used.
        """
        if isinstance(voltage_np, dict):
            channels = list(voltage_np.keys())
            voltage_np = list(voltage_np.values())

        is_v_list = isinstance(voltage_np, list)

        if channels is not None:
            if not isinstance(channels, list):
                channels = [channels]

            if is_v_list:
                if len(voltage_np) != len(channels):
                    raise ValueError(
                        "Length of voltage_np list must match length of channels list"
                    )
            elif len(channels) > 1:
                raise ValueError(
                    "voltage_np must be a list if multiple channels are specified"
                )

            old_channels = self.tx_enabled_channels
            self.tx_enabled_channels = channels
            if self.tx_enabled_channels != old_channels:
                self.tx_destroy_buffer()

        scale = float(self.channel[0].scale)
        if len(self.tx_enabled_channels) == 1:
            ch_voltage = voltage_np if not is_v_list else voltage_np[0]
            data_np = self._tx_voltage_format(scale, ch_voltage)
        else:
            data_np = []
            for ch_voltage in voltage_np:
                data_np.append(self._tx_voltage_format(scale, ch_voltage))

        self.tx(data_np)

    @property
    def nbits(self) -> int:
        """Number of resolution bits of the DAC"""
        return self._format.bits

    @property
    def output_gain(self) -> "ad5686.gain":
        """Set/Get gain mode of the DAC voltage output"""
        if self.channel[0].scale == self._scales[1]:
            return ad5686.gain.DOUBLE
        return ad5686.gain.NORMAL

    @output_gain.setter
    def output_gain(self, value: "ad5686.gain"):
        self.channel[0].scale = (
            self._scales[1] if value == ad5686.gain.DOUBLE else self._scales[0]
        )
