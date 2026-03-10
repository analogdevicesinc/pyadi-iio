# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ad514x(context_manager, attribute):
    """ AD514x DigiPOTs  """

    compatible_parts = ["AD5141", "AD5142", "AD5142A", "AD5143", "AD5144"]
    _complex_data = False
    channel = []  # type: ignore
    _device_name = ""

    def __init__(self, uri="", device_name=""):

        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None

        if not device_name:
            device_name = self.compatible_parts[0]
        else:
            if device_name not in self.compatible_parts:
                raise Exception("Not a compatible device: " + device_name)

        # Select the device matching device_name as working device
        for device in self._ctx.devices:
            if device.name == device_name:
                self._ctrl = device
                break

        self.channel = []
        for ch in self._ctrl.channels:
            name = ch._id
            self.channel.append(self._channel(self._ctrl, name))

    @property
    def nvm_programming_avail(self):
        """Get nvm_programming options"""
        return self._get_iio_dev_attr_str("nvm_programming_available")

    @property
    def nvm_programming(self):
        """Get nvm_programming value"""
        return self._get_iio_dev_attr_str("nvm_programming")

    @nvm_programming.setter
    def nvm_programming(self, value):
        """Set nvm_programming value"""
        if value in self.nvm_programming_avail:
            self._set_iio_dev_attr_str("nvm_programming", value)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.nvm_programming_avail)
            )

    @property
    def rdac_wp_avail(self):
        """Get rdac_wp options"""
        return self._get_iio_dev_attr_str("rdac_wp_available")

    @property
    def rdac_wp(self):
        """Get rdac_wp value"""
        return self._get_iio_dev_attr_str("rdac_wp")

    @rdac_wp.setter
    def rdac_wp(self, value):
        """Set rdac_wp value"""
        if value in self.rdac_wp_avail:
            self._set_iio_dev_attr_str("rdac_wp", value)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.rdac_wp_avail)
            )

    class _channel(attribute):
        """Digipots channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """Get channel raw value"""
            return self._get_iio_attr(self.name, "raw", False)

        @raw.setter
        def raw(self, value):
            """Set channel raw value"""
            self._set_iio_attr(self.name, "raw", False, str(int(value)))

        @property
        def eeprom_value(self):
            """Get channel eeprom value"""
            return self._get_iio_attr(self.name, "eeprom_value", False)

        @eeprom_value.setter
        def eeprom_value(self, value):
            """Set channel eeprom value"""
            self._set_iio_attr(self.name, "eeprom_value", False, str(int(value)))

        @property
        def input_reg_val(self):
            """Get channel input register value"""
            return self._get_iio_attr(self.name, "input_reg_val", False)

        @input_reg_val.setter
        def input_reg_val(self, value):
            """Set channel input register value"""
            self._set_iio_attr(self.name, "input_reg_val", False, str(int(value)))

        @property
        def bottom_scale_option(self):
            """Get bottom scale option"""
            return self._get_iio_attr_str(self.name, "bottom_scale_option", False)

        @property
        def bottom_scale_option_avail(self):
            """Get bottom scale options"""
            return self._get_iio_attr_str(
                self.name, "bottom_scale_option_available", False
            )

        @bottom_scale_option.setter
        def bottom_scale_option(self, value):
            """Set bottom scale option"""
            if value in self.bottom_scale_option_avail:
                self._set_iio_attr(self.name, "bottom_scale_option", False, value)
            else:
                raise ValueError(
                    "Error: Bottom_Scale_Option option not supported \nUse one of: "
                    + str(self.bottom_scale_option_avail)
                )

        @property
        def top_scale_option(self):
            """Get top scale options"""
            return self._get_iio_attr_str(self.name, "top_scale_option", False)

        @property
        def top_scale_option_avail(self):
            """Get top scale options"""
            return self._get_iio_attr_str(
                self.name, "top_scale_option_available", False
            )

        @top_scale_option.setter
        def top_scale_option(self, value):
            """Set top scale options"""
            if value in self.top_scale_option_avail:
                self._set_iio_attr(self.name, "top_scale_option", False, value)
            else:
                raise ValueError(
                    "Error: Top_Scale_Option option not supported \nUse one of: "
                    + str(self.top_scale_option_avail)
                )

        @property
        def copy_eeprom_to_rdac(self):
            """Get value"""
            return self._get_iio_attr_str(self.name, "copy_eeprom_to_rdac", False)

        @property
        def copy_eeprom_to_rdac_avail(self):
            """Get options"""
            return self._get_iio_attr_str(
                self.name, "copy_eeprom_to_rdac_available", False
            )

        @copy_eeprom_to_rdac.setter
        def copy_eeprom_to_rdac(self, value):
            """Set value"""
            if value in self.copy_eeprom_to_rdac_avail:
                self._set_iio_attr(self.name, "copy_eeprom_to_rdac", False, value)
            else:
                raise ValueError(
                    "Error: copy_eeprom_to_rdac option not supported \nUse one of: "
                    + str(self.copy_eeprom_to_rdac_avail)
                )

        @property
        def copy_rdac_to_eeprom(self):
            """Get value"""
            return self._get_iio_attr_str(self.name, "copy_rdac_to_eeprom", False)

        @property
        def copy_rdac_to_eeprom_avail(self):
            """Get options"""
            return self._get_iio_attr_str(
                self.name, "copy_rdac_to_eeprom_available", False
            )

        @copy_rdac_to_eeprom.setter
        def copy_rdac_to_eeprom(self, value):
            """Set value"""
            if value in self.copy_rdac_to_eeprom_avail:
                self._set_iio_attr(self.name, "copy_rdac_to_eeprom", False, value)
            else:
                raise ValueError(
                    "Error: copy_rdac_to_eeprom option not supported \nUse one of: "
                    + str(self.copy_rdac_to_eeprom_avail)
                )

        @property
        def shutdown(self):
            """Get shutdown value"""
            return self._get_iio_attr_str(self.name, "shutdown", False)

        @property
        def shutdown_avail(self):
            """Get shutdown options"""
            return self._get_iio_attr_str(self.name, "shutdown_available", False)

        @shutdown.setter
        def shutdown(self, value):
            """Set shutdown"""
            if value in self.shutdown_avail:
                self._set_iio_attr(self.name, "shutdown", False, value)
            else:
                raise ValueError(
                    "Error: shutdown option not supported \nUse one of: "
                    + str(self.shutdown_avail)
                )

        @property
        def rdac_6db(self):
            """Get rdac_6db value"""
            return self._get_iio_attr_str(self.name, "rdac_6db", False)

        @property
        def rdac_6db_avail(self):
            """Get rdac_6db options"""
            return self._get_iio_attr_str(self.name, "rdac_6db_available", False)

        @rdac_6db.setter
        def rdac_6db(self, value):
            """Set rdac_6db value"""
            if value in self.rdac_6db_avail:
                self._set_iio_attr(self.name, "rdac_6db", False, value)
            else:
                raise ValueError(
                    "Error: rdac_6db option not supported \nUse one of: "
                    + str(self.rdac_6db_avail)
                )

        @property
        def rdac_linear(self):
            """Get rdac_linear value"""
            return self._get_iio_attr_str(self.name, "rdac_linear", False)

        @property
        def rdac_linear_avail(self):
            """Get rdac_linear options"""
            return self._get_iio_attr_str(self.name, "rdac_linear_available", False)

        @rdac_linear.setter
        def rdac_linear(self, value):
            """Set rdac_linear value"""
            if value in self.rdac_linear_avail:
                self._set_iio_attr(self.name, "rdac_linear", False, value)
            else:
                raise ValueError(
                    "Error: rdac_linear option not supported \nUse one of: "
                    + str(self.rdac_linear_avail)
                )

        @property
        def sw_lrdac(self):
            """Get sw_lrdac value"""
            return self._get_iio_attr_str(self.name, "sw_lrdac", False)

        @property
        def sw_lrdac_avail(self):
            """Get sw_lrdac options"""
            return self._get_iio_attr_str(self.name, "sw_lrdac_available", False)

        @sw_lrdac.setter
        def sw_lrdac(self, value):
            """Set sw_lrdac value"""
            if value in self.sw_lrdac_avail:
                self._set_iio_attr(self.name, "sw_lrdac", False, value)
            else:
                raise ValueError(
                    "Error: sw_lrdac option not supported \nUse one of: "
                    + str(self.sw_lrdac_avail)
                )

        @property
        def scale(self):
            """Get scale value"""
            return self._get_iio_attr_str(self.name, "scale", False)
