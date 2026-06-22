"""
Layer 1: IIO Device Wrappers

Typed Python wrappers for each UDC RF IC, exposing IIO channel/device
attributes as Python properties instead of raw register reads/writes.

Each class takes an ``iio.Device`` object and provides named methods that
map to the IIO attribute API documented in README.md.
"""

import time


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# IIO device name for the GPIO one-bit-adc-dac device
GPIO_DEVICE_NAME = "UDC_gpio"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ch_find(iio_dev, ch_id, output=None):
    """Return the iio.Channel matching *ch_id* (checked against both
    ``id`` and ``name``).  When *output* is ``None`` the direction is
    not checked; otherwise it must match ``ch.output``."""
    for ch in iio_dev.channels:
        if output is not None and ch.output != output:
            continue
        if ch.id == ch_id or getattr(ch, 'name', None) == ch_id:
            return ch
    return None


def _ch_read(iio_dev, ch_id, attr, output=None):
    """Read a channel attribute value as a string."""
    ch = _ch_find(iio_dev, ch_id, output)
    if ch is None:
        raise RuntimeError(f"Channel '{ch_id}' not found on {iio_dev.name}")
    return ch.attrs[attr].value


def _ch_write(iio_dev, ch_id, attr, value, output=None):
    """Write a channel attribute value (converted to str)."""
    ch = _ch_find(iio_dev, ch_id, output)
    if ch is None:
        raise RuntimeError(f"Channel '{ch_id}' not found on {iio_dev.name}")
    ch.attrs[attr].value = str(value)


def _dev_read(iio_dev, attr):
    """Read a device-level attribute."""
    return iio_dev.attrs[attr].value


def _dev_write(iio_dev, attr, value):
    """Write a device-level attribute."""
    iio_dev.attrs[attr].value = str(value)


# ---------------------------------------------------------------------------
# ADMV1420  (Microwave Down-converter, RX)
# ---------------------------------------------------------------------------

class ADMV1420:
    """Wrapper for one admv1420_rx_N IIO device.

    Channels: rf, if, lo, temp0, power0
    """

    # RF band options
    RF_BANDS = ["100MHz_2GHz", "1GHz_5GHz", "3GHz_13GHz", "6GHz_20GHz"]
    # IF band options
    IF_BANDS = ["1GHz_5GHz", "3GHz_13GHz"]
    # LO x3 filter options
    LO_X3_FILTERS = ["24GHz_28GHz", "18GHz_24GHz", "14GHz_18GHz",
                      "12GHz_14GHz", "10GHz_12GHz", "8GHz_10GHz"]
    # DSA gain options (1 dB steps)
    DSA_GAINS_1DB = [f"-{i}dB" for i in range(16)]
    DSA_GAINS_1DB[0] = "0dB"
    # DSA2 has only 0 or -6
    DSA2_GAINS = ["0dB", "-6dB"]
    # 0.1 dB fine attenuator options
    DSA_01DB = [f"-{i*100}mdB" for i in range(16)]
    DSA_01DB[0] = "0dB"

    def __init__(self, iio_dev):
        self._dev = iio_dev
        self.name = iio_dev.name if iio_dev else "admv1420"

    # -- RF channel ----------------------------------------------------------
    def get_rf_band(self):
        return _ch_read(self._dev, "rf", "band")

    def set_rf_band(self, band: str):
        """Set RF band. Options: 100MHz_2GHz, 1GHz_5GHz, 3GHz_13GHz, 6GHz_20GHz"""
        _ch_write(self._dev, "rf", "band", band)

    def set_rf_dsa1_gain(self, gain: str):
        """Set DSA1 gain. Options: 0dB .. -15dB"""
        _ch_write(self._dev, "rf", "direct_dsa1_gain", gain)

    def set_rf_dsa2_gain(self, gain: str):
        """Set DSA2 gain. Options: 0dB, -6dB"""
        _ch_write(self._dev, "rf", "direct_dsa2_gain", gain)

    def set_rf_dsa3_gain(self, gain: str):
        """Set DSA3 gain. Options: 0dB .. -15dB"""
        _ch_write(self._dev, "rf", "direct_dsa3_gain", gain)

    def set_rf_bypass_lpf(self, enable: bool, val: int = 0):
        _ch_write(self._dev, "rf", "bypass_lpf_en", str(enable).lower())
        if enable:
            _ch_write(self._dev, "rf", "bypass_lpf_val", val)

    def set_rf_bypass_hpf(self, enable: bool, val: int = 0):
        _ch_write(self._dev, "rf", "bypass_hpf_en", str(enable).lower())
        if enable:
            _ch_write(self._dev, "rf", "bypass_hpf_val", val)

    def set_rf_direct_lpf(self, val: int):
        _ch_write(self._dev, "rf", "direct_lpf_val", val)

    def set_rf_direct_hpf(self, val: int):
        _ch_write(self._dev, "rf", "direct_hpf_val", val)

    def set_rf_bypass_dsa1(self, gain: str):
        _ch_write(self._dev, "rf", "bypass_dsa1_gain", gain)

    def set_rf_bypass_dsa2(self, gain: str):
        _ch_write(self._dev, "rf", "bypass_dsa2_gain", gain)

    def set_rf_bypass_dsa3(self, gain: str):
        _ch_write(self._dev, "rf", "bypass_dsa3_gain", gain)

    # -- IF channel ----------------------------------------------------------
    def get_if_band(self):
        return _ch_read(self._dev, "if", "band")

    def set_if_band(self, band: str):
        """Options: 1GHz_5GHz, 3GHz_13GHz"""
        _ch_write(self._dev, "if", "band", band)

    def set_if_mode(self, mode: str):
        """Options: baseband, if"""
        _ch_write(self._dev, "if", "mode", mode)

    def set_if_dsa4_gain(self, gain: str):
        _ch_write(self._dev, "if", "direct_dsa4_gain", gain)

    def set_if_dsa5_gain(self, gain: str):
        _ch_write(self._dev, "if", "direct_dsa5_gain", gain)

    def set_if_dsai_0p1db(self, val: str):
        """IMR I-path fine attenuator. Options: 0dB, -100mdB .. -1500mdB"""
        _ch_write(self._dev, "if", "dsai_0p1db", val)

    def set_if_dsaq_0p1db(self, val: str):
        """IMR Q-path fine attenuator. Options: 0dB, -100mdB .. -1500mdB"""
        _ch_write(self._dev, "if", "dsaq_0p1db", val)

    def set_if_bypass_dsa4(self, gain: str):
        _ch_write(self._dev, "if", "bypass_dsa4_gain", gain)

    def set_if_bypass_dsa5(self, gain: str):
        _ch_write(self._dev, "if", "bypass_dsa5_gain", gain)

    # -- DSA offset (fine-tune on top of table values) ------------------------
    def set_rf_dsa1_offset(self, val: int):
        """DSA1 offset added to table value. 0-15"""
        _ch_write(self._dev, "rf", "direct_dsa1_offset", val)

    def set_rf_dsa2_offset(self, val: int):
        """DSA2 offset added to table value. 0-3"""
        _ch_write(self._dev, "rf", "direct_dsa2_offset", val)

    def set_rf_dsa3_offset(self, val: int):
        """DSA3 offset added to table value. 0-15"""
        _ch_write(self._dev, "rf", "direct_dsa3_offset", val)

    def set_if_dsa4_offset(self, val: int):
        """DSA4 offset added to table value. 0-15"""
        _ch_write(self._dev, "if", "direct_dsa4_offset", val)

    def set_if_dsa5_offset(self, val: int):
        """DSA5 offset added to table value. 0-15"""
        _ch_write(self._dev, "if", "direct_dsa5_offset", val)

    # -- LO channel ----------------------------------------------------------
    def set_lo_sideband(self, sideband: str):
        """Options: LSB, USB"""
        _ch_write(self._dev, "lo", "sideband", sideband)

    def set_lo_x3_filter(self, filt: str):
        _ch_write(self._dev, "lo", "x3_filter", filt)

    def set_lo_i_phase(self, val: int):
        _ch_write(self._dev, "lo", "direct_i_phase_val", val)

    def set_lo_q_phase(self, val: int):
        _ch_write(self._dev, "lo", "direct_q_phase_val", val)

    # -- Device attributes ---------------------------------------------------
    def set_filter_table_en(self, enable: bool):
        _dev_write(self._dev, "filter_table_en", str(enable).lower())

    def set_gain_table_en(self, enable: bool):
        _dev_write(self._dev, "gain_table_en", str(enable).lower())

    def set_bypass_gain_table_en(self, enable: bool):
        _dev_write(self._dev, "bypass_gain_table_en", str(enable).lower())

    def set_gain_load_en(self, enable: bool):
        _dev_write(self._dev, "gain_load_en", str(enable).lower())

    def set_filter_load_en(self, enable: bool):
        _dev_write(self._dev, "filter_load_en", str(enable).lower())

    def set_filter_table_sel(self, sel: str):
        """Select filter table A or B."""
        _dev_write(self._dev, "filter_table_sel", sel)

    # -- LUT config read / write ---------------------------------------------
    def write_filter_table_entry(self, entry_str: str, table: str = "A"):
        """Write one formatted entry to the filter LUT."""
        attr = f"filter_table_config_{table.upper()}"
        _dev_write(self._dev, attr, entry_str)

    def read_filter_table(self, table: str = "A") -> str:
        """Read the full filter LUT (all 32 entries)."""
        attr = f"filter_table_config_{table.upper()}"
        return _dev_read(self._dev, attr)

    def write_gain_table_entry(self, entry_str: str):
        """Write one formatted entry to the gain LUT."""
        _dev_write(self._dev, "gain_table_config", entry_str)

    def read_gain_table(self) -> str:
        """Read the full gain LUT (all 32 entries)."""
        return _dev_read(self._dev, "gain_table_config")

    # -- Gain mode abstraction -----------------------------------------------
    GAIN_MODES = ["bypass", "table", "direct"]

    def configure_gain_mode(self, mode: str):
        """Set the gain control priority mode.

        The ADMV1420 uses a 3-level priority system:

        * **bypass** (highest) — ``bypass_gain_table_en = true``;
          uses ``bypass_dsa*_gain`` registers (0x28B-0x28D).
        * **table** — ``bypass_gain_table_en = false``,
          ``gain_table_en = true``; DSA values come from the gain
          lookup table, fine-tuned by ``direct_dsa*_offset``.
        * **direct** (lowest) — both enables false; uses
          ``direct_dsa*_gain`` registers (0x600-0x602).

        Parameters
        ----------
        mode : str
            ``"bypass"``, ``"table"``, or ``"direct"``.
        """
        if mode == "bypass":
            self.set_bypass_gain_table_en(True)
        elif mode == "table":
            self.set_bypass_gain_table_en(False)
            self.set_gain_table_en(True)
        elif mode == "direct":
            self.set_bypass_gain_table_en(False)
            self.set_gain_table_en(False)
        else:
            raise ValueError(
                f"Invalid gain mode '{mode}'. "
                f"Valid: {', '.join(self.GAIN_MODES)}"
            )

    # -- Sensors -------------------------------------------------------------
    def read_temperature(self):
        return _ch_read(self._dev, "temp0", "raw")

    def read_power(self):
        return _ch_read(self._dev, "power0", "raw")

    # -- Direct register (fallback) ------------------------------------------
    def reg_read(self, addr):
        return self._dev.reg_read(addr)

    def reg_write(self, addr, val):
        self._dev.reg_write(addr, val)


# ---------------------------------------------------------------------------
# ADMV1320  (Microwave Up-converter, TX)
# ---------------------------------------------------------------------------

class ADMV1320:
    """Wrapper for one admv1320_tx_N IIO device.

    Channels: rf, if, lo
    """

    RF_BANDS = ["0_2GHz", "1GHz_5GHz", "3GHz_10GHz", "6GHz_20GHz"]
    IF_BANDS = ["3GHz_12GHz", "1p7GHz_9GHz"]
    LO_X3_FILTERS = ["8GHz_9GHz", "9GHz_11GHz", "11GHz_13GHz",
                      "13GHz_17GHz", "17GHz_23GHz", "23GHz_28GHz"]

    def __init__(self, iio_dev):
        self._dev = iio_dev
        self.name = iio_dev.name if iio_dev else "admv1320"

    # -- RF channel ----------------------------------------------------------
    def set_rf_band(self, band: str):
        _ch_write(self._dev, "rf", "band", band)

    def get_rf_band(self):
        return _ch_read(self._dev, "rf", "band")

    def set_rf_dsa1_gain(self, gain: str):
        _ch_write(self._dev, "rf", "direct_dsa1_gain", gain)

    def set_rf_dsa2_gain(self, gain: str):
        _ch_write(self._dev, "rf", "direct_dsa2_gain", gain)

    def set_rf_bypass_lpf(self, enable: bool, val: int = 0):
        _ch_write(self._dev, "rf", "bypass_lpf_en", str(enable).lower())
        if enable:
            _ch_write(self._dev, "rf", "bypass_lpf_val", val)

    def set_rf_bypass_hpf(self, enable: bool, val: int = 0):
        _ch_write(self._dev, "rf", "bypass_hpf_en", str(enable).lower())
        if enable:
            _ch_write(self._dev, "rf", "bypass_hpf_val", val)

    def set_rf_direct_lpf(self, val: int):
        _ch_write(self._dev, "rf", "direct_lpf_val", val)

    def set_rf_direct_hpf(self, val: int):
        _ch_write(self._dev, "rf", "direct_hpf_val", val)

    def set_rf_bypass_dsa1(self, gain: str):
        _ch_write(self._dev, "rf", "bypass_dsa1_gain", gain)

    def set_rf_bypass_dsa2(self, gain: str):
        _ch_write(self._dev, "rf", "bypass_dsa2_gain", gain)

    # -- DSA offset (fine-tune on top of table values) ------------------------
    def set_rf_dsa1_offset(self, val: int):
        """DSA1 offset added to table value. 0-15"""
        _ch_write(self._dev, "rf", "direct_dsa1_offset", val)

    def set_rf_dsa2_offset(self, val: int):
        """DSA2 offset added to table value. 0-15"""
        _ch_write(self._dev, "rf", "direct_dsa2_offset", val)

    # -- IF channel ----------------------------------------------------------
    def set_if_band(self, band: str):
        _ch_write(self._dev, "if", "band", band)

    def set_if_mode(self, mode: str):
        """Options: baseband, if"""
        _ch_write(self._dev, "if", "mode", mode)

    def set_if_vcm(self, val: int):
        """IF common mode voltage. 0-127, LSB = 50mV"""
        _ch_write(self._dev, "if", "vcm", val)

    def set_if_dsai_0p1db(self, val: str):
        _ch_write(self._dev, "if", "dsai_0p1db", val)

    def set_if_dsaq_0p1db(self, val: str):
        _ch_write(self._dev, "if", "dsaq_0p1db", val)

    # -- LO channel ----------------------------------------------------------
    def set_lo_sideband(self, sideband: str):
        _ch_write(self._dev, "lo", "sideband", sideband)

    def set_lo_x3_filter(self, filt: str):
        _ch_write(self._dev, "lo", "x3_filter", filt)

    def set_lo_i_phase(self, val: int):
        _ch_write(self._dev, "lo", "direct_i_phase_val", val)

    def set_lo_q_phase(self, val: int):
        _ch_write(self._dev, "lo", "direct_q_phase_val", val)

    def set_lo_lon_offset_i(self, val: int):
        _ch_write(self._dev, "lo", "direct_lon_offset_i", val)

    def set_lo_lon_offset_q(self, val: int):
        _ch_write(self._dev, "lo", "direct_lon_offset_q", val)

    # -- Device attributes ---------------------------------------------------
    def set_filter_table_en(self, enable: bool):
        _dev_write(self._dev, "filter_table_en", str(enable).lower())

    def set_gain_table_en(self, enable: bool):
        _dev_write(self._dev, "gain_table_en", str(enable).lower())

    def set_bypass_gain_table_en(self, enable: bool):
        _dev_write(self._dev, "bypass_gain_table_en", str(enable).lower())

    def set_gain_load_en(self, enable: bool):
        _dev_write(self._dev, "gain_load_en", str(enable).lower())

    def set_filter_load_en(self, enable: bool):
        _dev_write(self._dev, "filter_load_en", str(enable).lower())

    def set_filter_table_sel(self, sel: str):
        """Select filter table A or B."""
        _dev_write(self._dev, "filter_table_sel", sel)

    # -- LUT config read / write ---------------------------------------------
    def write_filter_table_entry(self, entry_str: str, table: str = "A"):
        """Write one formatted entry to the filter LUT."""
        attr = f"filter_table_config_{table.upper()}"
        _dev_write(self._dev, attr, entry_str)

    def read_filter_table(self, table: str = "A") -> str:
        """Read the full filter LUT (all 32 entries)."""
        attr = f"filter_table_config_{table.upper()}"
        return _dev_read(self._dev, attr)

    def write_gain_table_entry(self, entry_str: str):
        """Write one formatted entry to the gain LUT."""
        _dev_write(self._dev, "gain_table_config", entry_str)

    def read_gain_table(self) -> str:
        """Read the full gain LUT (all 32 entries)."""
        return _dev_read(self._dev, "gain_table_config")

    # -- Gain mode abstraction -----------------------------------------------
    GAIN_MODES = ["bypass", "table", "direct"]

    def configure_gain_mode(self, mode: str):
        """Set the gain control priority mode.

        The ADMV1320 uses a 3-level priority system:

        * **bypass** (highest) — ``bypass_gain_table_en = true``;
          uses ``bypass_dsa*_gain`` register (0x28B).
        * **table** — ``bypass_gain_table_en = false``,
          ``gain_table_en = true``; DSA values come from the gain
          lookup table, fine-tuned by ``direct_dsa*_offset``.
        * **direct** (lowest) — both enables false; uses
          ``direct_dsa*_gain`` register (0x600).

        Parameters
        ----------
        mode : str
            ``"bypass"``, ``"table"``, or ``"direct"``.
        """
        if mode == "bypass":
            self.set_bypass_gain_table_en(True)
        elif mode == "table":
            self.set_bypass_gain_table_en(False)
            self.set_gain_table_en(True)
        elif mode == "direct":
            self.set_bypass_gain_table_en(False)
            self.set_gain_table_en(False)
        else:
            raise ValueError(
                f"Invalid gain mode '{mode}'. "
                f"Valid: {', '.join(self.GAIN_MODES)}"
            )

    def set_mixer_bypass_en(self, val: bool):
        _dev_write(self._dev, "mixer_bypass_en", str(val).lower())

    # -- Direct register (fallback) ------------------------------------------
    def reg_read(self, addr):
        return self._dev.reg_read(addr)

    def reg_write(self, addr, val):
        self._dev.reg_write(addr, val)


# ---------------------------------------------------------------------------
# ADMV8913  (Tunable Filter, both RX and TX)
# ---------------------------------------------------------------------------

class ADMV8913:
    """Wrapper for one admv8913_N IIO device (shared between RX and TX).

    The ADMV8913 has a 4-bit HPF and 4-bit LPF configurable via IIO channel
    attributes (parallel pin mode) or via direct register writes when IIO
    attributes are not yet available in the driver.
    """

    # Register addresses for direct HPF/LPF control (used when IIO
    # channel attributes are not available in early driver revisions).
    _REG_HPF = 0x20
    _REG_LPF = 0x20

    def __init__(self, iio_dev):
        self._dev = iio_dev
        self.name = iio_dev.name if iio_dev else "admv8913"

    # -- RF channel (IIO attribute methods) ----------------------------------
    def set_direct_hpf(self, val: int):
        """Set HPF via IIO channel attribute (4-bit value, 0-15)."""
        _ch_write(self._dev, "rf", "direct_hpf_val", val & 0xF)

    def set_direct_lpf(self, val: int):
        """Set LPF via IIO channel attribute (4-bit value, 0-15)."""
        _ch_write(self._dev, "rf", "direct_lpf_val", val & 0xF)

    # -- Register-based HPF/LPF (fallback for early driver revisions) --------
    def set_hpf_reg(self, val: int):
        """Set HPF via direct register write (4-bit value, 0-15)."""

        readBack = self._dev.reg_write(self._REG_HPF)
        self._dev.reg_write(self._REG_HPF, (readBack & 0xF) + ((val & 0xF)<<4)) 

    def set_lpf_reg(self, val: int):
        """Set LPF via direct register write (4-bit value, 0-15)."""

        readBack = self._dev.reg_write(self._REG_LPF)
        self._dev.reg_write(self._REG_LPF, (readBack & 0xF0) + (val & 0xF)) 

    # -- Device attributes ---------------------------------------------------
    def set_fast_latch_load(self):
        _dev_write(self._dev, "fast_latch_load", "true")

    def set_fast_latch_pointer(self, val: int):
        _dev_write(self._dev, "fast_latch_pointer", val)

    def set_fast_latch_stop(self, val: int):
        _dev_write(self._dev, "fast_latch_stop", val)

    def set_fast_latch_start(self, val: int):
        _dev_write(self._dev, "fast_latch_start", val)

    def set_fast_latch_direction(self, forward: bool):
        _dev_write(self._dev, "fast_latch_direction", str(forward).lower())

    def write_lut_entry(self, entry_str: str):
        """Write one formatted entry to the LUT."""
        _dev_write(self._dev, "lut_config", entry_str)

    def read_lut(self) -> str:
        """Read the full LUT (all 64 entries)."""
        return _dev_read(self._dev, "lut_config")

    def reg_read(self, addr):
        return self._dev.reg_read(addr)

    def reg_write(self, addr, val):
        self._dev.reg_write(addr, val)


# ---------------------------------------------------------------------------
# ADF4382  (Microwave Wideband Synthesizer with Integrated VCO)
# ---------------------------------------------------------------------------

class ADF4382:
    """Wrapper for the adf4382_lo IIO device.

    The ADF4382 is the LO PLL/VCO source.
    IIO channel: altvoltage0 (output).

    Attribute names are taken from the pyadi-iio ``adf4382`` driver and
    the upstream Linux IIO driver.
    """

    def __init__(self, iio_dev):
        self._dev = iio_dev
        self.name = iio_dev.name if iio_dev else "adf4382"

    # -- OUTA channel attributes (altvoltage0) ---------------------------------
    def set_outa_frequency(self, freq_hz: int):
        """Set OUTA (altvoltage0) RF output frequency in Hz."""
        _ch_write(self._dev, "altvoltage0", "frequency", freq_hz)

    def get_outa_frequency(self) -> int:
        """Read back OUTA (altvoltage0) RF output frequency in Hz."""
        return int(_ch_read(self._dev, "altvoltage0", "frequency"))

    def set_outa_enable(self, en: bool):
        """Enable or disable OUTA (altvoltage0)."""
        _ch_write(self._dev, "altvoltage0", "en", int(en))

    def get_outa_enable(self) -> bool:
        """Read back OUTA (altvoltage0) enable state."""
        return bool(int(_ch_read(self._dev, "altvoltage0", "en")))

    def set_outa_power(self, power: int):
        """Set OUTA (altvoltage0) output power level (0 = lowest, 3 = highest)."""
        _ch_write(self._dev, "altvoltage0", "output_power", power)

    def get_outa_power(self) -> int:
        """Read back OUTA (altvoltage0) output power level."""
        return int(_ch_read(self._dev, "altvoltage0", "output_power"))

    def set_outa_phase(self, phase: int):
        """Set OUTA (altvoltage0) phase adjustment."""
        _ch_write(self._dev, "altvoltage0", "phase", phase)

    def get_outa_phase(self) -> int:
        """Read back OUTA (altvoltage0) phase adjustment."""
        return int(_ch_read(self._dev, "altvoltage0", "phase"))

    # -- OUTB channel attributes (altvoltage1) ---------------------------------
    def set_outb_frequency(self, freq_hz: int):
        """Set OUTB (altvoltage1) RF output frequency in Hz."""
        _ch_write(self._dev, "altvoltage1", "frequency", freq_hz)

    def get_outb_frequency(self) -> int:
        """Read back OUTB (altvoltage1) RF output frequency in Hz."""
        return int(_ch_read(self._dev, "altvoltage1", "frequency"))

    def set_outb_enable(self, en: bool):
        """Enable or disable OUTB (altvoltage1)."""
        _ch_write(self._dev, "altvoltage1", "en", int(en))

    def get_outb_enable(self) -> bool:
        """Read back OUTB (altvoltage1) enable state."""
        return bool(int(_ch_read(self._dev, "altvoltage1", "en")))

    def set_outb_power(self, power: int):
        """Set OUTB (altvoltage1) output power level (0 = lowest, 3 = highest)."""
        _ch_write(self._dev, "altvoltage1", "output_power", power)

    def get_outb_power(self) -> int:
        """Read back OUTB (altvoltage1) output power level."""
        return int(_ch_read(self._dev, "altvoltage1", "output_power"))

    def set_outb_phase(self, phase: int):
        """Set OUTB (altvoltage1) phase adjustment."""
        _ch_write(self._dev, "altvoltage1", "phase", phase)

    def get_outb_phase(self) -> int:
        """Read back OUTB (altvoltage1) phase adjustment."""
        return int(_ch_read(self._dev, "altvoltage1", "phase"))

    # -- Convenience: shared PLL frequency and both-output helpers -------------
    def set_frequency(self, freq_hz: int):
        """Set both OUTA and OUTB to the same frequency in Hz."""
        self.set_outa_frequency(freq_hz)
        self.set_outb_frequency(freq_hz)

    def get_frequency(self) -> int:
        """Read back OUTA frequency in Hz (both outputs share the PLL)."""
        return self.get_outa_frequency()

    def set_enable(self, en: bool):
        """Enable or disable both OUTA and OUTB together."""
        self.set_outa_enable(en)
        self.set_outb_enable(en)

    # -- Device attributes ---------------------------------------------------
    def set_charge_pump_current(self, current_ma: str):
        """Set charge pump current. Options: 0.700000 .. 11.100000."""
        _dev_write(self._dev, "charge_pump_current", current_ma)

    def get_charge_pump_current(self) -> str:
        return _dev_read(self._dev, "charge_pump_current")

    def set_reference_frequency(self, freq_hz: int):
        _dev_write(self._dev, "reference_frequency", freq_hz)

    def get_reference_frequency(self) -> int:
        return int(_dev_read(self._dev, "reference_frequency"))

    def set_reference_divider(self, div: int):
        _dev_write(self._dev, "reference_divider", div)

    def set_reference_doubler_en(self, en: bool):
        _dev_write(self._dev, "reference_doubler_en", int(en))

    def set_sw_sync_en(self, en: bool):
        _dev_write(self._dev, "sw_sync_en", int(en))

    def set_fastcal_en(self, en: bool):
        _dev_write(self._dev, "fastcal_en", int(en))

    def set_fastcal_lut_en(self, en: bool):
        _dev_write(self._dev, "fastcal_lut_en", int(en))

    def set_change_frequency(self, freq_hz: int):
        """Change frequency without starting calibration."""
        _dev_write(self._dev, "change_frequency", freq_hz)

    def start_calibration(self):
        _dev_write(self._dev, "start_calibration", 1)

    # -- Temperature sensor ---------------------------------------------------
    def read_temperature(self) -> int:
        """Read the ADF4382 on-chip temperature sensor.

        Configures the internal ADC, triggers a conversion, waits for
        completion, and returns the signed temperature in degrees C.
        """
        dev = self._dev

        # Enable ADC clocks and ADC block (read-modify-write)
        val = dev.reg_read(0x02D)
        dev.reg_write(0x02D, val | 0xC0)   # set bit[7] EN_DRCLK=1, bit[6] EN_DNCLK=1

        val = dev.reg_read(0x031)
        dev.reg_write(0x031, val | 0x08)   # set bit[3] EN_ADC_CLK=1

        val = dev.reg_read(0x03F)
        dev.reg_write(0x03F, val | 0x02)   # set bit[1] EN_ADC=1

        val = dev.reg_read(0x02A)
        dev.reg_write(0x02A, val & ~0x01)  # clear bit[0] PD_ADC=0

        # Start conversion (read-modify-write)
        val = dev.reg_read(0x054)
        dev.reg_write(0x054, val | 0x01)   # set bit[0] ADC_ST_CNV=1

        # Wait for ADC_BUSY (bit 2 of reg 0x58) to clear
        for _ in range(100):
            status = dev.reg_read(0x058)
            if not (status >> 2) & 0x01:
                break
            import time
            time.sleep(0.001)

        # Read 9-bit signed temperature from registers 0x5B (LSB) and 0x5C (MSB bit 0)
        lsb = dev.reg_read(0x05B)
        msb = dev.reg_read(0x05C) & 0x01
        raw = (msb << 8) | lsb

        # Sign-extend 9-bit value
        if raw & 0x100:
            raw -= 512

        # Unwind temp sensor enables (read-modify-write)
        val = dev.reg_read(0x02A)
        dev.reg_write(0x02A, val | 0x01)   # set bit[0] PD_ADC=1

        val = dev.reg_read(0x03F)
        dev.reg_write(0x03F, val & ~0x02)  # clear bit[1] EN_ADC=0

        val = dev.reg_read(0x031)
        dev.reg_write(0x031, val & ~0x08)  # clear bit[3] EN_ADC_CLK=0

        val = dev.reg_read(0x02D)
        dev.reg_write(0x02D, val & ~0xC0)  # clear bit[7] EN_DRCLK=0, bit[6] EN_DNCLK=0

        return raw

    # -- PLL lock status -------------------------------------------------------
    def check_pll_lock(self) -> bool:
        """Read register 0x58 and return True if PLL is locked (bit 0 high)."""
        reg_val = self._dev.reg_read(0x58)
        return bool(reg_val & 0x01)
    # -- Reference clock status -------------------------------------------------------
    def check_ref_clock_status(self) -> bool:
        """Read register 0x58 and return True if reference clock is present (bit 3 high)."""
        reg_val = self._dev.reg_read(0x58)
        return bool(reg_val & 0x08)

    # -- Direct register access ----------------------------------------------
    def reg_read(self, addr):
        return self._dev.reg_read(addr)

    def reg_write(self, addr, val):
        self._dev.reg_write(addr, val)
