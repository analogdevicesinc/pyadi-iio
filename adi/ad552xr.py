# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""AD552XR DAC driver."""

from adi.attribute import attribute
from adi.context_manager import context_manager
from adi.rx_tx import tx


class ad552xr(tx, context_manager):
    """ad552xr DAC."""

    _complex_data = False
    _device_name = ""

    def __init__(self, uri="", device_name=""):
        """Initialize ad552xr class."""
        context_manager.__init__(self, uri, self._device_name)

        compatible_parts = ["ad5529r"]

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

        self._output_bits = []
        self.channel = []
        for ch in self._ctrl.channels:
            name = ch.id
            self._output_bits.append(ch.data_format.bits)
            self._tx_channel_names.append(name)
            self.channel.append(self._channel(self._ctrl, name))
            setattr(self, name, self._channel(self._ctrl, name))

        tx.__init__(self)

    @property
    def output_bits(self):
        """ad552xr channel-wise number of output bits list."""
        return self._output_bits

    @property
    def sampling_frequency(self):
        """ad552xr sampling frequency config."""
        return self._get_iio_dev_attr_str("sampling_frequency")

    @sampling_frequency.setter
    def sampling_frequency(self, value):
        self._set_iio_dev_attr_str("sampling_frequency", value)

    class _channel(attribute):
        """ad552xr channel."""

        def __init__(self, ctrl, channel_name):
            self.name = channel_name
            self._ctrl = ctrl

        @property
        def raw(self):
            """ad552xr channel raw value."""
            return self._get_iio_attr(self.name, "raw", True)

        @raw.setter
        def raw(self, value):
            self._set_iio_attr(self.name, "raw", True, str(int(value)))

        @property
        def offset(self):
            """ad552xr channel offset, read-only."""
            return self._get_iio_attr(self.name, "offset", True)

        @property
        def scale(self):
            """ad552xr channel scale, read-only."""
            return self._get_iio_attr(self.name, "scale", True)

        @property
        def input_register_a(self):
            """ad552xr channel Input Register A value."""
            return int(self._get_iio_attr_str(self.name, "input_register_a", True))

        @input_register_a.setter
        def input_register_a(self, value):
            """Set the ad552xr channel Input Register A value."""
            self._set_iio_attr(self.name, "input_register_a", True, value)

        @property
        def input_register_b(self):
            """ad552xr channel Input Register B value."""
            return int(self._get_iio_attr_str(self.name, "input_register_b", True))

        @input_register_b.setter
        def input_register_b(self, value):
            """Set the ad552xr channel Input Register B value."""
            self._set_iio_attr(self.name, "input_register_b", True, value)

        @property
        def output_state(self):
            """ad552xr channel output selection."""
            return self._get_iio_attr_str(self.name, "output_state", True)

        @property
        def output_state_available(self):
            """
            ad552xr channel output state options.

            Options are: disable, enable.
            """
            return self._get_iio_attr_str(self.name, "output_state_available", True)

        @output_state.setter
        def output_state(self, value):
            """Set the output state for the channel."""
            if value in self.output_state_available:
                self._set_iio_attr(self.name, "output_state", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.output_state_available)
                )

        @property
        def hw_sw_sel(self):
            """ad552xr channel hw/sw selection."""
            return self._get_iio_attr_str(self.name, "hw_sw_sel", True)

        @property
        def hw_sw_sel_available(self):
            """
            ad552xr channel hw/sw options.

            Options are: hw, sw.
            """
            return self._get_iio_attr_str(self.name, "hw_sw_sel_available", True)

        @hw_sw_sel.setter
        def hw_sw_sel(self, value):
            """Set the hw/sw for the channel."""
            if value in self.hw_sw_sel_available:
                self._set_iio_attr(self.name, "hw_sw_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.hw_sw_sel_available)
                )

        @property
        def func_sel(self):
            """ad552xr HW function setting."""
            return self._get_iio_attr_str(self.name, "func_sel", True)

        @property
        def func_sel_available(self):
            """
            ad552xr channel HW function options.

            Options are: disable, ldac_toggle, dither, sawtooth, triangular.
            """
            return self._get_iio_attr_str(self.name, "func_sel_available", True)

        @func_sel.setter
        def func_sel(self, value):
            """Set HW function for the channel."""
            if value in self.func_sel_available:
                self._set_iio_attr(self.name, "func_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.func_sel_available)
                )

        @property
        def hw_ldac_pin_sel(self):
            """ad552xr channel HW active pin."""
            return self._get_iio_attr_str(self.name, "hw_ldac_pin_sel", True)

        @property
        def hw_ldac_pin_sel_available(self):
            """
            ad552xr channel HW active pin options.

            Options are: ldac_toggle_0, ldac_toggle_1, ldac_toggle_2, ldac_toggle_3.
            """
            return self._get_iio_attr_str(self.name, "hw_ldac_pin_sel_available", True)

        @hw_ldac_pin_sel.setter
        def hw_ldac_pin_sel(self, value):
            """Set the HW active pin for the channel."""
            if value in self.hw_ldac_pin_sel_available:
                self._set_iio_attr(self.name, "hw_ldac_pin_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.hw_ldac_pin_sel_available)
                )

        @property
        def hw_ldac_edge_sel(self):
            """ad552xr channel HW active edge."""
            return self._get_iio_attr_str(self.name, "hw_ldac_edge_sel", True)

        @property
        def hw_ldac_edge_sel_available(self):
            """
            ad552xr channel HW active edge options.

            Options are: rising_edge, falling_edge, any_edge.
            """
            return self._get_iio_attr_str(self.name, "hw_ldac_edge_sel_available", True)

        @hw_ldac_edge_sel.setter
        def hw_ldac_edge_sel(self, value):
            """Set the HW active edge for the channel."""
            if value in self.hw_ldac_edge_sel_available:
                self._set_iio_attr(self.name, "hw_ldac_edge_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.hw_ldac_edge_sel_available)
                )

        @property
        def dither_period_factor(self):
            """ad552xr Dither period factor setting."""
            return self._get_iio_attr_str(self.name, "dither_period_factor", True)

        @property
        def dither_period_factor_available(self):
            """
            ad552xr channel Dither period factor options.

            Options are: 2, 4, 8, 16, 32, 64, 128.
            """
            return self._get_iio_attr_str(
                self.name, "dither_period_factor_available", True
            )

        @dither_period_factor.setter
        def dither_period_factor(self, value):
            """Dither period factor for the channel."""
            if value in self.dither_period_factor_available:
                self._set_iio_attr(self.name, "dither_period_factor", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.dither_period_factor_available)
                )

        @property
        def dither_phase(self):
            """ad552xr Dither phase setting."""
            return self._get_iio_attr_str(self.name, "dither_phase", True)

        @property
        def dither_phase_available(self):
            """
            ad552xr channel Dither phase options.

            Options are: 0, 90, 180, 270.
            """
            return self._get_iio_attr_str(self.name, "dither_phase_available", True)

        @dither_phase.setter
        def dither_phase(self, value):
            """Dither phase for the channel."""
            if value in self.dither_phase_available:
                self._set_iio_attr(self.name, "dither_phase", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.dither_phase_available)
                )

        @property
        def ramp_step_size(self):
            """ad552xr channel Ramp step size value."""
            return int(self._get_iio_attr_str(self.name, "ramp_step_size", True))

        @ramp_step_size.setter
        def ramp_step_size(self, value):
            """Set the ad552xr channel Ramp step size value."""
            self._set_iio_attr(self.name, "ramp_step_size", True, value)

        @property
        def range_sel(self):
            """ad552xr channel range selection."""
            return self._get_iio_attr_str(self.name, "range_sel", True)

        @property
        def range_sel_available(self):
            """
            ad552xr channel range selection options.

            Options are: unipolar_5V, unipolar_10V, unipolar_20V, unipolar_40V,
            bipolar_5V, bipolar_10V, bipolar_15V, bipolar_20V.
            """
            return self._get_iio_attr_str(self.name, "range_sel_available", True)

        @range_sel.setter
        def range_sel(self, value):
            """Set the output range for the channel."""
            if value in self.range_sel_available:
                self._set_iio_attr(self.name, "range_sel", True, value)
            else:
                raise ValueError(
                    "Error: Attribute value not supported \nUse one of: "
                    + str(self.range_sel_available)
                )
