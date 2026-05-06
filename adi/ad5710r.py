# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad5710r(tx, context_manager):
    """ AD5710r DAC """

    _complex_data = False
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for AD5710r class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad5710r"]

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

        self.channel = []  # type: ignore
        self._output_bits = []
        for ch in self._ctrl.channels:
            name = ch.id
            self._output_bits.append(ch.data_format.bits)
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
            setattr(self, name, self._channel(self._ctrl, name))

        tx.__init__(self)

    @property
    def output_bits(self):
        """AD5710r channel-wise number of output bits list"""
        return self._output_bits

    ### Add device attributes here ###

    @property
    def sampling_frequency(self):
        """AD5710r sampling frequency config"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def all_ch_operating_mode_avail(self):
        """AD5710r all channels operating mode available"""
        return self._get_iio_dev_attr_str("all_ch_operating_mode_available")

    @property
    def all_ch_operating_mode(self):
        """AD5710r all channels operating mode config"""
        return self._get_iio_dev_attr_str("all_ch_operating_mode")

    @all_ch_operating_mode.setter
    def all_ch_operating_mode(self, value):
        if value in self.all_ch_operating_mode_avail:
            self._set_iio_dev_attr_str("all_ch_operating_mode", value)
        else:
            raise ValueError(
                "Error: Operating mode not supported \nUse one of: "
                + str(self.all_ch_operating_mode_avail)
            )

    @property
    def all_ch_input_registers(self):
        """AD5710r all input registers config"""
        return self._get_iio_dev_attr_str("all_ch_input_registers")

    @all_ch_input_registers.setter
    def all_ch_input_registers(self, value):
        self._set_iio_dev_attr_str("all_ch_input_registers", value)

    @property
    def all_ch_raw(self):
        """AD5710r all dac registers config"""
        return self._get_iio_dev_attr_str("all_ch_raw")

    @all_ch_raw.setter
    def all_ch_raw(self, value):
        self._set_iio_dev_attr_str("all_ch_raw", value)

    @property
    def reference_select_available(self):
        """AD5710r reference voltage available"""
        return self._get_iio_dev_attr_str("reference_select_available")

    @property
    def reference_select(self):
        """AD5710r reference voltage config"""
        return self._get_iio_dev_attr_str("reference_select")

    @reference_select.setter
    def reference_select(self, value):
        if value in self.reference_select_available:
            self._set_iio_dev_attr_str("reference_select", value)
        else:
            raise ValueError(
                "Error: Reference select not supported \nUse one of: "
                + str(self.reference_select_available)
            )

    @property
    def sw_ldac_trigger_avail(self):
        """AD5710r sw_ldac_trigger available"""
        return self._get_iio_dev_attr_str("sw_ldac_trigger_available")

    @property
    def sw_ldac_trigger(self):
        """AD5710r software ldac trigger config"""
        return self._get_iio_dev_attr_str("sw_ldac_trigger")

    @sw_ldac_trigger.setter
    def sw_ldac_trigger(self, value):
        if value in self.sw_ldac_trigger_avail:
            self._set_iio_dev_attr_str("sw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: Trigger value not supported \nUse one of: "
                + str(self.sw_ldac_trigger_avail)
            )

    @property
    def hw_ldac_trigger_avail(self):
        """AD5710r hw_ldac_trigger available"""
        return self._get_iio_dev_attr_str("hw_ldac_trigger_available")

    @property
    def hw_ldac_trigger(self):
        """AD5710r hardware ldac trigger config"""
        return self._get_iio_dev_attr_str("hw_ldac_trigger")

    @hw_ldac_trigger.setter
    def hw_ldac_trigger(self, value):
        if value in self.hw_ldac_trigger_avail:
            self._set_iio_dev_attr_str("hw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: Trigger value not supported \nUse one of: "
                + str(self.hw_ldac_trigger_avail)
            )

    @property
    def range_avail(self):
        """AD5710r range available"""
        return self._get_iio_dev_attr_str("range_available")

    @property
    def range(self):
        """AD5710r range config"""
        return self._get_iio_dev_attr_str("range")

    @range.setter
    def range(self, value):
        if value in self.range_avail:
            self._set_iio_dev_attr_str("range", value)
        else:
            raise ValueError(
                "Error: Range option not supported \nUse one of: "
                + str(self.range_avail)
            )

    @property
    def mux_out_select_avail(self):
        """AD5710r mux_out_select available"""
        return self._get_iio_dev_attr_str("mux_out_select_available")

    @property
    def mux_out_select(self):
        """AD5710r mux out select"""
        return self._get_iio_dev_attr_str("mux_out_select")

    @mux_out_select.setter
    def mux_out_select(self, value):
        if value in self.mux_out_select_avail:
            self._set_iio_dev_attr_str("mux_out_select", value)
        else:
            raise ValueError(
                "Error: Mux output option not supported \nUse one of: "
                + str(self.mux_out_select_avail)
            )

    ############################################################################

    class _channel(attribute):
        """AD5710r channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        ### Add channel attributes here ###
        @property
        def input_register(self):
            """AD5710r channel input register value"""
            return self._get_iio_attr(self.name, "input_register", True)

        @input_register.setter
        def input_register(self, value):
            self._set_iio_attr(self.name, "input_register", True, str(int(value)))

        @property
        def raw(self):
            """AD5710r channel raw value"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def offset(self):
            """AD5710r channel offset"""
            return self._get_iio_attr(self.name, "offset", True)

        @property
        def scale(self):
            """AD5710r channel scale"""
            return self._get_iio_attr(self.name, "scale", True)

        @property
        def ch_mode_avail(self):
            """Ad5710r channel modes available"""
            return self._get_iio_attr_str(self.name, "ch_mode_available", True)

        @property
        def ch_mode(self):
            """Ad5710r channel mode config"""
            return self._get_iio_attr_str(self.name, "ch_mode", True)

        @ch_mode.setter
        def ch_mode(self, value):
            if value in self.ch_mode_avail:
                self._set_iio_attr(self.name, "ch_mode", True, value)
            else:
                raise ValueError(
                    "Error: Channel mode not supported \nUse one of: "
                    + str(self.ch_mode_avail)
                )

        @property
        def operating_mode_avail(self):
            """AD5710r channel operating mode settings"""
            return self._get_iio_attr_str(self.name, "operating_mode_available", True)

        @property
        def operating_mode(self):
            """AD5710r channel operating mode"""
            return self._get_iio_attr_str(self.name, "operating_mode", True)

        @operating_mode.setter
        def operating_mode(self, value):
            if value in self.operating_mode_avail:
                self._set_iio_attr(self.name, "operating_mode", True, value)
            else:
                raise ValueError(
                    "Error: Operating mode not supported \nUse one of: "
                    + str(self.operating_mode_avail)
                )

        #####################################################################
