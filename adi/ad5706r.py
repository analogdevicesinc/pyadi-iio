# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


from decimal import Decimal

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad5706r(tx, context_manager):
    """ ad5706r DAC """

    _complex_data = False
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for ad5706r class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad5706r"]

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
        """AD5706r channel-wise number of output bits list"""
        return self._output_bits

    @property
    def sampling_frequency(self):
        """ad5706r sampling frequency config"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    @property
    def dev_addr(self):
        """AD5706R multi-drop spi address config"""
        return self._get_iio_dev_attr_str("dev_addr")

    @dev_addr.setter
    def dev_addr(self, value):
        """Set device address."""
        self._set_iio_dev_attr_str("dev_addr", value)

    @property
    def addr_ascension(self):
        """AD5706R Address Ascension"""
        return self._get_iio_dev_attr_str("addr_ascension")

    @property
    def addr_ascension_available(self):
        """addr_ascension_available: Options are:
        descending, ascending"""
        return self._get_iio_dev_attr_str("addr_ascension_available")

    @addr_ascension.setter
    def addr_ascension(self, value):
        """Configure the Address Ascension."""
        if value in self.addr_ascension_available:
            self._set_iio_dev_attr_str("addr_ascension", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.addr_ascension_available)
            )

    @property
    def single_instr(self):
        """ad5706r Single instruction"""
        return self._get_iio_dev_attr_str("single_instr")

    @property
    def single_instr_available(self):
        """single_instr_available: Options are:
        single_instruction, streaming"""
        return self._get_iio_dev_attr_str("single_instr_available")

    @single_instr.setter
    def single_instr(self, value):
        """Configure the Address Ascension."""
        if value in self.single_instr_available:
            self._set_iio_dev_attr_str("single_instr", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.single_instr_available)
            )

    @property
    def hw_ldac_tg_state(self):
        """ad5706r HW LDAC/TG PWM"""
        return self._get_iio_dev_attr_str("hw_ldac_tg_state")

    @property
    def hw_ldac_tg_state_available(self):
        """hw_ldac_tg_state_available: Options are:
        low, high"""
        return self._get_iio_dev_attr_str("hw_ldac_tg_state_available")

    @hw_ldac_tg_state.setter
    def hw_ldac_tg_state(self, value):
        """Toggle the HW LDAC/TG pin."""
        if value in self.hw_ldac_tg_state_available:
            self._set_iio_dev_attr_str("hw_ldac_tg_state", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.hw_ldac_tg_state_available)
            )

    @property
    def hw_shutdown_state(self):
        """ad5706r HW Shutdown State"""
        return self._get_iio_dev_attr_str("hw_shutdown_state")

    @property
    def hw_shutdown_state_available(self):
        """hw_shutdown_state_available: Options are:
        low, high"""
        return self._get_iio_dev_attr_str("hw_shutdown_state_available")

    @hw_shutdown_state.setter
    def hw_shutdown_state(self, value):
        """Toggle the HW Shutdown pin."""
        if value in self.hw_shutdown_state_available:
            self._set_iio_dev_attr_str("hw_shutdown_state", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.hw_shutdown_state_available)
            )

    @property
    def mux_out_sel(self):
        """ad5706r Mux Output Select"""
        return self._get_iio_dev_attr_str("mux_out_sel")

    @property
    def mux_out_sel_available(self):
        """mux_out_sel_available: Options are:
        agnd, avdd, vref, agnd, iout0_vmon, iout1_vmon, iout2_vmon, iout3_vmon,
        iout0_imon, iout1_imon, iout2_imon, iout3_imon, pvdd0, pvdd1, pvdd2, pvdd3
        tdiode_ch0, tdiode_ch1, tdiode_ch2, tdiode_ch3, mux_in0, mux_in1, mux_in2, mux_in03"""
        return self._get_iio_dev_attr_str("mux_out_sel_available")

    @mux_out_sel.setter
    def mux_out_sel(self, value):
        """Configure the Mux output."""
        if value in self.mux_out_sel_available:
            self._set_iio_dev_attr_str("mux_out_sel", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.mux_out_sel_available)
            )

    @property
    def ref_select(self):
        """ad5706r Reference Select"""
        return self._get_iio_dev_attr_str("ref_select")

    @property
    def ref_select_available(self):
        """ref_select_available: Options are:
        internal, external"""
        return self._get_iio_dev_attr_str("ref_select_available")

    @ref_select.setter
    def ref_select(self, value):
        """Configure the reference select."""
        if value in self.ref_select_available:
            self._set_iio_dev_attr_str("ref_select", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.ref_select_available)
            )

    @property
    def multi_dac_sw_ldac_trigger(self):
        """ad5706r Multi DAC SW LDAC Trigger"""
        return self._get_iio_dev_attr_str("multi_dac_sw_ldac_trigger")

    @property
    def multi_dac_sw_ldac_trigger_available(self):
        """multi_dac_sw_ldac_trigger_available: Options are:
        trigger"""
        return self._get_iio_dev_attr_str("multi_dac_sw_ldac_trigger_available")

    @multi_dac_sw_ldac_trigger.setter
    def multi_dac_sw_ldac_trigger(self, value):
        """Configure the Multi DAC SW LDAC Trigger."""
        if value in self.multi_dac_sw_ldac_trigger:
            self._set_iio_dev_attr_str("multi_dac_sw_ldac_trigger", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.multi_dac_sw_ldac_trigger_available)
            )

    @property
    def hw_ldac_tg_pwm(self):
        """ad5706r HW LDAC/TG PWM"""
        return self._get_iio_dev_attr_str("hw_ldac_tg_pwm")

    @property
    def hw_ldac_tg_pwm_available(self):
        """hw_ldac_tg_pwm_available: Options are:
        disable, enable"""
        return self._get_iio_dev_attr_str("hw_ldac_tg_pwm_available")

    @hw_ldac_tg_pwm.setter
    def hw_ldac_tg_pwm(self, value):
        """Enable/Disable the HW LDAC/TG PWM."""
        if value in self.hw_ldac_tg_pwm_available:
            self._set_iio_dev_attr_str("hw_ldac_tg_pwm", value)
        else:
            raise ValueError(
                "Error: Attribute value not supported \nUse one of: "
                + str(self.hw_ldac_tg_pwm_available)
            )

    @property
    def reference_volts(self):
        """ad5706r Reference value"""
        return float(self._get_iio_dev_attr_str("reference_volts"))

    @reference_volts.setter
    def reference_volts(self, value):
        """Set the ad5706r Reference value"""
        self._set_iio_dev_attr_str("reference_volts", value)

    @property
    def multi_dac_input_a(self):
        """ad5706r Multi DAC Input Register A value"""
        return int(self._get_iio_dev_attr("multi_dac_input_a"))

    @multi_dac_input_a.setter
    def multi_dac_input_a(self, value):
        """Set the ad5706r Multi DAC Input Register A value"""
        self._set_iio_dev_attr_str("multi_dac_input_a", value)

    class _channel(attribute):
        """ad5706r channel"""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ad5706r channel raw value"""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def offset(self):
            """ad5706r channel offset"""
            return self._get_iio_attr(self.name, "offset", True)

        @offset.setter
        def offset(self, value):
            self._set_iio_attr(self.name, "offset", True, str(Decimal(value).real))

        @property
        def scale(self):
            """ad5706r channel scale"""
            return self._get_iio_attr(self.name, "scale", True)

        @scale.setter
        def scale(self, value):
            self._set_iio_attr(self.name, "scale", True, str(Decimal(value).real))

        @property
        def input_register_a(self):
            """ad5706r channel Input Register A value"""
            return int(self._get_iio_attr_str(self.name, "input_register_a", True))

        @input_register_a.setter
        def input_register_a(self, value):
            """Set the ad5706r channel Input Register A value"""
            self._set_iio_attr(self.name, "input_register_a", True, value)

        @property
        def input_register_b(self):
            """ad5706r channel Input Register B value"""
            return int(self._get_iio_attr_str(self.name, "input_register_b", True))

        @input_register_b.setter
        def input_register_b(self, value):
            """Set the ad5706r channel Input Register B value"""
            self._set_iio_attr(self.name, "input_register_b", True, value)

        @property
        def hw_active_edge(self):
            """ad5706r channel HW active edge"""
            return self._get_iio_attr_str(self.name, "hw_active_edge", True)

        @property
        def hw_active_edge_available(self):
            """ad5706r channel HW active edge options. Options are:
            rising_edge, falling_edge, any_edge"""
            return self._get_iio_attr_str(self.name, "hw_active_edge_available", True)

        @hw_active_edge.setter
        def hw_active_edge(self, value):
            """Set the HW active edge for the channel."""
            if value in self.hw_active_edge_available:
                self._set_iio_attr(self.name, "hw_active_edge", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.hw_active_edge_available)
                )

        @property
        def multi_dac_sel_ch(self):
            """ad5706r Multi DAC channel select"""
            return self._get_iio_attr_str(self.name, "multi_dac_sel_ch", True)

        @property
        def multi_dac_sel_ch_available(self):
            """ad5706r Multi DAC Channel Select options. Options are:
            exclude, include"""
            return self._get_iio_attr_str(self.name, "multi_dac_sel_ch_available", True)

        @multi_dac_sel_ch.setter
        def multi_dac_sel_ch(self, value):
            """Set the Multi DAC Channel."""
            if value in self.multi_dac_sel_ch_available:
                self._set_iio_attr(self.name, "multi_dac_sel_ch", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.multi_dac_sel_ch_available)
                )

        @property
        def range_sel(self):
            """ad5706r channel range selection"""
            return self._get_iio_attr_str(self.name, "range_sel", True)

        @property
        def range_sel_available(self):
            """ad5706r channel range options. Options are:
            50mA, 150mA, 200mA, 300mA"""
            return self._get_iio_attr_str(self.name, "range_sel_available", True)

        @range_sel.setter
        def range_sel(self, value):
            """Set the range for the channel."""
            if value in self.range_sel_available:
                self._set_iio_attr(self.name, "range_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.range_sel_available)
                )

        @property
        def ldac_trigger_chn(self):
            """ad5706r LDAC Trigger Chn setting"""
            return self._get_iio_attr_str(self.name, "ldac_trigger_chn", True)

        @property
        def ldac_trigger_chn_available(self):
            """ad5706r channel LDAC trigger options. Options are:
            None, sw_ldac, hw_ldac"""
            return self._get_iio_attr_str(self.name, "ldac_trigger_chn_available", True)

        @ldac_trigger_chn.setter
        def ldac_trigger_chn(self, value):
            """Trigger LDAC for the channel."""
            if value in self.ldac_trigger_chn_available:
                self._set_iio_attr(self.name, "ldac_trigger_chn", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.ldac_trigger_chn_available)
                )

        @property
        def toggle_trigger_chn(self):
            """ad5706r Toggle Trigger Chn setting"""
            return self._get_iio_attr_str(self.name, "toggle_trigger_chn", True)

        @property
        def toggle_trigger_chn_available(self):
            """ad5706r channel Toggle trigger options. Options are:
            None, sw_toggle, hw_toggle"""
            return self._get_iio_attr_str(
                self.name, "toggle_trigger_chn_available", True
            )

        @toggle_trigger_chn.setter
        def toggle_trigger_chn(self, value):
            """Trigger Toggle for the channel."""
            if value in self.toggle_trigger_chn_available:
                self._set_iio_attr(self.name, "toggle_trigger_chn", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.toggle_trigger_chn_available)
                )

        @property
        def hw_func_sel(self):
            """ad5706r HW function setting"""
            return self._get_iio_attr_str(self.name, "hw_func_sel", True)

        @property
        def hw_func_sel_available(self):
            """ad5706r channel HW function options. Options are:
            None, LDAC, Toggle, Dither"""
            return self._get_iio_attr_str(self.name, "hw_func_sel_available", True)

        @hw_func_sel.setter
        def hw_func_sel(self, value):
            """Set HW function for the channel."""
            if value in self.hw_func_sel_available:
                self._set_iio_attr(self.name, "hw_func_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.hw_func_sel_available)
                )

        @property
        def output_state(self):
            """ad5706r channel output state setting"""
            return self._get_iio_attr_str(self.name, "output_state", True)

        @property
        def output_state_available(self):
            """ad5706r channel output state options. Options are:
            shutdown_to_tristate_sw, shutdown_to_gnd_sw, normal_sw,
            shutdown_to_tristate_hw, shutdown_to_gnd_hw, normal_hw"""
            return self._get_iio_attr_str(self.name, "output_state_available", True)

        @output_state.setter
        def output_state(self, value):
            """Set output state for the channel."""
            if value in self.output_state_available:
                self._set_iio_attr(self.name, "output_state", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.output_state_available)
                )
