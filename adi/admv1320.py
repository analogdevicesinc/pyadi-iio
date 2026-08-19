# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from ctypes import create_string_buffer

from adi.attribute import attribute
from adi.context_manager import context_manager


class admv1320(attribute, context_manager):
    """ADMV1320 Microwave Upconverter

    The ADMV1320 converts baseband/IF signals to RF signals across four RF bands
    (0-2 GHz, 1-5 GHz, 3-10 GHz, 6-20 GHz) with selectable IF bands, LO sideband,
    digitally selectable attenuators (DSAs), IF common mode voltage control, and
    filter/gain LUT support.

    parameters:
        uri: type=string
            URI of IIO context with ADMV1320
        device_name: type=string
            IIO device name (e.g., "admv1320_tx_0" on Neponset board)
    """

    _device_name = "admv1320"

    def __init__(self, uri="", device_name=""):
        context_manager.__init__(self, uri, self._device_name)

        if device_name:
            self._device_name = device_name
        self._ctrl = self._ctx.find_device(self._device_name)

        if not self._ctrl:
            raise Exception("ADMV1320 device not found")

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
        Options: 0_2GHz, 1GHz_5GHz, 3GHz_10GHz, 6GHz_20GHz"""
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
        """Get/Set RF DSA2 gain (4-bit, 0dB to -15dB)"""
        return self._get_iio_attr_str(
            "altvoltage0", "direct_dsa2_gain", False, self._ctrl
        )

    @rf_direct_dsa2_gain.setter
    def rf_direct_dsa2_gain(self, value):
        self._set_iio_attr(
            "altvoltage0", "direct_dsa2_gain", False, value, self._ctrl
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
        """Get/Set RF DSA2 offset (0-15)"""
        return self._get_iio_attr(
            "altvoltage0", "direct_dsa2_offset", False, self._ctrl
        )

    @rf_direct_dsa2_offset.setter
    def rf_direct_dsa2_offset(self, value):
        self._set_iio_attr_int(
            "altvoltage0", "direct_dsa2_offset", False, int(value), self._ctrl
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
        """Get/Set RF bypass DSA2 gain (0dB to -15dB)"""
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

    # --- IF Channel (out_altvoltage1_if) ---

    @property
    def if_band(self):
        """Get/Set the IF band selection.
        Options: 3GHz_12GHz, 1p7GHz_9GHz"""
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
    def if_vcm(self):
        """Get/Set IF common mode voltage (0-127, LSB = 50mV)"""
        return self._get_iio_attr("altvoltage1", "vcm", True, self._ctrl)

    @if_vcm.setter
    def if_vcm(self, value):
        self._set_iio_attr_int("altvoltage1", "vcm", True, int(value), self._ctrl)

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
        Options: 8GHz_9GHz, 9GHz_11GHz, 11GHz_13GHz,
                 13GHz_17GHz, 17GHz_23GHz, 23GHz_28GHz"""
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

    @property
    def lo_direct_lon_offset_i(self):
        """Get/Set LO LON offset I value (0-63)"""
        return self._get_iio_attr(
            "altvoltage2", "direct_lon_offset_i", False, self._ctrl
        )

    @lo_direct_lon_offset_i.setter
    def lo_direct_lon_offset_i(self, value):
        self._set_iio_attr_int(
            "altvoltage2", "direct_lon_offset_i", False, int(value), self._ctrl
        )

    @property
    def lo_direct_lon_offset_q(self):
        """Get/Set LO LON offset Q value (0-63)"""
        return self._get_iio_attr(
            "altvoltage2", "direct_lon_offset_q", False, self._ctrl
        )

    @lo_direct_lon_offset_q.setter
    def lo_direct_lon_offset_q(self, value):
        self._set_iio_attr_int(
            "altvoltage2", "direct_lon_offset_q", False, int(value), self._ctrl
        )

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
    def bypass_gain_table_en(self):
        """Get/Set bypass gain table enable (true/false)"""
        return self._get_iio_dev_attr_str("bypass_gain_table_en", self._ctrl)

    @bypass_gain_table_en.setter
    def bypass_gain_table_en(self, value):
        self._set_iio_dev_attr("bypass_gain_table_en", value, self._ctrl)

    @property
    def direct_gpo_f(self):
        """Get/Set direct GPO_F value (0-511, 9-bit)"""
        return self._get_iio_dev_attr("direct_gpo_f", self._ctrl)

    @direct_gpo_f.setter
    def direct_gpo_f(self, value):
        self._set_iio_dev_attr("direct_gpo_f", value, self._ctrl)

    @property
    def gpo_f_oe(self):
        """Get/Set GPO_F output enable (0-511, 9-bit)"""
        return self._get_iio_dev_attr("gpo_f_oe", self._ctrl)

    @gpo_f_oe.setter
    def gpo_f_oe(self, value):
        self._set_iio_dev_attr("gpo_f_oe", value, self._ctrl)

    @property
    def gpo_g_oe(self):
        """Get/Set GPO_G output enable (0-127, 7-bit)"""
        return self._get_iio_dev_attr("gpo_g_oe", self._ctrl)

    @gpo_g_oe.setter
    def gpo_g_oe(self, value):
        self._set_iio_dev_attr("gpo_g_oe", value, self._ctrl)

    @property
    def direct_gpo_g(self):
        """Get/Set direct GPO_G value (0-127)"""
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
    def mixer_bypass_en(self):
        """Get/Set mixer bypass enable (true/false)"""
        return self._get_iio_dev_attr_str("mixer_bypass_en", self._ctrl)

    @mixer_bypass_en.setter
    def mixer_bypass_en(self, value):
        self._set_iio_dev_attr("mixer_bypass_en", value, self._ctrl)

    # --- Direct Register Access ---

    def reg_read(self, reg):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def reg_write(self, reg, value):
        """Direct Register Access via debugfs"""
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)
