# Copyright (C) 2020-2026 Analog Devices, Inc.
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
        self.channel = []
        self._tx_channel_names = []
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

    @property
    def clamp_enable(self):
        """Get clamp_en setting"""
        return self._get_iio_dev_attr_str("clamp_enable")

    @property
    def clamp_enable_available(self):
        """Get list of all clamp_en settings"""
        return self._get_iio_dev_attr_str("clamp_enable_available")

    @clamp_enable.setter
    def clamp_enable(self, value):
        """Set clamp_en"""
        if value in self.clamp_enable_available:
            self._set_iio_dev_attr_str("clamp_enable", value)
        else:
            raise ValueError(
                "Error: clamp_en setting not supported \nUse one of: "
                + str(self.clamp_enable_available)
            )

    @property
    def tsd_enable(self):
        """Get tsd_en setting"""
        return self._get_iio_dev_attr_str("tsd_enable")

    @property
    def tsd_enable_available(self):
        """Get list of all tsd_en settings"""
        return self._get_iio_dev_attr_str("tsd_enable_available")

    @tsd_enable.setter
    def tsd_enable(self, value):
        """Set tsd_en"""
        if value in self.tsd_enable_available:
            self._set_iio_dev_attr_str("tsd_enable", value)
        else:
            raise ValueError(
                "Error: tsd_en setting not supported \nUse one of: "
                + str(self.tsd_enable_available)
            )

    @property
    def oc_tsd(self):
        """Get oc_tsd status"""
        return self._get_iio_dev_attr_str("oc_tsd")

    @property
    def oc_tsd_available(self):
        """Get list of all possible oc_tsd status"""
        return self._get_iio_dev_attr_str("oc_tsd_available")

    @property
    def all_chns_clear(self):
        """Get current all_chns_clear setting"""
        return self._get_iio_dev_attr_str("all_chns_clear")

    @property
    def all_chns_clear_available(self):
        """Get list of all all_chns_clear settings"""
        return self._get_iio_dev_attr_str("all_chns_clear_available")

    @all_chns_clear.setter
    def all_chns_clear(self, value):
        """Clear all channels"""
        if value in self.all_chns_clear_available:
            self._set_iio_dev_attr_str("all_chns_clear", value)
        else:
            raise ValueError(
                "Error: all_chns_clear setting not supported \nUse one of: "
                + str(self.all_chns_clear_available)
            )

    @property
    def sw_ldac_trigger(self):
        """Get sw_ldac_trigger setting"""
        return self._get_iio_dev_attr_str("all_chns_clear")

    @property
    def sw_ldac_trigger_available(self):
        """Get list of all sw_ldac_trigger settings"""
        return self._get_iio_dev_attr_str("sw_ldac_trigger_available")

    @sw_ldac_trigger.setter
    def sw_ldac_trigger(self, value):
        """Trigger software LDAC"""
        if value in self.sw_ldac_trigger_available:
            self._set_iio_dev_attr_str("sw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: sw_ldac_trigger setting not supported \nUse one of: "
                + str(self.sw_ldac_trigger_available)
            )

    @property
    def hw_ldac_trigger(self):
        """Get hw_ldac_trigger setting"""
        return self._get_iio_dev_attr_str("hw_ldac_trigger")

    @property
    def hw_ldac_trigger_available(self):
        """Get list of all hw_ldac_trigger settings"""
        return self._get_iio_dev_attr_str("hw_ldac_trigger_available")

    @hw_ldac_trigger.setter
    def hw_ldac_trigger(self, value):
        """Trigger hardware LDAC"""
        if value in self.hw_ldac_trigger_available:
            self._set_iio_dev_attr_str("hw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: hw_ldac_trigger setting not supported \nUse one of: "
                + str(self.hw_ldac_trigger_available)
            )

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

        @property
        def dac_register(self):
            """Get dac_register value"""
            return self._get_iio_attr_str(self.name, "dac_register", True)

        @dac_register.setter
        def dac_register(self, value):
            """Set dac_register value"""
            self._set_iio_attr(
                self.name, "dac_register", True, str(Decimal(value).real)
            )
