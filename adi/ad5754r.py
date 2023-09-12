# Copyright (C) 2020-2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad5754r(tx, context_manager):
    """ AD5754R DAC """

    _complex_data = False
    channel = []
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """ Constructor for AD5754R driver class """

        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad5754r"]
        self._ctrl = None

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
        for ch in self._ctrl.channels:
            name = ch.id
            self.output_bits.append(ch.data_format.bits)
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))

        tx.__init__(self)

    @property
    def int_ref_powerup(self):
        """Get internal reference powerup"""
        return self._get_iio_dev_attr_str("int_ref_powerup")

    @property
    def int_ref_powerup_available(self):
        """Get list of all internal reference powerup settings"""
        return self._get_iio_dev_attr_str("int_ref_powerup_available")

    @int_ref_powerup.setter
    def int_ref_powerup(self, value):
        """Set internal reference powerup"""
        if value in self.int_ref_powerup_available:
            self._set_iio_dev_attr_str("int_ref_powerup", value)
        else:
            raise ValueError(
                "Error: internal reference powerup not supported \nUse one of: "
                + str(self.int_ref_powerup_available)
            )

    @property
    def clear_setting(self):
        """Get clear code setting"""
        return self._get_iio_dev_attr_str("clear_setting")

    @property
    def clear_setting_available(self):
        """Get list of all clear code settings"""
        return self._get_iio_dev_attr_str("clear_setting_available")

    @clear_setting.setter
    def clear_setting(self, value):
        """Set clear setting"""
        if value in self.clear_setting_available:
            self._set_iio_dev_attr_str("clear_setting", value)
        else:
            raise ValueError(
                "Error: clear setting not supported \nUse one of: "
                + str(self.clear_setting_available)
            )

    @property
    def sdo_disable(self):
        """Get sdo disable"""
        return self._get_iio_dev_attr_str("sdo_disable")

    @property
    def sdo_disable_available(self):
        """Get list of all sdo enable/disable settings"""
        return self._get_iio_dev_attr_str("sdo_disable_available")

    @sdo_disable.setter
    def sdo_disable(self, value):
        """Set sdo enable/disable setting"""
        if value in self.sdo_disable_available:
            self._set_iio_dev_attr_str("sdo_disable", value)
        else:
            raise ValueError(
                "Error: sdo setting not supported \nUse one of: "
                + str(self.sdo_disable_available)
            )

    @property
    def sampling_frequency(self):
        """Get sampling frequency"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Set sampling frequency"""
        self._set_iio_dev_attr_str("sampling_frequency", value)

    class _channel(attribute):
        """AD5754R channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """Get channel raw value
                DAC code in the range 0-65535"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            """Set channel raw value"""
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def offset(self):
            """Get channel offset"""
            return self._get_iio_attr_str(self.name, "offset", True)

        @offset.setter
        def offset(self, value):
            """Set channel offset"""
            self._set_iio_attr(self.name, "offset", True, str(Decimal(value).real))

        @property
        def scale(self):
            """Get channel scale"""
            return float(self._get_iio_attr_str(self.name, "scale", True))

        @scale.setter
        def scale(self, value):
            """Set channel scale"""
            self._set_iio_attr(self.name, "scale", True, str(Decimal(value).real))

        @property
        def powerup(self):
            """Get DAC chn powerup"""
            return self._get_iio_attr_str(self.name, "powerup", True)

        @property
        def powerup_available(self):
            """Get list of DAC chn powerup settings"""
            return self._get_iio_attr_str(self.name, "powerup_available", True)

        @powerup.setter
        def powerup(self, value):
            """Set DAC chn powerup"""
            if value in self.powerup_available:
                self._set_iio_attr(self.name, "powerup", True, value)
            else:
                raise ValueError(
                    "Error: powerup setting not supported \nUse one of: "
                    + str(self.powerup_available)
                )

        @property
        def range(self):
            """Get output range"""
            return self._get_iio_attr_str(self.name, "range", True)

        @property
        def range_available(self):
            """Get list of all output ranges"""
            return self._get_iio_attr_str(self.name, "range_available", True)

        @range.setter
        def range(self, value):
            """Set DAC chn range"""
            if value in self.range_available:
                self._set_iio_attr(self.name, "range", True, value)
            else:
                raise ValueError(
                    "Error: range setting not supported \nUse one of: "
                    + str(self.range_available)
                )
