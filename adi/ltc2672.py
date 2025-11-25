# Copyright (C) 2024-2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class ltc2672(context_manager, attribute):
    """LTC2672 DAC"""

    _complex_data = False
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Constructor for LTC2672 class"""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ltc2662-12", "ltc2662-16", "ltc2672-12", "ltc2672-16"]

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
    def sampling_frequency(self):
        """Get sampling frequency value"""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        """Get sampling frequency value"""
        self._set_iio_dev_attr_str("sampling_frequency", value)

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
                + str(self.all_chns_span_avail)
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
    def all_chns_input_register_and_update(self):
        """Get input register and update value in mA"""
        return self._get_iio_dev_attr_str("all_chns_input_register_and_update")

    @all_chns_input_register_and_update.setter
    def all_chns_input_register_and_update(self, value):
        """Set input register and update value in mA"""
        self._set_iio_dev_attr_str("all_chns_input_register_and_update", value)

    @property
    def powerdown_chip(self):
        """Get powerdown value"""
        return self._get_iio_dev_attr_str("powerdown_chip")

    @property
    def powerdown_chip_avail(self):
        """Get powerdown options"""
        return self._get_iio_dev_attr_str("powerdown_chip_available")

    @powerdown_chip.setter
    def powerdown_chip(self, value):
        """Powerdown the chip"""
        if value in self.powerdown_chip_avail:
            self._set_iio_dev_attr_str("powerdown_chip", value)
        else:
            raise ValueError(
                "Error: powerdown option not supported \nUse one of: "
                + str(self.powerdown_chip_avail)
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
        """Set mux value"""
        if value in self.mux_avail:
            self._set_iio_dev_attr_str("mux", value)
        else:
            raise ValueError(
                "Error: mux setting not supported \nUse one of: " + str(self.mux_avail)
            )

    @property
    def readback(self):
        """Get readback value"""
        return self._get_iio_dev_attr_str("readback")

    @property
    def reset(self):
        """Get reset value"""
        return self._get_iio_dev_attr_str("reset")

    @property
    def reset_avail(self):
        """Get reset options"""
        return self._get_iio_dev_attr_str("reset_available")

    @reset.setter
    def reset(self, value):
        """Reset the device using CLR pin"""
        if value in self.reset_avail:
            self._set_iio_dev_attr_str("reset", value)
        else:
            raise ValueError(
                "Error: reset option not supported \nUse one of: "
                + str(self.reset_avail)
            )

    @property
    def toggle_pin_state(self):
        """Get toggle pin state"""
        return self._get_iio_dev_attr_str("toggle_pin_state")

    @property
    def toggle_pin_state_avail(self):
        """Get toggle pin state options"""
        return self._get_iio_dev_attr_str("toggle_pin_state_available")

    @toggle_pin_state.setter
    def toggle_pin_state(self, value):
        """Set toggle pin state"""
        if value in self.toggle_pin_state_avail:
            self._set_iio_dev_attr_str("toggle_pin_state", value)
        else:
            raise ValueError(
                "Error: toggle pin state option not supported \nUse one of: "
                + str(self.toggle_pin_state_avail)
            )

    @property
    def toggle_pwm(self):
        """Get toggle PWM value"""
        return self._get_iio_dev_attr_str("toggle_pwm")

    @property
    def toggle_pwm_avail(self):
        """Get toggle PWM options"""
        return self._get_iio_dev_attr_str("toggle_pwm_available")

    @toggle_pwm.setter
    def toggle_pwm(self, value):
        """Configure toggle PWM"""
        if value in self.toggle_pwm_avail:
            self._set_iio_dev_attr_str("toggle_pwm", value)
        else:
            raise ValueError(
                "Error: toggle PWM option not supported \nUse one of: "
                + str(self.toggle_pwm_avail)
            )

    @property
    def all_chns_input_register_a(self):
        """Get input register A value in mA"""
        return self._get_iio_dev_attr_str("all_chns_input_register_a")

    @all_chns_input_register_a.setter
    def all_chns_input_register_a(self, value):
        """Set input register A value"""
        self._set_iio_dev_attr_str("all_chns_input_register_a", value)

    @property
    def all_chns_input_register_b(self):
        """Get input register B value in mA"""
        return self._get_iio_dev_attr_str("all_chns_input_register_b")

    @all_chns_input_register_b.setter
    def all_chns_input_register_b(self, value):
        """Set input register B value"""
        self._set_iio_dev_attr_str("all_chns_input_register_b", value)

    @property
    def hw_ldac_update(self):
        """Get HW LDAC update value"""
        return self._get_iio_dev_attr_str("hw_ldac_update")

    @property
    def hw_ldac_update_avail(self):
        """Get HW LDAC update options"""
        return self._get_iio_dev_attr_str("hw_ldac_update_available")

    @hw_ldac_update.setter
    def hw_ldac_update(self, value):
        """Update using the LDAC pin"""
        if value in self.hw_ldac_update_avail:
            self._set_iio_dev_attr_str("hw_ldac_update", value)
        else:
            raise ValueError(
                "Error: update option not supported \nUse one of: "
                + str(self.hw_ldac_update_avail)
            )

    @property
    def all_chns_sw_update(self):
        """Get SW update value"""
        return self._get_iio_dev_attr_str("all_chns_sw_update")

    @property
    def all_chns_sw_update_avail(self):
        """Get SW update options"""
        return self._get_iio_dev_attr_str("all_chns_sw_update_available")

    @all_chns_sw_update.setter
    def all_chns_sw_update(self, value):
        """Update using the SW command"""
        if value in self.all_chns_sw_update_avail:
            self._set_iio_dev_attr_str("all_chns_sw_update", value)
        else:
            raise ValueError(
                "Error: update option not supported \nUse one of: "
                + str(self.all_chns_sw_update_avail)
            )

    @property
    def fault_alert(self):
        """Get fault alert value"""
        return self._get_iio_dev_attr_str("fault_alert")

    @property
    def fault_alert_avail(self):
        """Get fault alert options"""
        return self._get_iio_dev_attr_str("fault_alert_available")

    @property
    def open_circuit_detection(self):
        """Get open circuit detection value"""
        return self._get_iio_dev_attr_str("open_circuit_detection")

    @property
    def open_circuit_detection_avail(self):
        """Get open circuit detection options"""
        return self._get_iio_dev_attr_str("open_circuit_detection_available")

    @open_circuit_detection.setter
    def open_circuit_detection(self, value):
        """Configure open circuit detection"""
        if value in self.open_circuit_detection_avail:
            self._set_iio_dev_attr_str("open_circuit_detection", value)
        else:
            raise ValueError(
                "Error: open circuit detection option not supported \nUse one of: "
                + str(self.open_circuit_detection_avail)
            )

    @property
    def thermal_shutdown_protection(self):
        """Get thermal shutdown protection value"""
        return self._get_iio_dev_attr_str("thermal_shutdown_protection")

    @property
    def thermal_shutdown_protection_avail(self):
        """Get thermal shutdown protection options"""
        return self._get_iio_dev_attr_str("thermal_shutdown_protection_available")

    @thermal_shutdown_protection.setter
    def thermal_shutdown_protection(self, value):
        """Configure thermal shutdown protection"""
        if value in self.thermal_shutdown_protection_avail:
            self._set_iio_dev_attr_str("thermal_shutdown_protection", value)
        else:
            raise ValueError(
                "Error: thermal shutdown protection option not supported \nUse one of: "
                + str(self.thermal_shutdown_protection_avail)
            )

    @property
    def external_reference(self):
        """Get external reference value"""
        return self._get_iio_dev_attr_str("external_reference")

    @property
    def external_reference_avail(self):
        """Get external reference options"""
        return self._get_iio_dev_attr_str("external_reference_available")

    @external_reference.setter
    def external_reference(self, value):
        """Configure external reference"""
        if value in self.external_reference_avail:
            self._set_iio_dev_attr_str("external_reference", value)
        else:
            raise ValueError(
                "Error: external reference option not supported \nUse one of: "
                + str(self.external_reference_avail)
            )

    @property
    def sw_toggle_state(self):
        """Get software toggle state"""
        return self._get_iio_dev_attr_str("sw_toggle_state")

    @property
    def sw_toggle_state_avail(self):
        """Get software toggle state options"""
        return self._get_iio_dev_attr_str("sw_toggle_state_available")

    @sw_toggle_state.setter
    def sw_toggle_state(self, value):
        """Configure software toggle state"""
        if value in self.sw_toggle_state_avail:
            self._set_iio_dev_attr_str("sw_toggle_state", value)
        else:
            raise ValueError(
                "Error: software toggle state option not supported \nUse one of: "
                + str(self.sw_toggle_state_avail)
            )

    @property
    def over_temperature_fault(self):
        """Get over temperature fault value"""
        return self._get_iio_dev_attr_str("over_temperature_fault")

    @property
    def over_temperature_fault_avail(self):
        """Get over temperature fault options"""
        return self._get_iio_dev_attr_str("over_temperature_fault_available")

    @property
    def invalid_spi_seq_length(self):
        """Get invalid SPI sequence length value"""
        return self._get_iio_dev_attr_str("invalid_spi_seq_length")

    @property
    def invalid_spi_seq_length_avail(self):
        """Get invalid SPI sequence length options"""
        return self._get_iio_dev_attr_str("invalid_spi_seq_length_available")

    @property
    def reference_in_volts(self):
        """Get reference value in volts"""
        return self._get_iio_dev_attr_str("reference_in_volts")

    @reference_in_volts.setter
    def reference_in_volts(self, value):
        """Set reference value in volts"""
        self._set_iio_dev_attr_str("reference_in_volts", value)

    @property
    def fsadj_res_in_kohm(self):
        """Get FSADJ resistor value in k-ohm"""
        return self._get_iio_dev_attr_str("fsadj_res_in_kohm")

    @fsadj_res_in_kohm.setter
    def fsadj_res_in_kohm(self, value):
        """Set FSADJ resistor value in k-ohm"""
        self._set_iio_dev_attr_str("fsadj_res_in_kohm", value)

    @property
    def no_op_cmd(self):
        """Get no operation command value"""
        return self._get_iio_dev_attr_str("no_op_cmd")

    @property
    def no_op_cmd_avail(self):
        """Get no operation command options"""
        return self._get_iio_dev_attr_str("no_op_cmd_available")

    @no_op_cmd.setter
    def no_op_cmd(self, value):
        """Send no operation command"""
        if value in self.no_op_cmd_avail:
            self._set_iio_dev_attr_str("no_op_cmd", value)
        else:
            raise ValueError(
                "Error: command option not supported \nUse one of: "
                + str(self.no_op_cmd_avail)
            )

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
        def input_register_and_update(self):
            """Get channel value of input and update in mA"""
            return self._get_iio_attr(self.name, "input_register_and_update", True)

        @input_register_and_update.setter
        def input_register_and_update(self, value):
            """Set channel value of input and update in mA"""
            self._set_iio_attr(self.name, "input_register_and_update", True, value)

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
                    + str(self.span_avail)
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
                    + str(self.powerdown_avail)
                )

        @property
        def input_register_a(self):
            """Get channel input register A value in mA"""
            return self._get_iio_attr(self.name, "input_register_a", True)

        @input_register_a.setter
        def input_register_a(self, value):
            """Set channel input register A value"""
            self._set_iio_attr(self.name, "input_register_a", True, value)

        @property
        def input_register_b(self):
            """Get channel input register B value in mA"""
            return self._get_iio_attr(self.name, "input_register_b", True)

        @input_register_b.setter
        def input_register_b(self, value):
            """Set channel input register B value"""
            self._set_iio_attr(self.name, "input_register_b", True, value)

        @property
        def sw_update(self):
            """Get channel SW update value"""
            return self._get_iio_attr_str(self.name, "sw_update", True)

        @property
        def sw_update_avail(self):
            """Get channel SW update options"""
            return self._get_iio_attr_str(self.name, "sw_update_available", True)

        @sw_update.setter
        def sw_update(self, value):
            """Update the channel using SW command"""
            if value in self.sw_update_avail:
                self._set_iio_attr(self.name, "sw_update", True, value)
            else:
                raise ValueError(
                    "Error: SW update option not supported \nUse one of: "
                    + str(self.sw_update_avail)
                )

        @property
        def input_register_and_update_all_chns(self):
            """Set input register and update all channels value in mA"""
            return self._get_iio_attr(
                self.name, "input_register_and_update_all_chns", True
            )

        @input_register_and_update_all_chns.setter
        def input_register_and_update_all_chns(self, value):
            """Set input register and update all channels value"""
            self._set_iio_attr(
                self.name, "input_register_and_update_all_chns", True, value
            )

        @property
        def toggle_select(self):
            """Get channel toggle select value"""
            return self._get_iio_attr_str(self.name, "toggle_select", True)

        @property
        def toggle_select_avail(self):
            """Get channel toggle select options"""
            return self._get_iio_attr_str(self.name, "toggle_select_available", True)

        @toggle_select.setter
        def toggle_select(self, value):
            """Configure channel toggle select"""
            if value in self.toggle_select_avail:
                self._set_iio_attr(self.name, "toggle_select", True, value)
            else:
                raise ValueError(
                    "Error: channel toggle select option not supported \nUse one of: "
                    + str(self.toggle_select_avail)
                )

        @property
        def open_circuit_fault(self):
            """Get channel open circuit fault value"""
            return self._get_iio_attr_str(self.name, "open_circuit_fault", True)

        @property
        def open_circuit_fault_avail(self):
            """Get channel open circuit fault options"""
            return self._get_iio_attr_str(
                self.name, "open_circuit_fault_available", True
            )
