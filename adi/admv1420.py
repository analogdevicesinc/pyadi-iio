# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from ctypes import c_char_p, c_size_t, create_string_buffer

from adi.attribute import attribute
from adi.context_manager import context_manager


class admv1420(attribute, context_manager):
    """ADMV1420 Microwave Downconverter

    The ADMV1420 converts RF signals to IF/baseband signals across four RF bands
    (0.1-2 GHz, 1-5 GHz, 3-13 GHz, 6-20 GHz) with selectable IF bands, LO
    sideband, digitally selectable attenuators (DSAs), and filter LUT support.

    parameters:
        uri: type=string
            URI of IIO context with ADMV1420
        device_name: type=string
            IIO device name (e.g., "admv1420_rx_0" on Neponset board)
    """

    _device_name = "admv1420"

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)

        if device_name:
            self._device_name = device_name
        self._ctrl = self._ctx.find_device(self._device_name)

        if not self._ctrl:
            raise Exception("ADMV1420 device not found")

    def _read_dev_attr_large(self, attr_name, bufsize=8192):
        """Read a device attribute using a larger buffer than libiio default.

        The default libiio DeviceAttr._read() uses a 1024-byte buffer which
        is too small for multi-line LUT table attributes.
        """
        import iio as _iio

        buf = create_string_buffer(bufsize)
        _iio._d_read_attr(
            self._ctrl._device, attr_name.encode("ascii"), buf, len(buf)
        )
        return buf.value.decode("ascii")

    # --- RF Channel (in_altvoltage0_rf) ---

    @property
    def rf_band(self):
        """Get/Set the RF band selection.
        Options: 100MHz_2GHz, 1GHz_5GHz, 3GHz_13GHz, 6GHz_20GHz"""
        return self._get_iio_attr_str("altvoltage0", "band", False, self._ctrl)

    @rf_band.setter
    def rf_band(self, value):
        self._set_iio_attr("altvoltage0", "band", False, value, self._ctrl)

    @property
    def rf_band_available(self):
        """Get available RF band selections"""
        return self._get_iio_attr_str(
            "altvoltage0", "band_available", False, self._ctrl
        )

    @property
    def rf_direct_dsa1_gain(self):
        """Get/Set RF DSA1 gain (4-bit, 0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa1_gain", False, self._ctrl
        )

    @rf_direct_dsa1_gain.setter
    def rf_direct_dsa1_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "direct_dsa1_gain", False, value, self._ctrl
        )

    @property
    def rf_direct_dsa2_gain(self):
        """Get/Set RF DSA2 gain (1-bit, 0dB or -6dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa2_gain", False, self._ctrl
        )

    @rf_direct_dsa2_gain.setter
    def rf_direct_dsa2_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "direct_dsa2_gain", False, value, self._ctrl
        )

    @property
    def rf_direct_dsa3_gain(self):
        """Get/Set RF DSA3 gain (4-bit, 0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa3_gain", False, self._ctrl
        )

    @rf_direct_dsa3_gain.setter
    def rf_direct_dsa3_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "direct_dsa3_gain", False, value, self._ctrl
        )

    @property
    def rf_direct_lpf_val(self):
        """Get/Set RF direct LPF value (0-15)"""
        return self._get_iio_attr("altvoltage0", "direct_lpf_val", False, self._ctrl)

    @rf_direct_lpf_val.setter
    def rf_direct_lpf_val(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "direct_lpf_val", False, int(value), self._ctrl
        )

    @property
    def rf_direct_hpf_val(self):
        """Get/Set RF direct HPF value (0-15)"""
        return self._get_iio_attr("altvoltage0", "direct_hpf_val", False, self._ctrl)

    @rf_direct_hpf_val.setter
    def rf_direct_hpf_val(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "direct_hpf_val", False, int(value), self._ctrl
        )

    @property
    def rf_direct_dsa1_offset(self):
        """Get/Set RF DSA1 offset (0-15)"""
        return self._get_iio_attr(
            "altvoltage0", "direct_dsa1_offset", False, self._ctrl
        )

    @rf_direct_dsa1_offset.setter
    def rf_direct_dsa1_offset(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "direct_dsa1_offset", False, int(value), self._ctrl
        )

    @property
    def rf_direct_dsa2_offset(self):
        """Get/Set RF DSA2 offset (0-3)"""
        return self._get_iio_attr(
            "altvoltage0", "direct_dsa2_offset", False, self._ctrl
        )

    @rf_direct_dsa2_offset.setter
    def rf_direct_dsa2_offset(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "direct_dsa2_offset", False, int(value), self._ctrl
        )

    @property
    def rf_direct_dsa3_offset(self):
        """Get/Set RF DSA3 offset (0-15)"""
        return self._get_iio_attr(
            "altvoltage0", "direct_dsa3_offset", False, self._ctrl
        )

    @rf_direct_dsa3_offset.setter
    def rf_direct_dsa3_offset(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "direct_dsa3_offset", False, int(value), self._ctrl
        )

    @property
    def rf_bypass_lpf_en(self):
        """Get/Set RF bypass LPF enable (true/false)"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_lpf_en", False, self._ctrl
        )

    @rf_bypass_lpf_en.setter
    def rf_bypass_lpf_en(self, value):
        self._set_iio_attr("altvoltage0", "bypass_lpf_en", False, value, self._ctrl)

    @property
    def rf_bypass_hpf_en(self):
        """Get/Set RF bypass HPF enable (true/false)"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_hpf_en", False, self._ctrl
        )

    @rf_bypass_hpf_en.setter
    def rf_bypass_hpf_en(self, value):
        self._set_iio_attr("altvoltage0", "bypass_hpf_en", False, value, self._ctrl)

    @property
    def rf_bypass_lpf_val(self):
        """Get/Set RF bypass LPF value"""
        return self._get_iio_attr("altvoltage0", "bypass_lpf_val", False, self._ctrl)

    @rf_bypass_lpf_val.setter
    def rf_bypass_lpf_val(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "bypass_lpf_val", False, int(value), self._ctrl
        )

    @property
    def rf_bypass_hpf_val(self):
        """Get/Set RF bypass HPF value"""
        return self._get_iio_attr("altvoltage0", "bypass_hpf_val", False, self._ctrl)

    @rf_bypass_hpf_val.setter
    def rf_bypass_hpf_val(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "bypass_hpf_val", False, int(value), self._ctrl
        )

    @property
    def rf_bypass_dsa1_gain(self):
        """Get/Set RF bypass DSA1 gain (0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_dsa1_gain", False, self._ctrl
        )

    @rf_bypass_dsa1_gain.setter
    def rf_bypass_dsa1_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "bypass_dsa1_gain", False, value, self._ctrl
        )

    @property
    def rf_bypass_dsa1_gain_available(self):
        """Get available RF bypass DSA1 gain options"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_dsa1_gain_available", False, self._ctrl
        )

    @property
    def rf_bypass_dsa2_gain(self):
        """Get/Set RF bypass DSA2 gain (0dB or -6dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_dsa2_gain", False, self._ctrl
        )

    @rf_bypass_dsa2_gain.setter
    def rf_bypass_dsa2_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "bypass_dsa2_gain", False, value, self._ctrl
        )

    @property
    def rf_bypass_dsa2_gain_available(self):
        """Get available RF bypass DSA2 gain options"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_dsa2_gain_available", False, self._ctrl
        )

    @property
    def rf_bypass_dsa3_gain(self):
        """Get/Set RF bypass DSA3 gain (0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_dsa3_gain", False, self._ctrl
        )

    @rf_bypass_dsa3_gain.setter
    def rf_bypass_dsa3_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "bypass_dsa3_gain", False, value, self._ctrl
        )

    @property
    def rf_bypass_dsa3_gain_available(self):
        """Get available RF bypass DSA3 gain options"""
        return self._get_iio_attr_str(
            "altvoltage0", "bypass_dsa3_gain_available", False, self._ctrl
        )

    @property
    def rf_direct_dsa1_gain_available(self):
        """Get available RF direct DSA1 gain options"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa1_gain_available", False, self._ctrl
        )

    @property
    def rf_direct_dsa2_gain_available(self):
        """Get available RF direct DSA2 gain options"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa2_gain_available", False, self._ctrl
        )

    @property
    def rf_direct_dsa3_gain_available(self):
        """Get available RF direct DSA3 gain options"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa3_gain_available", False, self._ctrl
        )

    # --- IF Channel (out_altvoltage1_if) ---

    @property
    def if_band(self):
        """Get/Set the IF band selection.
        Options: 1GHz_5GHz, 3GHz_13GHz"""
        return self._get_iio_attr_str("altvoltage1", "band", True, self._ctrl)

    @if_band.setter
    def if_band(self, value):
        self._set_iio_attr("altvoltage1", "band", True, value, self._ctrl)

    @property
    def if_band_available(self):
        """Get available IF band selections"""
        return self._get_iio_attr_str(
            "altvoltage1", "band_available", True, self._ctrl
        )

    @property
    def if_mode(self):
        """Get/Set IF mode. Options: baseband, if"""
        return self._get_iio_attr_str("altvoltage1", "mode", True, self._ctrl)

    @if_mode.setter
    def if_mode(self, value):
        self._set_iio_attr("altvoltage1", "mode", True, value, self._ctrl)

    @property
    def if_mode_available(self):
        """Get available IF mode options"""
        return self._get_iio_attr_str(
            "altvoltage1", "mode_available", True, self._ctrl
        )

    @property
    def if_direct_dsa4_gain(self):
        """Get/Set IF DSA4 gain (4-bit, 0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage1", "direct_dsa4_gain", True, self._ctrl
        )

    @if_direct_dsa4_gain.setter
    def if_direct_dsa4_gain(self, value):
        self._set_iio_attr("altvoltage1", "direct_dsa4_gain", True, value, self._ctrl)

    @property
    def if_direct_dsa5_gain(self):
        """Get/Set IF DSA5 gain (4-bit, 0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage1", "direct_dsa5_gain", True, self._ctrl
        )

    @if_direct_dsa5_gain.setter
    def if_direct_dsa5_gain(self, value):
        self._set_iio_attr("altvoltage1", "direct_dsa5_gain", True, value, self._ctrl)

    @property
    def if_dsai_0p1db(self):
        """Get/Set IF I-channel DSA for IMR calibration (0.1dB steps, 0-1.5dB)"""
        return self._get_iio_attr_str("altvoltage1", "dsai_0p1db", True, self._ctrl)

    @if_dsai_0p1db.setter
    def if_dsai_0p1db(self, value):
        self._set_iio_attr("altvoltage1", "dsai_0p1db", True, value, self._ctrl)

    @property
    def if_dsaq_0p1db(self):
        """Get/Set IF Q-channel DSA for IMR calibration (0.1dB steps, 0-1.5dB)"""
        return self._get_iio_attr_str("altvoltage1", "dsaq_0p1db", True, self._ctrl)

    @if_dsaq_0p1db.setter
    def if_dsaq_0p1db(self, value):
        self._set_iio_attr("altvoltage1", "dsaq_0p1db", True, value, self._ctrl)

    @property
    def if_dsai_0p1db_available(self):
        """Get available IF DSAI 0.1dB options"""
        return self._get_iio_attr_str(
            "altvoltage1", "dsai_0p1db_available", True, self._ctrl
        )

    @property
    def if_dsaq_0p1db_available(self):
        """Get available IF DSAQ 0.1dB options"""
        return self._get_iio_attr_str(
            "altvoltage1", "dsaq_0p1db_available", True, self._ctrl
        )

    @property
    def if_direct_dsa4_gain_available(self):
        """Get available IF direct DSA4 gain options"""
        return self._get_iio_attr_str(
            "altvoltage1", "direct_dsa4_gain_available", True, self._ctrl
        )

    @property
    def if_direct_dsa5_gain_available(self):
        """Get available IF direct DSA5 gain options"""
        return self._get_iio_attr_str(
            "altvoltage1", "direct_dsa5_gain_available", True, self._ctrl
        )

    @property
    def if_direct_lpf_val(self):
        """Get/Set IF direct LPF value"""
        return self._get_iio_attr("altvoltage1", "direct_lpf_val", True, self._ctrl)

    @if_direct_lpf_val.setter
    def if_direct_lpf_val(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "direct_lpf_val", True, int(value), self._ctrl
        )

    @property
    def if_direct_dsa4_offset(self):
        """Get/Set IF DSA4 offset"""
        return self._get_iio_attr(
            "altvoltage1", "direct_dsa4_offset", True, self._ctrl
        )

    @if_direct_dsa4_offset.setter
    def if_direct_dsa4_offset(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "direct_dsa4_offset", True, int(value), self._ctrl
        )

    @property
    def if_direct_dsa5_offset(self):
        """Get/Set IF DSA5 offset"""
        return self._get_iio_attr(
            "altvoltage1", "direct_dsa5_offset", True, self._ctrl
        )

    @if_direct_dsa5_offset.setter
    def if_direct_dsa5_offset(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "direct_dsa5_offset", True, int(value), self._ctrl
        )

    @property
    def if_bypass_lpf_en(self):
        """Get/Set IF bypass LPF enable (true/false)"""
        return self._get_iio_attr_str(
            "altvoltage1", "bypass_lpf_en", True, self._ctrl
        )

    @if_bypass_lpf_en.setter
    def if_bypass_lpf_en(self, value):
        self._set_iio_attr("altvoltage1", "bypass_lpf_en", True, value, self._ctrl)

    @property
    def if_bypass_lpf_val(self):
        """Get/Set IF bypass LPF value"""
        return self._get_iio_attr("altvoltage1", "bypass_lpf_val", True, self._ctrl)

    @if_bypass_lpf_val.setter
    def if_bypass_lpf_val(self, value):
        self._set_iio_attr_int(
            "altvoltage1", "bypass_lpf_val", True, int(value), self._ctrl
        )

    @property
    def if_bypass_dsa4_gain(self):
        """Get/Set IF bypass DSA4 gain (0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage1", "bypass_dsa4_gain", True, self._ctrl
        )

    @if_bypass_dsa4_gain.setter
    def if_bypass_dsa4_gain(self, value):
        self._set_iio_attr("altvoltage1", "bypass_dsa4_gain", True, value, self._ctrl)

    @property
    def if_bypass_dsa4_gain_available(self):
        """Get available IF bypass DSA4 gain options"""
        return self._get_iio_attr_str(
            "altvoltage1", "bypass_dsa4_gain_available", True, self._ctrl
        )

    @property
    def if_bypass_dsa5_gain(self):
        """Get/Set IF bypass DSA5 gain (0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage1", "bypass_dsa5_gain", True, self._ctrl
        )

    @if_bypass_dsa5_gain.setter
    def if_bypass_dsa5_gain(self, value):
        self._set_iio_attr("altvoltage1", "bypass_dsa5_gain", True, value, self._ctrl)

    @property
    def if_bypass_dsa5_gain_available(self):
        """Get available IF bypass DSA5 gain options"""
        return self._get_iio_attr_str(
            "altvoltage1", "bypass_dsa5_gain_available", True, self._ctrl
        )

    # --- LO Channel (in_altvoltage2_lo) ---

    @property
    def lo_sideband(self):
        """Get/Set LO sideband selection. Options: LSB, USB"""
        return self._get_iio_attr_str("altvoltage2", "sideband", False, self._ctrl)

    @lo_sideband.setter
    def lo_sideband(self, value):
        self._set_iio_attr("altvoltage2", "sideband", False, value, self._ctrl)

    @property
    def lo_sideband_available(self):
        """Get available LO sideband options"""
        return self._get_iio_attr_str(
            "altvoltage2", "sideband_available", False, self._ctrl
        )

    @property
    def lo_x3_filter(self):
        """Get/Set LO x3 filter selection.
        Options: 24GHz_28GHz, 18GHz_24GHz, 14GHz_18GHz,
                 12GHz_14GHz, 10GHz_12GHz, 8GHz_10GHz"""
        return self._get_iio_attr_str("altvoltage2", "x3_filter", False, self._ctrl)

    @lo_x3_filter.setter
    def lo_x3_filter(self, value):
        self._set_iio_attr("altvoltage2", "x3_filter", False, value, self._ctrl)

    @property
    def lo_x3_filter_available(self):
        """Get available LO x3 filter options"""
        return self._get_iio_attr_str(
            "altvoltage2", "x3_filter_available", False, self._ctrl
        )

    @property
    def lo_direct_i_phase_val(self):
        """Get/Set LO I-phase value (0-31)"""
        return self._get_iio_attr(
            "altvoltage2", "direct_i_phase_val", False, self._ctrl
        )

    @lo_direct_i_phase_val.setter
    def lo_direct_i_phase_val(self, value):
        self._set_iio_attr_int(
            "altvoltage2", "direct_i_phase_val", False, int(value), self._ctrl
        )

    @property
    def lo_direct_q_phase_val(self):
        """Get/Set LO Q-phase value (0-31)"""
        return self._get_iio_attr(
            "altvoltage2", "direct_q_phase_val", False, self._ctrl
        )

    @lo_direct_q_phase_val.setter
    def lo_direct_q_phase_val(self, value):
        self._set_iio_attr_int(
            "altvoltage2", "direct_q_phase_val", False, int(value), self._ctrl
        )

    # --- Temperature and Power Sensor ---

    @property
    def temp_raw(self):
        """Get raw temperature sensor readback"""
        return self._get_iio_attr("temp0", "raw", False, self._ctrl)

    @property
    def power_raw(self):
        """Get raw power detector readback"""
        return self._get_iio_attr("power0", "raw", False, self._ctrl)

    # --- Device-Level Attributes ---

    @property
    def filter_table_en(self):
        """Get/Set filter table enable (true/false)"""
        return self._get_iio_dev_attr_str("filter_table_en", self._ctrl)

    @filter_table_en.setter
    def filter_table_en(self, value):
        self._set_iio_dev_attr("filter_table_en", value, self._ctrl)

    @property
    def filter_load_en(self):
        """Get/Set filter load enable (true/false)"""
        return self._get_iio_dev_attr_str("filter_load_en", self._ctrl)

    @filter_load_en.setter
    def filter_load_en(self, value):
        self._set_iio_dev_attr("filter_load_en", value, self._ctrl)

    @property
    def filter_table_sel(self):
        """Get/Set filter table selection (A or B)"""
        return self._get_iio_dev_attr_str("filter_table_sel", self._ctrl)

    @filter_table_sel.setter
    def filter_table_sel(self, value):
        self._set_iio_dev_attr("filter_table_sel", value, self._ctrl)

    @property
    def gain_table_en(self):
        """Get/Set gain table enable (true/false)"""
        return self._get_iio_dev_attr_str("gain_table_en", self._ctrl)

    @gain_table_en.setter
    def gain_table_en(self, value):
        self._set_iio_dev_attr("gain_table_en", value, self._ctrl)

    @property
    def gain_load_en(self):
        """Get/Set gain load enable (true/false)"""
        return self._get_iio_dev_attr_str("gain_load_en", self._ctrl)

    @gain_load_en.setter
    def gain_load_en(self, value):
        self._set_iio_dev_attr("gain_load_en", value, self._ctrl)

    @property
    def direct_gpo_f(self):
        """Get/Set direct GPO_F value (0-511, 9-bit filter LUT control)"""
        return self._get_iio_dev_attr("direct_gpo_f", self._ctrl)

    @direct_gpo_f.setter
    def direct_gpo_f(self, value):
        self._set_iio_dev_attr("direct_gpo_f", value, self._ctrl)

    @property
    def direct_gpo_g(self):
        """Get/Set direct GPO_G value (0-127, 7-bit switch control)"""
        return self._get_iio_dev_attr("direct_gpo_g", self._ctrl)

    @direct_gpo_g.setter
    def direct_gpo_g(self, value):
        self._set_iio_dev_attr("direct_gpo_g", value, self._ctrl)

    @property
    def bypass_gpo_g(self):
        """Get/Set bypass GPO_G value (0-127)"""
        return self._get_iio_dev_attr("bypass_gpo_g", self._ctrl)

    @bypass_gpo_g.setter
    def bypass_gpo_g(self, value):
        self._set_iio_dev_attr("bypass_gpo_g", value, self._ctrl)

    @property
    def filter_table_config_A(self):
        """Get/Set filter LUT table A configuration (32 entries)"""
        return self._read_dev_attr_large("filter_table_config_A")

    @filter_table_config_A.setter
    def filter_table_config_A(self, value):
        self._set_iio_dev_attr_str("filter_table_config_A", value, self._ctrl)

    @property
    def filter_table_config_B(self):
        """Get/Set filter LUT table B configuration (32 entries)"""
        return self._read_dev_attr_large("filter_table_config_B")

    @filter_table_config_B.setter
    def filter_table_config_B(self, value):
        self._set_iio_dev_attr_str("filter_table_config_B", value, self._ctrl)

    @property
    def gain_table_config(self):
        """Get/Set gain LUT table configuration (67 entries)"""
        return self._read_dev_attr_large("gain_table_config")

    @gain_table_config.setter
    def gain_table_config(self, value):
        self._set_iio_dev_attr_str("gain_table_config", value, self._ctrl)

    @property
    def bypass_gain_table_en(self):
        """Get/Set bypass gain table enable (true/false)"""
        return self._get_iio_dev_attr_str("bypass_gain_table_en", self._ctrl)

    @bypass_gain_table_en.setter
    def bypass_gain_table_en(self, value):
        self._set_iio_dev_attr("bypass_gain_table_en", value, self._ctrl)

    # --- Direct Register Access ---

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
