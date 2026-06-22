"""
Layer 2: Signal Chain Composites

Composes multiple IIO device wrappers (from iio_devices.py) into logical
RX / TX / LO chains.  Each chain manages the cross-device coordination.

Typical usage (inside a DUT or test step)::

    ctx   = iio.Context("ip:192.168.2.1")
    gpio  = GpioHelper(ctx)
    rx0   = RxChain(0, ctx, gpio)
    rx0.initialize()
    rx0.set_band("3-13GHz_mixer")
    rx0.set_direct_gain(dsa1="-5dB", dsa3="-3dB")
"""

import time
import iio
from .iio_devices import (
    ADMV1420, ADMV1320, ADMV8913, ADF4382,
    _ch_read, _ch_write, GPIO_DEVICE_NAME,
)


# ---------------------------------------------------------------------------
# GPIO Helper  (wraps the UDC_gpio IIO device)
# ---------------------------------------------------------------------------

class GpioHelper:
    """Read / write GPIOs via IIO voltage channels across multiple devices.

    The _LABEL_MAP can specify channels in three formats:
    1. Simple voltage ID: "voltage0" (searches all devices)
    2. Device:channel format: "UDC_gpio:voltage0" (specific device by name)
    3. Device:channel format: "UDC_gpio(label):voltage0" (specific device by label)
    """

    # Label → (device, voltage channel) mapping
    # Format options:
    #   "voltage0"                    -> searches all devices for voltage0
    #   "device_name:voltage0"        -> looks for device with name="device_name"
    #   "device_label(label):voltage0" -> looks for device with label="device_label"
    #
    _LABEL_MAP = {
        # # ── ADMV1420 RX enable / load ─────────────────────────────────
        # "ADMV1420_RX_LOAD_1": "voltage9",
        # "ADMV1420_RX_LOAD_2": "voltage44",
        # "ADMV1420_RX_LOAD_3": "voltage36",
        # "ADMV1420_RX_LOAD_4": "voltage0",
        # "ADMV1420_RX_CEN_1":   "voltage10",
        # "ADMV1420_RX_CEN_2":   "voltage45",
        # "ADMV1420_RX_CEN_3":   "voltage11",
        # "ADMV1420_RX_CEN_4":   "voltage1",
        # "ADMV1420_RX_RSTB_1":   "voltage10",
        # "ADMV1420_RX_RSTB_2":   "voltage45",
        # "ADMV1420_RX_RSTB_3":   "voltage11",
        # "ADMV1420_RX_RSTB_4":   "voltage1",

        # # ── ADMV1x20 address ─────────────────────────────────
        # "ADMV1x20_ADDR_0": "voltage22",
        # "ADMV1x20_ADDR_1": "voltage14",
        # "ADMV1x20_ADDR_2": "voltage21",
        # "ADMV1x20_ADDR_3": "voltage30",
        # "ADMV1x20_ADDR_4": "voltage28",
        # "ADMV1x20_ADDR_5": "voltage16",

        # "ADMV1x20_ADDRF_0": "voltage14",
        # "ADMV1x20_ADDRF_1": "voltage22",
        # "ADMV1x20_ADDRF_2": "voltage30",
        # "ADMV1x20_ADDRF_3": "voltage28",
        # "ADMV1x20_ADDRF_4": "voltage16",

        # # ── ADMV1320 TX load / enable ────────────────────────────────
        # "ADMV1320_TX_LOAD_1": "voltage8",
        # "ADMV1320_TX_LOAD_2": "voltage38",
        # "ADMV1320_TX_LOAD_3": "voltage20",
        # "ADMV1320_TX_LOAD_4": "voltage40",
        # "ADMV1320_TX_CEN_1":   "voltage10",
        # "ADMV1320_TX_CEN_2":   "voltage45",
        # "ADMV1320_TX_CEN_3":   "voltage11",
        # "ADMV1320_TX_CEN_4":   "voltage1",
        # "ADMV1320_TX_RSTB_1":   "voltage10",
        # "ADMV1320_TX_RSTB_2":   "voltage45",
        # "ADMV1320_TX_RSTB_3":   "voltage11",
        # "ADMV1320_TX_RSTB_4":   "voltage1",

        # ── ADMV1x20 TX load / enable ────────────────────────────────
        "RX_LOAD1": "mantaray_txrx_control:voltage4",
        "RX_LOAD2": "mantaray_txrx_control:voltage5",
        "RX_LOAD3": "mantaray_txrx_control:voltage6",
        "RX_LOAD4": "mantaray_txrx_control:voltage7",
        "TX_LOAD1": "mantaray_txrx_control:voltage0",
        "TX_LOAD2": "mantaray_txrx_control:voltage1",
        "TX_LOAD3": "mantaray_txrx_control:voltage2",
        "TX_LOAD4": "mantaray_txrx_control:voltage3",
        "ADMVXX20_ADDF0": "mantaray_control:voltage19",
        "ADMVXX20_ADDF1": "mantaray_control:voltage20",
        "ADMVXX20_ADDF2": "mantaray_control:voltage21",
        "ADMVXX20_ADDF3": "mantaray_control:voltage22",
        "ADMVXX20_ADDF4": "mantaray_control:voltage23",
        "ADMVXX20_ADDG0": "mantaray_control:voltage24",
        "ADMVXX20_ADDG1": "mantaray_control:voltage25",
        "ADMVXX20_ADDG2": "mantaray_control:voltage26",
        "ADMVXX20_ADDG3": "mantaray_control:voltage27",
        "ADMVXX20_ADDG4": "mantaray_control:voltage28",
        "ADMVXX20_ADDG5": "mantaray_control:voltage29",

        # ── ADRF5030 switch control ─────────────────────────
        # "ADRF5030_EN_1": "voltage",
        # "ADRF5030_EN_2": "voltage",
        # "ADRF5030_EN_3": "voltage",
        # "ADRF5030_EN_4": "voltage",
        # "ADRF5030_CTRL_1": "voltage",
        # "ADRF5030_CTRL_2": "voltage",
        # "ADRF5030_CTRL_3": "voltage",
        # "ADRF5030_CTRL_4": "voltage",

        "ADRF5030_CTRL1": "mantaray_txrx_control:voltage8",
        "ADRF5030_CTRL2": "mantaray_txrx_control:voltage9",
        "ADRF5030_CTRL3": "mantaray_txrx_control:voltage10",
        "ADRF5030_CTRL4": "mantaray_txrx_control:voltage11",
        "ADRF5030_EN1": "mantaray_txrx_control:voltage12",
        "ADRF5030_EN2": "mantaray_txrx_control:voltage13",
        "ADRF5030_EN3": "mantaray_txrx_control:voltage14",
        "ADRF5030_EN4": "mantaray_txrx_control:voltage15",


        # ── BF TX PA control ─────────────────────────
        "BF_PA_ON_01": "mantaray_txrx_control:voltage0",
        "BF_PA_ON_02": "mantaray_txrx_control:voltage1",
        "BF_PA_ON_03": "mantaray_txrx_control:voltage2",
        "BF_PA_ON_04": "mantaray_txrx_control:voltage3",

        # ── ADMV8913 filter control ─────────────────────────
        # "ADMV8913_FL_LDO_EN": "voltage",
        # "ADMV8913_FL_PS_N": "voltage",
        # "ADMV8913_FL_SFL": "voltage",
        # "ADMV8913_FL_RST_N": "voltage",
        # "ADMV8913_FL_HPF_0": "voltage",
        # "ADMV8913_FL_HPF_1": "voltage",
        # "ADMV8913_FL_HPF_2": "voltage",
        # "ADMV8913_FL_HPF_3": "voltage",
        # "ADMV8913_FL_LPF_0": "voltage",
        # "ADMV8913_FL_LPF_1": "voltage",
        # "ADMV8913_FL_LPF_2": "voltage",
        # "ADMV8913_FL_LPF_3": "voltage",

        "RF_FL_LDO_EN": "mantaray_control:voltage4",
        "RF_FL_RST_N": "mantaray_control:voltage7",
        "RF_FL_PS_N": "mantaray_control:voltage6",
        "RF_FL_SFL": "mantaray_control:voltage5",
        "RF_FL_LPF0": "mantaray_control:voltage12",
        "RF_FL_LPF1": "mantaray_control:voltage13",
        "RF_FL_LPF2": "mantaray_control:voltage14",
        "RF_FL_LPF3": "mantaray_control:voltage15",
        "RF_FL_HPF0": "mantaray_control:voltage8",
        "RF_FL_HPF1": "mantaray_control:voltage9",
        "RF_FL_HPF2": "mantaray_control:voltage10",
        "RF_FL_HPF3": "mantaray_control:voltage11",

        # ── ADF4382 LO control ─────────────────────────
        #"ADF4382_LO_CE": "voltage",
        "LO_CE": "mantaray_control:voltage16",

        # ── Power enable and Power good status ─────────────────────────
        # "FPGA_DONE": "voltage17",
        # "UDC_PG": "voltage29",
        # "UDC_5P0V_PWR_EN": "voltage17",
        # "UDC_5P0V_LDO_PG": "voltage29",
        # "UDC_3P3V_PWR_EN": "voltage16",
        # "UDC_3P3V_LDO_PG": "voltage28",
        # "UDC_NEG_PWR_EN": "voltage22",

        # ── Power enable and Power good status ─────────────────────────
         "UDC_NEG_PWR_EN": "mantaray_pwr_control:voltage1",
         "UDC_5P0V_PWR_EN": "mantaray_pwr_control:voltage3",
         "N6P0V_EN": "mantaray_pwr_control:voltage0",
         "UDC_3P3V_PWR_EN": "mantaray_pwr_control:voltage2",
         "BF_PWR_EN_01": "mantaray_pwr_control:voltage4",
         "BF_PWR_EN_02": "mantaray_pwr_control:voltage5",
         "BF_PWR_EN_03": "mantaray_pwr_control:voltage6",
         "BF_PWR_EN_04": "mantaray_pwr_control:voltage7",

    }

    def __init__(self, ctx, log=None):
        self._devices = {}  # Maps device name -> device object
        self._device_by_label = {}  # Maps device label -> device object
        self._channels = {}  # Maps "device_name:voltage_id" -> (device, channel)
        self._resolved_cache = {}  # Maps label -> (device, channel) - PRE-RESOLVED!
        self._log = log
        self._ctx = ctx

        if ctx is None:
            return

        # Scan all devices in the context for GPIO channels
        for d in ctx.devices:
            # Check if device has voltage channels (typical GPIO indicator)
            has_voltage_channels = False
            for ch in d.channels:
                if ch.id.startswith("voltage"):
                    has_voltage_channels = True
                    break

            if has_voltage_channels:
                # Store device by name
                self._devices[d.name] = d

                # Store device by label (if available)
                device_label = getattr(d, 'label', None)
                if device_label:
                    self._device_by_label[device_label] = d

                if self._log:
                    self._log.Debug(f"GpioHelper: found GPIO device '{d.name}' (label: {device_label})")

                # Cache channels with full device:channel key
                for ch in d.channels:
                    if ch.id.startswith("voltage"):
                        key = f"{d.name}:{ch.id}"
                        self._channels[key] = (d, ch)

        if not self._devices:
            if self._log:
                self._log.Warning("No GPIO devices with voltage channels found in IIO context")
        else:
            if self._log:
                self._log.Info(f"GpioHelper: initialized with {len(self._devices)} GPIO device(s), "
                             f"{len(self._channels)} total voltage channels")

        # PRE-RESOLVE all labels in _LABEL_MAP once during init
        # This makes read/write operations fast
        self._presolve_labels()

    def _presolve_labels(self):
        """Pre-resolve all labels in _LABEL_MAP to (device, channel) tuples.

        This is called once during __init__ so read/write operations are just
        fast dictionary lookups instead of parsing and searching every time.
        """
        for label, mapping_str in self._LABEL_MAP.items():
            if mapping_str == "voltage":
                # Incomplete mapping - skip (will error on use)
                continue

            device_channel = self._resolve_channel(mapping_str)
            if device_channel:
                self._resolved_cache[label] = device_channel
                if self._log:
                    dev, ch = device_channel
                    self._log.Debug(f"Pre-resolved: '{label}' -> {dev.name}:{ch.id}")
            else:
                if self._log:
                    self._log.Warning(f"Failed to pre-resolve: '{label}' -> '{mapping_str}'")

    def _resolve_channel(self, mapping_str: str):
        """Resolve a mapping string to (device, channel) tuple.

        Supports three formats:
        1. "voltage0"                -> searches all devices for voltage0 (first match)
        2. "device_name:voltage0"    -> specific device by name
        3. "device_label(label):voltage0" -> specific device by label

        Returns:
            (device, channel) tuple or None if not found
        """
        # Format 1: Simple voltage ID - "voltage0"
        if ":" not in mapping_str:
            voltage_id = mapping_str

            # Search all devices for this voltage channel
            for device_name, device in self._devices.items():
                key = f"{device_name}:{voltage_id}"
                if key in self._channels:
                    return self._channels[key]
            return None

        # Format 2 or 3: Device-specific - "device:voltage0" or "label(label):voltage0"
        device_spec, voltage_id = mapping_str.split(":", 1)

        # Check if it's label format: "device_label(label)"
        if device_spec.endswith("(label)"):
            device_label = device_spec[:-7]  # Remove "(label)" suffix
            device = self._device_by_label.get(device_label)
            if device is None:
                return None
            key = f"{device.name}:{voltage_id}"
            return self._channels.get(key)

        # Format 2: Device name - "device_name:voltage0"
        key = f"{device_spec}:{voltage_id}"
        return self._channels.get(key)

    def write(self, label_or_voltage: str, value: int):
        """Set a GPIO pin.  *label_or_voltage* is either a human-readable
        label (e.g. ``ADMV1420_RX_EN_0``) or a voltage channel id
        (e.g. ``voltage39`` or ``device_name:voltage39``).
        """
        if not self._devices:
            if self._log:
                self._log.Error(f"GPIO write failed: no GPIO devices available ({label_or_voltage}={value})")
            return

        # Try pre-resolved cache first (FAST PATH - most common case)
        device_channel_tuple = self._resolved_cache.get(label_or_voltage)

        if device_channel_tuple is None:
            # Not in cache - might be a direct voltage ID like "voltage39"
            # or a device:voltage format like "UDC_gpio:voltage39"
            device_channel_tuple = self._resolve_channel(label_or_voltage)

            if device_channel_tuple is None:
                if self._log:
                    self._log.Error(f"GPIO write failed: '{label_or_voltage}' not found in any device")
                return

        device, ch = device_channel_tuple

        # Check if channel is writable (output)
        if not ch.output:
            if self._log:
                self._log.Error(f"GPIO write failed: channel '{ch.id}' on '{device.name}' is input-only")
            return

        ch.attrs["raw"].value = str(value)
        if self._log:
            self._log.Debug(f"GPIO {label_or_voltage} ({ch.id} on {device.name}) = {value}")

    def read(self, label_or_voltage: str) -> int:
        """Read a GPIO pin. *label_or_voltage* is either a human-readable
        label or a voltage channel id.
        """
        if not self._devices:
            if self._log:
                self._log.Error(f"GPIO read failed: no GPIO devices available ({label_or_voltage})")
            return -1

        # Try pre-resolved cache first (FAST PATH - most common case)
        device_channel_tuple = self._resolved_cache.get(label_or_voltage)

        if device_channel_tuple is None:
            # Not in cache - might be a direct voltage ID like "voltage39"
            # or a device:voltage format like "UDC_gpio:voltage39"
            device_channel_tuple = self._resolve_channel(label_or_voltage)

            if device_channel_tuple is None:
                if self._log:
                    self._log.Error(f"GPIO read failed: '{label_or_voltage}' not found in any device")
                return -1

        device, ch = device_channel_tuple
        value = int(ch.attrs["raw"].value)
        if self._log:
            self._log.Debug(f"GPIO {label_or_voltage} ({ch.id} on {device.name}) read = {value}")
        return value

    def list_available_channels(self):
        """List all available GPIO channels from all devices (for debugging mapping issues)."""
        if not self._devices:
            if self._log:
                self._log.Warning("No GPIO devices available")
            return []

        channels = []
        for device_name, device in self._devices.items():
            for ch in device.channels:
                if ch.id.startswith("voltage"):
                    direction = "output" if ch.output else "input"
                    label = getattr(ch, 'label', 'N/A')
                    channels.append({
                        "device": device.name,
                        "id": ch.id,
                        "direction": direction,
                        "label": label
                    })

        return channels

    def validate_label_map(self):
        """Validate _LABEL_MAP and report any incomplete or missing mappings."""
        issues = []

        # Check for incomplete mappings
        for label, mapping_str in self._LABEL_MAP.items():
            if mapping_str == "voltage":
                issues.append(f"Incomplete mapping: '{label}' -> 'voltage' (missing channel number)")
            else:
                # Try to resolve the mapping
                device_channel = self._resolve_channel(mapping_str)
                if device_channel is None:
                    issues.append(f"Invalid mapping: '{label}' -> '{mapping_str}' (channel not found in any device)")

        if self._log and issues:
            self._log.Warning(f"GPIO _LABEL_MAP validation found {len(issues)} issues:")
            for issue in issues:
                self._log.Warning(f"  - {issue}")

        return issues

    def list_devices(self):
        """List all GPIO devices found in the IIO context."""
        return [{"name": name, "label": getattr(dev, 'label', 'N/A')} for name, dev in self._devices.items()]


# ---------------------------------------------------------------------------
# LO Band Presets
# ---------------------------------------------------------------------------
# Each LO preset describes the ADF4382 frequency state for a
# given frequency plan.  The dict keys are user-facing band names.

LO_PRESETS = {
    # Band name → lo_frequency
    "13p9GHz": {
        "lo_frequency": 13_900_000_000,
    },
    "13p4GHz": {
        "lo_frequency": 13_400_000_000,
    },
    "14p9GHz": {
        "lo_frequency": 14_900_000_000,
    },
    "16p4GHz": {
        "lo_frequency": 16_400_000_000,
    },
}


# ===================================================================
# LoChain  (shared LO — ADF4382)
# ===================================================================

class LoChain:
    """One complete LO signal chain.

    The LO chain is shared between the RX and TX paths and should be
    configured once before setting RX or TX bands.

    Composed of:
      * ADF4382  (PLL/VCO — LO frequency source)
    """

    def __init__(self, ctx, gpio: GpioHelper, log=None):
        self._ctx = ctx
        self._gpio = gpio
        self._log = log

        dev = _find_iio_device(ctx, "adf4382_lo")
        self.adf4382 = ADF4382(dev) if dev else None

        self._current_preset = None

    def _info(self, msg):
        if self._log:
            self._log.Info(msg)

    def _warn(self, msg):
        if self._log:
            self._log.Warning(msg)

    # -- Initialization ------------------------------------------------------
    def initialize(self):
        """Bring-up ADF4382 on this LO channel."""
        results = []

        # -- ADF4382 ---------------------------------------------------------
        if self.adf4382:
            try:
                # Enable output
                self.adf4382.set_enable(True)
                freq = self.adf4382.get_frequency()
                results.append({"device": "adf4382_lo",
                                "pid": None, "pass": True})
                self._info(f"adf4382_lo present, freq={freq} Hz")
            except Exception as e:
                self._warn(f"adf4382_lo init error: {e}")
                results.append({"device": "adf4382_lo",
                                "pid": None, "pass": False})
        else:
            results.append({"device": "adf4382_lo",
                            "pid": None, "pass": False})

        return results

    # -- Preset configuration ------------------------------------------------
    @staticmethod
    def list_presets():
        """Return the names of all available LO presets."""
        return list(LO_PRESETS.keys())

    def set_preset(self, preset_name: str):
        """Configure the full LO chain for a named preset.

        Sets the ADF4382 output frequency and associated GPIO
        filter-select lines.

        Parameters
        ----------
        preset_name : str
            One of the keys in ``LO_PRESETS`` (e.g. ``"15GHz"``).
        """
        preset = LO_PRESETS.get(preset_name)
        if preset is None:
            raise ValueError(
                f"Unknown LO preset '{preset_name}'. "
                f"Valid: {', '.join(self.list_presets())}"
            )

        ch = self.channel
        self._info(f"LO{ch}: setting preset → {preset_name}")

        # ADF4382 — set PLL frequency
        if self.adf4382:
            lo_freq = preset.get("lo_frequency")
            if lo_freq is not None:
                self.adf4382.set_frequency(lo_freq)
                self._info(f"LO{ch}: ADF4382 frequency → {lo_freq} Hz")

        # Settling time for LO lock
        time.sleep(0.5)

        self._current_preset = preset_name

    # -- Direct frequency control --------------------------------------------
    def set_frequency(self, freq_hz: int):
        """Set the ADF4382 output frequency directly (Hz)."""
        if self.adf4382:
            self.adf4382.set_frequency(freq_hz)
            self._info(f"LO{self.channel}: ADF4382 frequency → {freq_hz} Hz")

    def get_frequency(self) -> int:
        """Read back the ADF4382 output frequency (Hz)."""
        if self.adf4382:
            return self.adf4382.get_frequency()
        return 0

    def check_pll_lock(self):
        """Read ADF4382 register 0x58 and check bit 0 for PLL lock status."""
        if not self.adf4382:
            self._warn("ADF4382 device not available — cannot check PLL lock")
            return False
        reg_val = self.adf4382.reg_read(0x58)
        locked = bool(reg_val & 0x01)
        self._info(f"ADF4382 PLL Lock Register 0x58 = 0x{reg_val:02X}, Locked = {locked}")
        return locked

    def read_temperature(self) -> int:
        """Read ADF4382 on-chip temperature sensor (°C)."""
        if not self.adf4382:
            self._warn("ADF4382 device not available — cannot read temperature")
            return None
        temp = self.adf4382.read_temperature()
        self._info(f"LO{self.channel}: ADF4382 chip temperature = {temp} °C")
        return temp

    # -- Per-output power control (IIO altvoltage0/1) -------------------------
    def set_outa_power(self, power: int, enable: bool = True):
        """Set OUTA (altvoltage0) power level (0-3) and enable state."""
        if not self.adf4382:
            self._warn("ADF4382 device not available — cannot set OUTA power")
            return
        self.adf4382.set_outa_power(power)
        self.adf4382.set_outa_enable(enable)
        self._info(f"LO{self.channel}: OUTA power={power}, enable={enable}")

    def get_outa_power(self):
        """Read back OUTA (altvoltage0) power level and enable state."""
        if not self.adf4382:
            self._warn("ADF4382 device not available — cannot read OUTA power")
            return None, None
        return self.adf4382.get_outa_power(), self.adf4382.get_outa_enable()

    def set_outb_power(self, power: int, enable: bool = True):
        """Set OUTB (altvoltage1) power level (0-3) and enable state."""
        if not self.adf4382:
            self._warn("ADF4382 device not available — cannot set OUTB power")
            return
        self.adf4382.set_outb_power(power)
        self.adf4382.set_outb_enable(enable)
        self._info(f"LO{self.channel}: OUTB power={power}, enable={enable}")

    def get_outb_power(self):
        """Read back OUTB (altvoltage1) power level and enable state."""
        if not self.adf4382:
            self._warn("ADF4382 device not available — cannot read OUTB power")
            return None, None
        return self.adf4382.get_outb_power(), self.adf4382.get_outb_enable()

    def set_output_power(self, outa_power: int, outb_power: int,
                         outa_en: bool = True, outb_en: bool = True):
        """Set both OUTA and OUTB power levels and enable states together."""
        self.set_outa_power(outa_power, outa_en)
        self.set_outb_power(outb_power, outb_en)

    # -- Band-1 config --------------------------------------------
    def set_band1(self, state):
        """Configure the LO chain for Band-1 operation."""
        if (state=="init"):
            self.reg_write(0x000,0x18) 
            self.reg_write(0x001,0x00)
            self.reg_write(0x00A,0x5A)
            #self.reg_write(0x010,0x71)
            self.reg_write(0x011,0x00)
            self.reg_write(0x012,0xAA)
            self.reg_write(0x013,0xAA)
            self.reg_write(0x014,0x3C)
            self.reg_write(0x015,0x82)
            self.reg_write(0x016,0x85)
            self.reg_write(0x017,0x86)
            self.reg_write(0x018,0xA6)
            self.reg_write(0x019,0xAA)
            self.reg_write(0x01A,0xC9)
            self.reg_write(0x01B,0xF9)
            self.reg_write(0x01C,0xFF)
            self.reg_write(0x01D,0x09)
            self.reg_write(0x01E,0x24)
            self.reg_write(0x01F,0x1F)
            self.reg_write(0x020,0x81)
            self.reg_write(0x021,0x00)
            self.reg_write(0x022,0x00)
            self.reg_write(0x023,0x00)
            self.reg_write(0x024,0x00)
            self.reg_write(0x025,0x01)
            self.reg_write(0x026,0x00)
            self.reg_write(0x027,0xF0)
            self.reg_write(0x028,0x20)
            self.reg_write(0x029,0x55)
            self.reg_write(0x02A,0x30)
            #self.reg_write(0x02B,0x00)
            self.reg_write(0x02C,0x89)
            self.reg_write(0x02D,0xF1)
            self.reg_write(0x02E,0x10)
            self.reg_write(0x02F,0xBF)
            self.reg_write(0x030,0x2F)
            self.reg_write(0x031,0x6B)
            self.reg_write(0x032,0x40)
            self.reg_write(0x033,0x00)
            self.reg_write(0x034,0x36)
            self.reg_write(0x035,0x3F)
            self.reg_write(0x036,0x80)
            self.reg_write(0x037,0x42)
            self.reg_write(0x038,0xEB)
            self.reg_write(0x039,0x80)
            self.reg_write(0x03A,0x7B)
            self.reg_write(0x03B,0x00)
            self.reg_write(0x03C,0x00)
            self.reg_write(0x03D,0x00)         #set to 1.8v CMOS logic
            self.reg_write(0x03E,0x4D)
            self.reg_write(0x03F,0x82)
            self.reg_write(0x040,0x00)
            self.reg_write(0x041,0x00)
            self.reg_write(0x042,0x01)
            self.reg_write(0x043,0xB8)
            self.reg_write(0x044,0x2E)
            self.reg_write(0x045,0x52)
            self.reg_write(0x04B,0x5D)
            self.reg_write(0x04C,0x2B)
            self.reg_write(0x04D,0x00)
            self.reg_write(0x04F,0x08)
            self.reg_write(0x053,0x45)
            self.reg_write(0x054,0x01)             
            self.reg_write(0x100,0x3F)
            self.reg_write(0x101,0x3F)
            self.reg_write(0x102,0x3F)
            self.reg_write(0x103,0x3F)
            self.reg_write(0x104,0x3F)
            self.reg_write(0x105,0x3F)
            self.reg_write(0x106,0x3F)
            self.reg_write(0x107,0x3F)
            self.reg_write(0x108,0x3F)
            self.reg_write(0x109,0x25)
            self.reg_write(0x10A,0x25)
            self.reg_write(0x10B,0x3F)
            self.reg_write(0x10C,0x3F)
            self.reg_write(0x10D,0x3F)
            self.reg_write(0x10E,0x3F)
            self.reg_write(0x10F,0x3F)
            self.reg_write(0x110,0x3F)
            self.reg_write(0x111,0x3F)
            self.reg_write(0x200,0x00)
            self.reg_write(0x201,0x00)
            self.reg_write(0x202,0x00)
            self.reg_write(0x203,0x00)

        else:
            self.reg_write(0x02B,0x00) #PD_ALL = 0
            self.reg_write(0x010,0x71) #Start auto-calibration
            time.sleep(0.1) #Wait for calibration to complete

            lock_status = []
            refClk_status = []
            status = self.reg_read(0x58) 
            ok= lock_status == status & 0x1
            self._info(f"adf4382 LOCK STATUS: {'PASS' if ok else 'FAIL'}")

            ok= refClk_status == status & 0x8
            self._info(f"adf4382 REF CLOCK STATUS: {'PASS' if ok else 'FAIL'}")

    # -- Band-2 config --------------------------------------------
    def set_band2(self,state):    
        if (state=="init"):
            self.reg_write(0x000 ,0x18  )
            self.reg_write(0x001 ,0x00  )
            self.reg_write(0x00A ,0x5A  )
            #self.reg_write(0x010 ,0x6D  )
            self.reg_write(0x011 ,0x00  )
            self.reg_write(0x012 ,0x55  )
            self.reg_write(0x013 ,0x55  )
            self.reg_write(0x014 ,0x19  )
            self.reg_write(0x015 ,0x82  )
            self.reg_write(0x016 ,0x85  )
            self.reg_write(0x017 ,0x43  )
            self.reg_write(0x018 ,0x53  )
            self.reg_write(0x019 ,0x55  )
            self.reg_write(0x01A ,0xC9  )
            self.reg_write(0x01B ,0xF9  )
            self.reg_write(0x01C ,0xFF  )
            self.reg_write(0x01D ,0x09  )
            self.reg_write(0x01E ,0x24  )
            self.reg_write(0x01F ,0x1F  )
            self.reg_write(0x020 ,0x81  )
            self.reg_write(0x021 ,0x00  )
            self.reg_write(0x022 ,0x00  )
            self.reg_write(0x023 ,0x00  )
            self.reg_write(0x024 ,0x00  )
            self.reg_write(0x025 ,0x01  )
            self.reg_write(0x026 ,0x00  )
            self.reg_write(0x027 ,0xF0  )
            self.reg_write(0x028 ,0x20  )
            self.reg_write(0x029 ,0x55  )
            self.reg_write(0x02A ,0x30  )
            #self.reg_write(0x02B ,0x00  )
            self.reg_write(0x02C ,0x89  )
            self.reg_write(0x02D ,0xF1  )
            self.reg_write(0x02E ,0x10  )
            self.reg_write(0x02F ,0xBF  )
            self.reg_write(0x030 ,0x2F  )
            self.reg_write(0x031 ,0x6B  )
            self.reg_write(0x032 ,0x40  )
            self.reg_write(0x033 ,0x00  )
            self.reg_write(0x034 ,0x36  )
            self.reg_write(0x035 ,0x3F  )
            self.reg_write(0x036 ,0x80  )
            self.reg_write(0x037 ,0x42  )
            self.reg_write(0x038 ,0xEB  )
            self.reg_write(0x039 ,0x80  )
            self.reg_write(0x03A ,0x7B  )
            self.reg_write(0x03B ,0x00  )
            self.reg_write(0x03C ,0x00  )
            self.reg_write(0x03D ,0x00  )       #set to 1.8v CMOS logic
            self.reg_write(0x03E ,0x4D  )
            self.reg_write(0x03F ,0x82  )
            self.reg_write(0x040 ,0x00  )
            self.reg_write(0x041 ,0x00  )
            self.reg_write(0x042 ,0x01  )
            self.reg_write(0x043 ,0xB8  )
            self.reg_write(0x044 ,0x2E  )
            self.reg_write(0x045 ,0x52  )
            self.reg_write(0x04B ,0x5D  )
            self.reg_write(0x04C ,0x2B  )
            self.reg_write(0x04D ,0x00  )
            self.reg_write(0x04F ,0x08  )
            self.reg_write(0x053 ,0x45  )
            self.reg_write(0x054 ,0x01  )
            self.reg_write(0x100 ,0x3F  )
            self.reg_write(0x101 ,0x3F  )
            self.reg_write(0x102 ,0x3F  )
            self.reg_write(0x103 ,0x3F  )
            self.reg_write(0x104 ,0x3F  )
            self.reg_write(0x105 ,0x3F  )
            self.reg_write(0x106 ,0x3F  )
            self.reg_write(0x107 ,0x3F  )
            self.reg_write(0x108 ,0x3F  )
            self.reg_write(0x109 ,0x25  )
            self.reg_write(0x10A ,0x25  )
            self.reg_write(0x10B ,0x3F  )
            self.reg_write(0x10C ,0x3F  )
            self.reg_write(0x10D ,0x3F  )
            self.reg_write(0x10E ,0x3F  )
            self.reg_write(0x10F ,0x3F  )
            self.reg_write(0x110 ,0x3F  )
            self.reg_write(0x111 ,0x3F  )
            self.reg_write(0x200 ,0x00  )
            self.reg_write(0x201 ,0x00  )
            self.reg_write(0x202 ,0x00  )
            self.reg_write(0x203 ,0x00  )
   
        else:
            self.reg_write(0x02B ,0x00) #PD_ALL = 0
            self.reg_write(0x010 ,0x6D) #Start auto-calibration
            time.sleep(0.1) #Wait for calibration to complete

            lock_status = []
            refClk_status = []
            status = self.reg_read(0x58) 
            ok= lock_status == status & 0x1
            self._info(f"adf4382 LOCK STATUS: {'PASS' if ok else 'FAIL'}")

            ok= refClk_status == status & 0x8
            self._info(f"adf4382 REF CLOCK STATUS: {'PASS' if ok else 'FAIL'}")

    # -- Band-3 config --------------------------------------------
    def set_band3(self,state):
        if (state=="init"):
            self.reg_write(0x000,0x18) 
            self.reg_write(0x001,0x00)
            self.reg_write(0x00A,0x5A)
            #self.reg_write(0x010,0x79)
            self.reg_write(0x011,0x00)
            self.reg_write(0x012,0x55)
            self.reg_write(0x013,0x55)
            self.reg_write(0x014,0x83)
            self.reg_write(0x015,0x82)
            self.reg_write(0x016,0x85)
            self.reg_write(0x017,0x43)
            self.reg_write(0x018,0x53)
            self.reg_write(0x019,0x55)
            self.reg_write(0x01A,0xC9)
            self.reg_write(0x01B,0xF9)
            self.reg_write(0x01C,0xFF)
            self.reg_write(0x01D,0x09)
            self.reg_write(0x01E,0x24)
            self.reg_write(0x01F,0x1F)
            self.reg_write(0x020,0x81)
            self.reg_write(0x021,0x00)
            self.reg_write(0x022,0x00)
            self.reg_write(0x023,0x00)
            self.reg_write(0x024,0x00)
            self.reg_write(0x025,0x01)
            self.reg_write(0x026,0x00)
            self.reg_write(0x027,0xF0)
            self.reg_write(0x028,0x20)
            self.reg_write(0x029,0x55)
            self.reg_write(0x02A,0x30)
            #self.reg_write(0x02B,0x00)
            self.reg_write(0x02C,0x89)
            self.reg_write(0x02D,0xF1)
            self.reg_write(0x02E,0x10)
            self.reg_write(0x02F,0xBF)
            self.reg_write(0x030,0x2F)
            self.reg_write(0x031,0x6B)
            self.reg_write(0x032,0x40)
            self.reg_write(0x033,0x00)
            self.reg_write(0x034,0x36)
            self.reg_write(0x035,0x3F)
            self.reg_write(0x036,0x80)
            self.reg_write(0x037,0x42)
            self.reg_write(0x038,0xEB)
            self.reg_write(0x039,0x80)
            self.reg_write(0x03A,0x7B)
            self.reg_write(0x03B,0x00)
            self.reg_write(0x03C,0x00)
            self.reg_write(0x03D,0x00)      #set to 1.8v CMOS logic
            self.reg_write(0x03E,0x4D)
            self.reg_write(0x03F,0x82)
            self.reg_write(0x040,0x00)
            self.reg_write(0x041,0x00)
            self.reg_write(0x042,0x01)
            self.reg_write(0x043,0xB8)
            self.reg_write(0x044,0x2E)
            self.reg_write(0x045,0x52)
            self.reg_write(0x04B,0x5D)
            self.reg_write(0x04C,0x2B)
            self.reg_write(0x04D,0x00)
            self.reg_write(0x04F,0x08)
            self.reg_write(0x053,0x45)
            self.reg_write(0x054,0x01)
            self.reg_write(0x100,0x3F)
            self.reg_write(0x101,0x3F)
            self.reg_write(0x102,0x3F)
            self.reg_write(0x103,0x3F)
            self.reg_write(0x104,0x3F)
            self.reg_write(0x105,0x3F)
            self.reg_write(0x106,0x3F)
            self.reg_write(0x107,0x3F)
            self.reg_write(0x108,0x3F)
            self.reg_write(0x109,0x25)
            self.reg_write(0x10A,0x25)
            self.reg_write(0x10B,0x3F)
            self.reg_write(0x10C,0x3F)
            self.reg_write(0x10D,0x3F)
            self.reg_write(0x10E,0x3F)
            self.reg_write(0x10F,0x3F)
            self.reg_write(0x110,0x3F)
            self.reg_write(0x111,0x3F)
            self.reg_write(0x200,0x00)
            self.reg_write(0x201,0x00)
            self.reg_write(0x202,0x00)
            self.reg_write(0x203,0x00)

        else:
            self.reg_write(0x02B ,0x00) #PD_ALL = 0
            self.reg_write(0x010 ,0x79) #Start auto-calibration
            time.sleep(0.1) #Wait for calibration to complete

            lock_status = []
            refClk_status = []
            status = self.reg_read(0x58) 
            ok= lock_status == status & 0x1
            self._info(f"adf4382 LOCK STATUS: {'PASS' if ok else 'FAIL'}")

            ok= refClk_status == status & 0x8
            self._info(f"adf4382 REF CLOCK STATUS: {'PASS' if ok else 'FAIL'}")

    # -- Band-4 config --------------------------------------------
    def set_band4(self,state):
        if (state=="init"):
            self.reg_write(0x000,0x18) 
            self.reg_write(0x001,0x00)
            self.reg_write(0x00A,0x5A)
            #self.reg_write(0x010,0x85)
            self.reg_write(0x011,0x00)
            self.reg_write(0x012,0x55)
            self.reg_write(0x013,0x55)
            self.reg_write(0x014,0xED)
            self.reg_write(0x015,0x82)
            self.reg_write(0x016,0x85)
            self.reg_write(0x017,0x43)
            self.reg_write(0x018,0x53)
            self.reg_write(0x019,0x55)
            self.reg_write(0x01A,0xC9)
            self.reg_write(0x01B,0xF9)
            self.reg_write(0x01C,0xFF)
            self.reg_write(0x01D,0x09)
            self.reg_write(0x01E,0x24)
            self.reg_write(0x01F,0x1F)
            self.reg_write(0x020,0x81)
            self.reg_write(0x021,0x00)
            self.reg_write(0x022,0x00)
            self.reg_write(0x023,0x00)
            self.reg_write(0x024,0x00)
            self.reg_write(0x025,0x01)
            self.reg_write(0x026,0x00)
            self.reg_write(0x027,0xF0)
            self.reg_write(0x028,0x20)
            self.reg_write(0x029,0x55)
            self.reg_write(0x02A,0x30)
            #self.reg_write(0x02B,0x00)
            self.reg_write(0x02C,0x89)
            self.reg_write(0x02D,0xF1)
            self.reg_write(0x02E,0x10)
            self.reg_write(0x02F,0xBF)
            self.reg_write(0x030,0x2F)
            self.reg_write(0x031,0x6B)
            self.reg_write(0x032,0x40)
            self.reg_write(0x033,0x00)
            self.reg_write(0x034,0x36)
            self.reg_write(0x035,0x3F)
            self.reg_write(0x036,0x80)
            self.reg_write(0x037,0x42)
            self.reg_write(0x038,0xEB)
            self.reg_write(0x039,0x80)
            self.reg_write(0x03A,0x7B)
            self.reg_write(0x03B,0x00)
            self.reg_write(0x03C,0x00)
            self.reg_write(0x03D,0x00)           #set to 1.8v CMOS logic
            self.reg_write(0x03E,0x4D)
            self.reg_write(0x03F,0x82)
            self.reg_write(0x040,0x00)
            self.reg_write(0x041,0x00)
            self.reg_write(0x042,0x01)
            self.reg_write(0x043,0xB8)
            self.reg_write(0x044,0x2E)
            self.reg_write(0x045,0x52)
            self.reg_write(0x04B,0x5D)
            self.reg_write(0x04C,0x2B)
            self.reg_write(0x04D,0x00)
            self.reg_write(0x04F,0x08)
            self.reg_write(0x053,0x45)
            self.reg_write(0x054,0x01)
            self.reg_write(0x100,0x3F)
            self.reg_write(0x101,0x3F)
            self.reg_write(0x102,0x3F)
            self.reg_write(0x103,0x3F)
            self.reg_write(0x104,0x3F)
            self.reg_write(0x105,0x3F)
            self.reg_write(0x106,0x3F)
            self.reg_write(0x107,0x3F)
            self.reg_write(0x108,0x3F)
            self.reg_write(0x109,0x25)
            self.reg_write(0x10A,0x25)
            self.reg_write(0x10B,0x3F)
            self.reg_write(0x10C,0x3F)
            self.reg_write(0x10D,0x3F)
            self.reg_write(0x10E,0x3F)
            self.reg_write(0x10F,0x3F)
            self.reg_write(0x110,0x3F)
            self.reg_write(0x111,0x3F)
            self.reg_write(0x200,0x00)
            self.reg_write(0x201,0x00)
            self.reg_write(0x202,0x00)
            self.reg_write(0x203,0x00)
        else:
            self.reg_write(0x02B ,0x00) #PD_ALL = 0
            self.reg_write(0x010 ,0x85) #Start auto-calibration
            time.sleep(0.1) #Wait for calibration to complete

            lock_status = []
            refClk_status = []
            status = self.reg_read(0x58)        
            ok= lock_status == status & 0x1
            self._info(f"adf4382 LOCK STATUS: {'PASS' if ok else 'FAIL'}")
                                            
            ok= refClk_status == status & 0x8
            self._info(f"adf4382 REF CLOCK STATUS: {'PASS' if ok else 'FAIL'}")

    # -- Raw register access -------------------------------------------------
    def reg_read(self, addr):
        if self.adf4382:
            return self.adf4382.reg_read(addr)
        return None

    def reg_write(self, addr, val):
        if self.adf4382:
            self.adf4382.reg_write(addr, val)


# ===================================================================
# FilterChain  (shared tunable filter — ADMV8913)
# ===================================================================

class FilterChain:
    """One shared ADMV8913 tunable filter chain (channel 1-4).

    The ADMV8913 is shared between the RX and TX paths on each channel
    and should be configured once for a given band before using either
    RX or TX.

    Composed of:
      * ADMV8913  (tunable filter with 4-bit HPF and 4-bit LPF)
    """

    def __init__(self, channel: int, ctx, log=None):
        self.channel = channel
        self._ctx = ctx
        self._log = log

        dev = _find_iio_device(ctx, f"admv8913_{channel}")
        self.admv8913 = ADMV8913(dev) if dev else None

    def _info(self, msg):
        if self._log:
            self._log.Info(msg)

    def _warn(self, msg):
        if self._log:
            self._log.Warning(msg)

    # -- Initialization ------------------------------------------------------
    def initialize(self):
        """Bring-up the ADMV8913 on this channel: 4-wire SPI, verify PID."""
        results = []
        ch = self.channel

        if self.admv8913:
            try:
                d = self.admv8913
                d.reg_write(0x0, 0x81)
                time.sleep(1e-3)
                d.reg_write(0x0, 0x18)
                pid0 = d.reg_read(0x4)
                pid1 = d.reg_read(0x5)
                pid = (pid1 << 8) | pid0
                ok = pid == 0x8913
                results.append({"device": f"admv8913_{ch}",
                                "pid": pid, "pass": ok})
                self._info(f"admv8913_{ch} PID=0x{pid:04x} "
                           f"{'PASS' if ok else 'FAIL'}")
            except Exception as e:
                self._warn(f"admv8913_{ch} init error: {e}")
                results.append({"device": f"admv8913_{ch}",
                                "pid": None, "pass": False})
        else:
            results.append({"device": f"admv8913_{ch}",
                            "pid": None, "pass": False})

        return results

    # -- Direct HPF/LPF control (IIO channel attributes) ---------------------
    def set_hpf(self, val: int):
        """Set HPF via IIO channel attribute (4-bit, 0-15)."""
        if self.admv8913:
            self.admv8913.set_direct_hpf(val)
            self._info(f"Filter{self.channel}: ADMV8913 HPF={val}")

    def set_lpf(self, val: int):
        """Set LPF via IIO channel attribute (4-bit, 0-15)."""
        if self.admv8913:
            self.admv8913.set_direct_lpf(val)
            self._info(f"Filter{self.channel}: ADMV8913 LPF={val}")

    # -- Register-based HPF/LPF (fallback for early driver revisions) --------
    def set_hpf_reg(self, val: int):
        """Set HPF via direct register write (4-bit, 0-15)."""
        if self.admv8913:
            self.admv8913.set_hpf_reg(val)
            self._info(f"Filter{self.channel}: ADMV8913 HPF (reg)={val}")

    def set_lpf_reg(self, val: int):
        """Set LPF via direct register write (4-bit, 0-15)."""
        if self.admv8913:
            self.admv8913.set_lpf_reg(val)
            self._info(f"Filter{self.channel}: ADMV8913 LPF (reg)={val}")

    # -- LUT programming -----------------------------------------------------
    def load_lut(self, entries):
        """Write ADMV8913 LUT entries to hardware.

        Parameters
        ----------
        entries : list
            ``ADMV8913LutEntry`` objects (or pre-formatted strings).
        """
        if self.admv8913 is None:
            return
        for entry in entries:
            s = entry.format() if hasattr(entry, "format") else str(entry)
            self.admv8913.write_lut_entry(s)
        self._info(f"Filter{self.channel}: loaded {len(entries)} "
                   f"ADMV8913 LUT entries")

    def read_lut(self) -> str:
        """Read the full LUT (all 64 entries)."""
        if self.admv8913:
            return self.admv8913.read_lut()
        return ""

    # -- Fast-latch control --------------------------------------------------
    def set_fast_latch_load(self):
        if self.admv8913:
            self.admv8913.set_fast_latch_load()

    def set_fast_latch_pointer(self, val: int):
        if self.admv8913:
            self.admv8913.set_fast_latch_pointer(val)

    def set_fast_latch_stop(self, val: int):
        if self.admv8913:
            self.admv8913.set_fast_latch_stop(val)

    def set_fast_latch_start(self, val: int):
        if self.admv8913:
            self.admv8913.set_fast_latch_start(val)

    def set_fast_latch_direction(self, forward: bool):
        if self.admv8913:
            self.admv8913.set_fast_latch_direction(forward)

    # -- Raw register access -------------------------------------------------
    def reg_read(self, addr):
        if self.admv8913:
            return self.admv8913.reg_read(addr)
        return None

    def reg_write(self, addr, val):
        if self.admv8913:
            self.admv8913.reg_write(addr, val)

    def set_band1(self):
        self.set_lpf_reg(0x04)
        self.set_hpf_reg(0x07)
    def set_band2(self):
        self.set_lpf_reg(0x09)
        self.set_hpf_reg(0x06)
    def set_band3(self):
        self.set_lpf_reg(0x12)
        self.set_hpf_reg(0x09)
    def set_band4(self):
        self.set_lpf_reg(0x14)
        self.set_hpf_reg(0x12)
# ---------------------------------------------------------------------------
# System-level RX Band Configurations
# ---------------------------------------------------------------------------
# Each key maps to the complete per-device settings for one system band.

RX_BAND_CONFIGS = {
    # --- Mixer bands (with LO) ---
    "Band1": {
        "admv1420_rf_band": "6GHz_20GHz",
        "admv1420_if_band": "3GHz_13GHz",
        "admv1420_if_mode": "if",
        "admv1420_lo_sideband": "LSB",
        "admv1420_lo_x3_filter": "14GHz_18GHz",
        "lo_preset":        "13p9GHz",
        "use_mixer":        True,
    },
    "Band2": {
        "admv1420_rf_band": "6GHz_20GHz",
        "admv1420_if_band": "3GHz_13GHz",
        "admv1420_if_mode": "if",
        "admv1420_lo_sideband": "LSB",
        "admv1420_lo_x3_filter": "18GHz_24GHz",
        "lo_preset":        "13p4GHz",
        "use_mixer":        True,
    },
    "Band3": {
        "admv1420_rf_band": "6GHz_20GHz",
        "admv1420_if_band": "3GHz_13GHz",
        "admv1420_if_mode": "if",
        "admv1420_lo_sideband": "LSB",
        "admv1420_lo_x3_filter": "24GHz_28GHz",
        "lo_preset":        "14p9GHz",
        "use_mixer":        True,
    },
    "Band4": {
        "admv1420_rf_band": "6GHz_20GHz",
        "admv1420_if_band": "3GHz_13GHz",
        "admv1420_if_mode": "if",
        "admv1420_lo_sideband": "LSB",
        "admv1420_lo_x3_filter": "24GHz_28GHz",
        "lo_preset":        "16p4GHz",
        "use_mixer":        True,
    },
    
}

# ---------------------------------------------------------------------------
# System-level TX Band Configurations
# ---------------------------------------------------------------------------

TX_BAND_CONFIGS = {
   
    # --- Mixer bands ---
    "Band1": {
        "admv1320_mixer_bypass_en" : False,
        "admv1320_rf_band": "6GHz_20GHz",
        "admv1320_if_band": "3GHz_12GHz", #"1p7GHz_9GHz",
        "admv1320_if_mode": "if",
        "admv1320_lo_sideband": "LSB",
        "admv1320_lo_x3_filter": "13GHz_17GHz",
        "lo_preset":        "13p9GHz",
        "use_mixer":        True,       
    },
    "Band2": {
        "admv1320_mixer_bypass_en" : False,
        "admv1320_rf_band": "6GHz_20GHz",
        "admv1320_if_band": "3GHz_12GHz", #"1p7GHz_9GHz",
        "admv1320_if_mode": "if",
        "admv1320_lo_sideband": "LSB",
        "admv1320_lo_x3_filter": "17GHz_23GHz",
        "lo_preset":        "13p4GHz",
        "use_mixer":        True,
    },
    "Band3": {
        "admv1320_mixer_bypass_en" : False,
        "admv1320_rf_band": "6GHz_20GHz",
        "admv1320_if_band": "3GHz_12GHz", #"1p7GHz_9GHz",
        "admv1320_if_mode": "if",
        "admv1320_lo_sideband": "LSB",
        "admv1320_lo_x3_filter": "23GHz_28GHz",
        "lo_preset":        "14p9GHz",
        "use_mixer":        True,
    },
    "Band4": {
        "admv1320_mixer_bypass_en" : False,
        "admv1320_rf_band": "6GHz_20GHz",
        "admv1320_if_band": "3GHz_12GHz", #"1p7GHz_9GHz",
        "admv1320_if_mode": "if",
        "admv1320_lo_sideband": "LSB",
        "admv1320_lo_x3_filter": "23GHz_28GHz",
        "lo_preset":        "16p4GHz",
        "use_mixer":        True,
    },
}


# ---------------------------------------------------------------------------
# DSA value conversion helper
# ---------------------------------------------------------------------------

def _dsa_int_to_str(val: int) -> str:
    """Convert an integer attenuation value to a DSA gain string.

    Parameters
    ----------
    val : int
        Attenuation in positive dB (0-15).  ``0`` → ``"0dB"``,
        ``5`` → ``"-5dB"``, ``15`` → ``"-15dB"``.

    Returns
    -------
    str
        Gain string accepted by the ADMV1420 / ADMV1320 IIO driver.
    """
    val = max(0, int(val))
    return "0dB" if val == 0 else f"-{val}dB"


# ===================================================================
# Helper: find IIO device by label / name
# ===================================================================

def _find_iio_device(ctx, label: str):
    """Return the IIO device whose ``label`` or ``name`` matches *label*, or None."""
    if ctx is None:
        return None
    for d in ctx.devices:
        if getattr(d, "label", None) == label or d.name == label:
            return d
    return None

# ===================================================================
# UDC Power up sequencer - manual control of the power enable signals 
# ===================================================================
class PowerSeqeuence:

    def __init__(self, channel: int, ctx, gpio: GpioHelper, log=None):
        self.channel = channel
        self._ctx = ctx
        self._gpio = gpio
        self._log = log

        # Compose chain instances — reuse channel/ctx/gpio/log
        self.lo_chain = LoChain(channel, ctx, gpio, log)
        self.rx_chain = RxChain(channel, ctx, gpio, log)
        self.tx_chain = TxChain(channel, ctx, gpio, log)
        self.filt_chain = FilterChain(channel, ctx, log)

    def powerUpLDOs(self):

        ch = self.channel
        #=======================================
        #Set all key GPIOs to low to start power-up sequence in known state
        self._gpio.write(f"ADMV1420_RX_CEN_{ch}",0)
        self._gpio.write(f"ADMV1420_RX_RSTB_{ch}",0)

        self._gpio.write(f"ADMV1320_TX_CEN_{ch}",0)
        self._gpio.write(f"ADMV1320_TX_RSTB_{ch}",0)

        self._gpio.write(f"ADRF5030_EN_{ch}",1)  # ADRF5030 disabled initially
		
        self._gpio.write(f"ADMV8913_FL_LDO_EN",1)  #use internal LDO supply
        self._gpio.write(f"ADMV8913_FL_RST_N",0)
        self._gpio.write(f"ADMV8913_FL_PS_N",0)
        self._gpio.write(f"ADMV8913_FL_SFL",0)

        self._gpio.write(f"ADF4382_LO_CE",0)

        #=======================================
        #Check FPGA_DONE status to make sure Artix fpga is fully configured 
        fpga_done_read = self._gpio.read(f"FPGA_DONE")
        self._info(f"FPGA_DONE: {fpga_done_read}")
        if fpga_done_read != 1:
            self._warn(f"FPGA_DONE is not high, power-up sequence may fail")
            return

        #UDC_PG should be high to indicate 
        udc_pg_read = self._gpio.read(f"UDC_PG")
        self._info(f"UDC_PG: {udc_pg_read}")
        if udc_pg_read != 1:            
            self._warn(f"UDC_PG is not high, UDC power supplies may not be good")
            return

        #Turn on +5V LDO
        self._gpio.write(f"UDC_5P0V_PWR_EN",1)
        time.sleep(0.1)
        udc_5p0_ldo_read = self._gpio.read(f"UDC_5P0V_LDO_PG")
        self._info(f"UDC_5P0V_LDO_PG: {udc_5p0_ldo_read}")  
        if udc_5p0_ldo_read != 1:            
            self._warn(f"UDC_5P0V_LDO_PG is not high, 5V power supply may not be good")
            return

        #Turn on +3.3V LDO
        self._gpio.write(f"UDC_3P3V_PWR_EN",1) 
        time.sleep(0.1)
        udc_3p3_ldo_read = self._gpio.read(f"UDC_3P3V_LDO_PG")
        self._info(f"UDC_3P3V_LDO_PG: {udc_3p3_ldo_read}")    
        if udc_3p3_ldo_read != 1:            
            self._warn(f"UDC_3P3V_LDO_PG is not high, 3.3V power supply may not be good")
            return

        #Turn on -2.5V and -3.3V LDOs
        self._gpio.write(f"UDC_NEG_PWR_EN",1)
        time.sleep(0.1)
     
    def initDevices(self): 

        results = []
        ch = self.channel
        #=======================================
        #init ADF4382 LO 
        self._gpio.write(f"ADF4382_LO_CE",1)       # set chip enable high 
    
        self.lo_chain.reg_write(0x0, 0x81)          # soft reset
        self.lo_chain.reg_write(0x0, 0x18)          # 4-wire SPI
        self.lo_chain.reg_write(0x03D, 0x00)        # bit-5: 0=1.8v, 1=3.3v IO

        pid = self.lo_chain.reg_read(0xc)           # vendor ID
        ok = pid == 0x56
        results.append({"device": f"adf4382", "pid": pid, "pass": ok})
        self._info(f"adf4382 PID=0x{pid:02x} {'PASS' if ok else 'FAIL'}")

        #=======================================
        #init ADMV1420
        self._gpio.write(f"ADMV1420_RX_RSTB_{ch}",1)       # resetb high 

        self.rx_chain.reg_write(0x0, 0x81)          # soft reset
        self.rx_chain.reg_write(0x0, 0x18)          # 4-wire SPI
        self.rx_chain.reg_write(0x013, 0x00)        # bit-0: 0=1.8v, 1=3.3v IO

        self.rx_chain.reg_read(0x4)                 # chip id
        ok = pid == 0x68
        results.append({"device": f"admv1420", "pid": pid, "pass": ok})
        self._info(f"admv1420 PID=0x{pid:02x} {'PASS' if ok else 'FAIL'}")

        #=======================================
        #init ADMV1320
        self._gpio.write(f"ADMV1320_TX_RSTB_{ch}",1)       # resetb high 

        self.tx_chain.reg_write(0x0, 0x81)          # soft reset
        self.tx_chain.reg_write(0x0, 0x18)          # 4-wire SPI
        self.tx_chain.reg_write(0x013, 0x00)        # bit-0: 0=1.8v, 1=3.3v IO

        self.tx_chain.reg_read(0x4)                 # chip id
        ok = pid == 0x67
        results.append({"device": f"admv1320", "pid": pid, "pass": ok})
        self._info(f"admv1320 PID=0x{pid:02x} {'PASS' if ok else 'FAIL'}")

        #=======================================
        # init ADMV8913 filter
        self._gpio.write(f"ADMV8913_FL_RST_N",1)      # resetb high
        self._gpio.write(f"ADMV8913_FL_PS_N",1)       # spi mode
        self._gpio.write(f"ADMV8913_FL_SFL",0)        # fast latch disabled

        self.filt_chain.reg_write(0x00, 0x81)         # soft reset
        self.filt_chain.reg_write(0x00, 0x18)         # 4-wire SPI
        self.filt_chain.reg_read(0x4)                 # chip id

        ok = pid == 0x13
        results.append({"device": f"admv8913", "pid": pid, "pass": ok})
        self._info(f"admv8913 PID=0x{pid:02x} {'PASS' if ok else 'FAIL'}")

    def configDevices(self, band): 

        ch = self.channel
        #=======================================
        # Configure ADF4382 LO in band-2 configuration, clocks are disabled at this point until ADMV1x20 are configured
        if (band== "Band1"):
            self.lo_chain.set_band1("init")
        elif (band== "Band2"):
            self.lo_chain.set_band2("init")
        elif (band== "Band3"):
            self.lo_chain.set_band3("init")
        elif (band== "Band4"):
            self.lo_chain.set_band4("init")
        
        #=======================================
        # Configure ADMV1420         
        self._gpio.write(f"ADMV1420_RX_RSTB_{ch}",1)      # resetb high 
        self._gpio.write(f"ADMV1420_RX_CEN_{ch}",0)       # set chip enable low 
        self.rx_chain.set_band()
        self._gpio.write(f"ADMV1420_RX_CEN_{ch}",1)       # set chip enable high 

        #=======================================
        # Cofigure ADMV1320
        self._gpio.write(f"ADMV1320_TX_RSTB_{ch}",1)      # resetb high 
        self._gpio.write(f"ADMV1320_TX_CEN_{ch}",0)       # set chip enable low 
        if (band== "Band1"):
            self.tx_chain.set_band1()
        elif (band== "Band2"):
            self.tx_chain.set_band1()
        elif (band== "Band3"):
            self.tx_chain.set_band2()
        elif (band== "Band4"):
            self.tx_chain.set_band2()
        time.sleep(1e-3)
        self._gpio.write(f"ADMV1320_TX_CEN_{ch}",1)       # set chip enable high 

        #=======================================
        # Enable ADF4382 LO for specific band, auto-calibration mode
        if (band== "Band1"):
            self.lo_chain.set_band1("cal")
        elif (band== "Band2"):
            self.lo_chain.set_band2("cal")
        elif (band== "Band3"):
            self.lo_chain.set_band3("cal")
        elif (band== "Band4"):
            self.lo_chain.set_band4("cal")

        #=======================================
        # Enable AD5030 switch
        self._gpio.write(f"ADRF5030_EN_{ch}",0)  # ADRF5030 enabled

        #=======================================
        # Configure ADMV8913 filter
        if (band== "Band1"):                    
            self.filt_chain.set_band1()
        elif (band== "Band2"):
            self.filt_chain.set_band2()
        elif (band== "Band3"):
            self.filt_chain.set_band3()
        elif (band== "Band4"):
            self.filt_chain.set_band4()

    def powerDownLDOs(self):
        self._gpio.write(f"UDC_NEG_PWR_EN",0)
        time.sleep(0.1)

        self._gpio.write(f"UDC_3P3V_PWR_EN",0) 
        time.sleep(0.1)
        udc_3p3_ldo_read = self._gpio.read(f"UDC_3P3V_LDO_PG")
        self._info(f"UDC_3P3V_LDO_PG: {udc_3p3_ldo_read}")    
        if udc_3p3_ldo_read != 0:            
            self._warn(f"UDC_3P3V_LDO_PG is not low, 3.3V power supply not powered down")
            return

        self._gpio.write(f"UDC_5P0V_PWR_EN",0)
        time.sleep(0.1)
        udc_5p0_ldo_read = self._gpio.read(f"UDC_5P0V_LDO_PG")
        self._info(f"UDC_5P0V_LDO_PG: {udc_5p0_ldo_read}")  
        if udc_5p0_ldo_read != 0:            
            self._warn(f"UDC_5P0V_LDO_PG is not low, 5V power supply not powered down")
            return

    def powerDownDevices(self):
        ch = self.channel
        self._gpio.write(f"ADMV1420_RX_CEN_{ch}",0)
        self._gpio.write(f"ADMV1320_TX_CEN_{ch}",0)
        self._gpio.write(f"ADRF5030_EN_{ch}",1)  
        self._gpio.write(f"ADF4382_LO_CE",0)      # LO disabled
        self._gpio.write(f"ADMV8913_FL_RST_N",0)      
        self._gpio.write(f"ADMV1420_RX_RSTB_{ch}",0)
        self._gpio.write(f"ADMV1320_TX_RSTB_{ch}",0)

    def setRfSwitch(self, mode: str):
        """Set the ADRF5030 RF switch for RX or TX mode on this channel.

        Parameters
        ----------
        mode : str
            ``"RX"`` or ``"TX"``.
        """
        ch = self.channel
        mode = mode.upper()
        if mode not in ("RX", "TX"):
            self._warn(f"Invalid RF switch mode '{mode}', expected 'RX' or 'TX'")
            return

        ctrl_val = 0 if mode == "RX" else 1
        self._gpio.write(f"ADRF5030_EN_{ch}", 0)       # enable switch
        self._gpio.write(f"ADRF5030_CTRL_{ch}", ctrl_val)
        self._info(f"CH{ch}: ADRF5030 RF switch → {mode} (EN=0, CTRL={ctrl_val})")

                                            
# ===================================================================
# RxChain
# ===================================================================

class RxChain:
    """One complete RX signal chain (channel 1-4).

    Composed of:
      * ADMV1420  (down-converter)

    The LO (ADF4382) is managed separately via :class:`LoChain`
    and the tunable filter (ADMV8913) is managed via :class:`FilterChain`.
    Both should be configured before calling :meth:`set_band` on mixer bands.

    Parameters
    ----------
    channel : int
        Channel index (1-4).
    ctx : iio.Context
        IIO context connected to the ZCU SOM.
    gpio : GpioHelper
        For LO filter select GPIOs.
    log : optional
        OpenTAP-style logger (must have ``.Info()``, ``.Warning()``, etc.).
    """

    BAND_CONFIGS = RX_BAND_CONFIGS

    def __init__(self, channel: int, ctx, gpio: GpioHelper, log=None):
        self.channel = channel
        self._ctx = ctx
        self._gpio = gpio
        self._log = log

        # Wrap underlying IIO devices
        dev = _find_iio_device(ctx, f"admv1420_rx_{channel}")
        self.admv1420 = ADMV1420(dev) if dev else None

        self._current_band = None

    # -- Logging helpers -----------------------------------------------------
    def _info(self, msg):
        if self._log:
            self._log.Info(msg)

    def _warn(self, msg):
        if self._log:
            self._log.Warning(msg)

    # -- Initialization ------------------------------------------------------
    def initialize(self):
        """Run the bring-up sequence for every device on this RX channel.

        * Soft-reset + 4-wire SPI for ADMV1420
        * Put ADMV1420 in bypass mode with DSAs zeroed
        * Verify product IDs (where possible)
        """
        results = []
        ch = self.channel

        # -- ADMV1420 --------------------------------------------------------
        if self.admv1420:
            try:
                d = self.admv1420
                d.reg_write(0x0, 0x81)          # soft reset
                d.reg_write(0x0, 0x18)          # 4-wire SPI
                pid = d.reg_read(0x4)
                ok = pid == 0x1420
                results.append({"device": f"admv1420_rx_{ch}", "pid": pid, "pass": ok})
                self._info(f"admv1420_rx_{ch} PID=0x{pid:04x} {'PASS' if ok else 'FAIL'}")

                # Default bypass-mode register init (from existing ConfigureRxPath)
                d.set_filter_table_en(False)
                d.set_gain_table_en(False)
                d.set_bypass_gain_table_en(True)

                # Zero all DSAs via bypass registers
                d.set_rf_bypass_dsa1("0dB")
                d.set_rf_bypass_dsa2("0dB")
                d.set_rf_bypass_dsa3("0dB")
                d.set_if_bypass_dsa4("0dB")
                d.set_if_bypass_dsa5("0dB")

                # Default RF band (bypass)
                d.set_rf_band("100MHz_2GHz")
                d.set_if_mode("baseband")

            except Exception as e:
                self._warn(f"admv1420_rx_{ch} init error: {e}")
                results.append({"device": f"admv1420_rx_{ch}", "pid": None, "pass": False})
        else:
            results.append({"device": f"admv1420_rx_{ch}", "pid": None, "pass": False})

        return results

    # -- Band configuration --------------------------------------------------
    @classmethod
    def list_bands(cls):
        """Return the names of all available system bands."""
        return list(cls.BAND_CONFIGS.keys())

    def set_band(self, band_name: str):
        """Configure the entire RX chain for a system-level band.

        Parameters
        ----------
        band_name : str
            One of the keys in ``RX_BAND_CONFIGS``.
        """
        cfg = self.BAND_CONFIGS.get(band_name)
        if cfg is None:
            raise ValueError(
                f"Unknown RX band '{band_name}'. "
                f"Valid: {', '.join(self.list_bands())}"
            )

        ch = self.channel
        self._info(f"RX{ch}: setting band → {band_name}")

        # ADMV1420 RF band
        if self.admv1420:
            self.admv1420.set_rf_band(cfg["admv1420_rf_band"])
            self.admv1420.set_if_band(cfg.get("admv1420_if_band", "1GHz_5GHz"))
            if cfg["use_mixer"]:
                self.admv1420.set_if_band(cfg.get("admv1420_if_band", "1GHz_5GHz"))
                self.admv1420.set_if_mode(cfg.get("admv1420_if_mode", "if"))
                self.admv1420.set_lo_sideband(cfg["admv1420_lo_sideband"])
                self.admv1420.set_lo_x3_filter(cfg["admv1420_lo_x3_filter"])
            else:
                self.admv1420.set_if_mode("baseband")

        self._current_band = band_name

    # -- Gain control --------------------------------------------------------
    def set_direct_gain(self, dsa1="0dB", dsa2="0dB", dsa3="0dB",
                        dsa4="0dB", dsa5="0dB"):
        """Set individual DSA values via *direct* registers (tables off).

        All arguments are optional; only supplied DSAs are changed.
        """
        if self.admv1420 is None:
            return
        self.admv1420.set_rf_dsa1_gain(dsa1)
        self.admv1420.set_rf_dsa2_gain(dsa2)
        self.admv1420.set_rf_dsa3_gain(dsa3)
        self.admv1420.set_if_dsa4_gain(dsa4)
        self.admv1420.set_if_dsa5_gain(dsa5)

    def set_bypass_gain(self, dsa1="0dB", dsa2="0dB", dsa3="0dB",
                        dsa4="0dB", dsa5="0dB"):
        """Set individual DSA values via *bypass* registers (highest priority)."""
        if self.admv1420 is None:
            return
        self.admv1420.set_rf_bypass_dsa1(dsa1)
        self.admv1420.set_rf_bypass_dsa2(dsa2)
        self.admv1420.set_rf_bypass_dsa3(dsa3)
        self.admv1420.set_if_bypass_dsa4(dsa4)
        self.admv1420.set_if_bypass_dsa5(dsa5)

    def set_direct_gain_int(self, dsa1=0, dsa2=0, dsa3=0,
                            dsa4=0, dsa5=0):
        """Set individual DSA values via *direct* registers using integers.

        Convenience wrapper around :meth:`set_direct_gain` that accepts
        plain integers instead of strings.

        Parameters
        ----------
        dsa1 : int
            RF DSA1 attenuation (0-15, in dB).
        dsa2 : int
            RF DSA2 attenuation (0 or 6).
        dsa3 : int
            RF DSA3 attenuation (0-15, in dB).
        dsa4 : int
            IF DSA4 attenuation (0-15, in dB).
        dsa5 : int
            IF DSA5 attenuation (0-15, in dB).
        """
        self.set_direct_gain(
            _dsa_int_to_str(dsa1), _dsa_int_to_str(dsa2),
            _dsa_int_to_str(dsa3), _dsa_int_to_str(dsa4),
            _dsa_int_to_str(dsa5),
        )

    def set_bypass_gain_int(self, dsa1=0, dsa2=0, dsa3=0,
                            dsa4=0, dsa5=0):
        """Set individual DSA values via *bypass* registers using integers.

        Convenience wrapper around :meth:`set_bypass_gain` that accepts
        plain integers instead of strings.

        Parameters
        ----------
        dsa1 : int
            RF DSA1 attenuation (0-15, in dB).
        dsa2 : int
            RF DSA2 attenuation (0 or 6).
        dsa3 : int
            RF DSA3 attenuation (0-15, in dB).
        dsa4 : int
            IF DSA4 attenuation (0-15, in dB).
        dsa5 : int
            IF DSA5 attenuation (0-15, in dB).
        """
        self.set_bypass_gain(
            _dsa_int_to_str(dsa1), _dsa_int_to_str(dsa2),
            _dsa_int_to_str(dsa3), _dsa_int_to_str(dsa4),
            _dsa_int_to_str(dsa5),
        )

    def reset_gain(self):
        """Zero out all DSA bypass values."""
        self.set_bypass_gain("0dB", "0dB", "0dB", "0dB", "0dB")

    def configure_gain_int(self, mode="bypass",
                           rf_dsa1=0, rf_dsa2=0, rf_dsa3=0,
                           if_dsa4=0, if_dsa5=0,
                           rf_dsa1_offset=0, rf_dsa2_offset=0, rf_dsa3_offset=0,
                           if_dsa4_offset=0, if_dsa5_offset=0):
        """Configure the RX gain chain using integer DSA values.

        Convenience wrapper around :meth:`configure_gain` that accepts
        plain integers instead of gain strings.

        Parameters
        ----------
        mode : str
            Gain priority mode: ``"bypass"``, ``"table"``, or ``"direct"``.
        rf_dsa1 : int
            RF DSA1 attenuation (0-15, in dB).
        rf_dsa2 : int
            RF DSA2 attenuation (0 or 6).
        rf_dsa3 : int
            RF DSA3 attenuation (0-15, in dB).
        if_dsa4 : int
            IF DSA4 attenuation (0-15, in dB).
        if_dsa5 : int
            IF DSA5 attenuation (0-15, in dB).
        rf_dsa1_offset : int
            RF DSA1 offset (0-15).  Table mode only.
        rf_dsa2_offset : int
            RF DSA2 offset (0-3).  Table mode only.
        rf_dsa3_offset : int
            RF DSA3 offset (0-15).  Table mode only.
        if_dsa4_offset : int
            IF DSA4 offset (0-15).  Table mode only.
        if_dsa5_offset : int
            IF DSA5 offset (0-15).  Table mode only.
        """
        self.configure_gain(
            mode=mode,
            rf_dsa1=_dsa_int_to_str(rf_dsa1),
            rf_dsa2=_dsa_int_to_str(rf_dsa2),
            rf_dsa3=_dsa_int_to_str(rf_dsa3),
            if_dsa4=_dsa_int_to_str(if_dsa4),
            if_dsa5=_dsa_int_to_str(if_dsa5),
            rf_dsa1_offset=rf_dsa1_offset,
            rf_dsa2_offset=rf_dsa2_offset,
            rf_dsa3_offset=rf_dsa3_offset,
            if_dsa4_offset=if_dsa4_offset,
            if_dsa5_offset=if_dsa5_offset,
        )

    def configure_gain(self, mode="bypass",
                       rf_dsa1="0dB", rf_dsa2="0dB", rf_dsa3="0dB",
                       if_dsa4="0dB", if_dsa5="0dB",
                       rf_dsa1_offset=0, rf_dsa2_offset=0, rf_dsa3_offset=0,
                       if_dsa4_offset=0, if_dsa5_offset=0):
        """Configure the RX gain chain with mode selection and DSA values.

        The ADMV1420 uses a 3-level priority system:

        * **bypass** (highest) — writes ``bypass_dsa*_gain`` registers;
          ignores table and direct values.
        * **table** — enables the gain lookup table; the DSA offset
          parameters fine-tune the table output.
        * **direct** (lowest) — writes ``direct_dsa*_gain`` registers;
          active only when both table and bypass are disabled.

        Parameters
        ----------
        mode : str
            Gain priority mode: ``"bypass"``, ``"table"``, or ``"direct"``.
        rf_dsa1 : str
            RF DSA1 gain (0dB .. -15dB, 1 dB steps).  Used in bypass and
            direct modes.
        rf_dsa2 : str
            RF DSA2 gain (0dB or -6dB).  Used in bypass and direct modes.
        rf_dsa3 : str
            RF DSA3 gain (0dB .. -15dB, 1 dB steps).  Used in bypass and
            direct modes.
        if_dsa4 : str
            IF DSA4 gain (0dB .. -15dB, 1 dB steps).  Used in bypass and
            direct modes.
        if_dsa5 : str
            IF DSA5 gain (0dB .. -15dB, 1 dB steps).  Used in bypass and
            direct modes.
        rf_dsa1_offset : int
            RF DSA1 offset (0-15).  Only applied in table mode.
        rf_dsa2_offset : int
            RF DSA2 offset (0-3).  Only applied in table mode.
        rf_dsa3_offset : int
            RF DSA3 offset (0-15).  Only applied in table mode.
        if_dsa4_offset : int
            IF DSA4 offset (0-15).  Only applied in table mode.
        if_dsa5_offset : int
            IF DSA5 offset (0-15).  Only applied in table mode.
        """
        if self.admv1420 is None:
            return

        self.admv1420.configure_gain_mode(mode)

        if mode == "bypass":
            self.admv1420.set_rf_bypass_dsa1(rf_dsa1)
            self.admv1420.set_rf_bypass_dsa2(rf_dsa2)
            self.admv1420.set_rf_bypass_dsa3(rf_dsa3)
            self.admv1420.set_if_bypass_dsa4(if_dsa4)
            self.admv1420.set_if_bypass_dsa5(if_dsa5)
        elif mode == "direct":
            self.admv1420.set_rf_dsa1_gain(rf_dsa1)
            self.admv1420.set_rf_dsa2_gain(rf_dsa2)
            self.admv1420.set_rf_dsa3_gain(rf_dsa3)
            self.admv1420.set_if_dsa4_gain(if_dsa4)
            self.admv1420.set_if_dsa5_gain(if_dsa5)
        elif mode == "table":
            self.admv1420.set_rf_dsa1_offset(rf_dsa1_offset)
            self.admv1420.set_rf_dsa2_offset(rf_dsa2_offset)
            self.admv1420.set_rf_dsa3_offset(rf_dsa3_offset)
            self.admv1420.set_if_dsa4_offset(if_dsa4_offset)
            self.admv1420.set_if_dsa5_offset(if_dsa5_offset)

        self._info(
            f"RX{self.channel}: gain mode={mode} "
            f"RF(DSA1={rf_dsa1}, DSA2={rf_dsa2}, DSA3={rf_dsa3}) "
            f"IF(DSA4={if_dsa4}, DSA5={if_dsa5})"
        )

    # -- IMR calibration -----------------------------------------------------
    def set_imr(self, dsai="0dB", dsaq="0dB"):
        """Set the I/Q fine attenuators for image rejection."""
        if self.admv1420:
            self.admv1420.set_if_dsai_0p1db(dsai)
            self.admv1420.set_if_dsaq_0p1db(dsaq)

    # -- LO phase adjustment -------------------------------------------------
    def set_lo_phase(self, i_phase: int = 16, q_phase: int = 16):
        if self.admv1420:
            self.admv1420.set_lo_i_phase(i_phase)
            self.admv1420.set_lo_q_phase(q_phase)

    # -- LO sideband ---------------------------------------------------------
    def set_lo_sideband(self, sideband: str = "USB"):
        if self.admv1420:
            self.admv1420.set_lo_sideband(sideband)

    # -- LO x3 filter -------------------------------------------------------
    def set_lo_x3_filter(self, filt: str):
        if self.admv1420:
            self.admv1420.set_lo_x3_filter(filt)

    # -- Temperature sensor --------------------------------------------------
    def read_temperature(self):
        """Read the on-chip temperature sensor (ADMV1420). Returns deg C."""
        if self.admv1420 is None:
            return None
        try:
            raw = int(self.admv1420.read_temperature())
            return raw * 5 / 6 * (-1) + 177
        except Exception:
            return None

    # -- LUT programming -----------------------------------------------------

    def load_filter_lut(self, entries, table="A"):
        """Write filter LUT entries to the ADMV1420.

        Parameters
        ----------
        entries : list
            ``ADMV1420FilterEntry`` objects (or pre-formatted strings).
        table : str
            ``"A"`` or ``"B"``.
        """
        if self.admv1420 is None:
            return
        for entry in entries:
            s = entry.format() if hasattr(entry, "format") else str(entry)
            self.admv1420.write_filter_table_entry(s, table)
        self._info(f"RX{self.channel}: loaded {len(entries)} filter LUT "
                   f"entries to table {table}")

    def load_gain_lut(self, entries):
        """Write gain LUT entries to the ADMV1420.

        Parameters
        ----------
        entries : list
            ``ADMV1420GainEntry`` objects (or pre-formatted strings).
        """
        if self.admv1420 is None:
            return
        for entry in entries:
            s = entry.format() if hasattr(entry, "format") else str(entry)
            self.admv1420.write_gain_table_entry(s)
        self._info(f"RX{self.channel}: loaded {len(entries)} gain LUT entries")

    # -- LUT mode control ----------------------------------------------------

    def enable_filter_table(self, table="A"):
        """Switch the filter path to table-driven mode.

        Parameters
        ----------
        table : str
            ``"A"`` or ``"B"`` — selects which pre-loaded table is active.
        """
        if self.admv1420:
            self.admv1420.set_filter_table_sel(table)
            self.admv1420.set_filter_table_en(True)
            self.admv1420.set_filter_load_en(True)

        self._info(f"RX{self.channel}: filter table mode enabled "
                   f"(table {table})")

    def disable_filter_table(self):
        """Return the filter path to bypass / direct mode."""
        if self.admv1420:
            self.admv1420.set_filter_table_en(False)
            self.admv1420.set_filter_load_en(False)

        self._info(f"RX{self.channel}: filter table mode disabled")

    def enable_gain_table(self):
        """Switch gain control to table mode on the ADMV1420."""
        if self.admv1420:
            self.admv1420.configure_gain_mode("table")
            self.admv1420.set_gain_load_en(True)
        self._info(f"RX{self.channel}: gain table mode enabled")

    def disable_gain_table(self):
        """Return gain control to bypass mode."""
        if self.admv1420:
            self.admv1420.configure_gain_mode("bypass")
            self.admv1420.set_gain_load_en(False)
        self._info(f"RX{self.channel}: gain table mode disabled")

    def set_filter_lut_index(self, index: int):
        """Select a filter LUT entry via the ADDF GPIO address bus.

        Writes the 5-bit index to ``ADMV1420_ADDF_0..4`` then pulses
        the channel's ``ADMV1420_RX_LOAD_N`` GPIO to latch.
        """
        ch = self.channel
        for bit in range(5):
            self._gpio.write(f"ADMV1420_ADDF_{bit}", (index >> bit) & 1)
        self._gpio.write(f"ADMV1420_RX_LOAD_{ch}", 0)
        self._gpio.write(f"ADMV1420_RX_LOAD_{ch}", 1)
        self._gpio.write(f"ADMV1420_RX_LOAD_{ch}", 0)
        self._info(f"RX{ch}: filter LUT index → {index}")

    def set_gain_lut_index(self, index: int):
        """Select a gain LUT entry via the ADDG GPIO address bus.

        Writes the 5-bit index to ``ADMV1420_ADDG_0..4`` then pulses
        the channel's ``ADMV1420_RX_LOAD_N`` GPIO to latch.
        """
        ch = self.channel
        for bit in range(5):
            self._gpio.write(f"ADMV1420_ADDG_{bit}", (index >> bit) & 1)
        self._gpio.write(f"ADMV1420_RX_LOAD_{ch}", 0)
        self._gpio.write(f"ADMV1420_RX_LOAD_{ch}", 1)
        self._gpio.write(f"ADMV1420_RX_LOAD_{ch}", 0)
        self._info(f"RX{ch}: gain LUT index → {index}")

    # -- Raw register access -------------------------------------------------
    def reg_read(self, addr):
        if self.admv1420:
            return self.admv1420.reg_read(addr)
        return None

    def reg_write(self, addr, val):
        if self.admv1420:
            self.admv1420.reg_write(addr, val)

    def set_band(self):
        self.reg_write(0x000,	0x81)
        time.sleep(1e-3)
        self.reg_write(0x000,	0x18)
        self.reg_write(0x004,	0x68)
        self.reg_write(0x005,	0x00)
        self.reg_write(0x00A,	0x00)
        self.reg_write(0x013,	0x01)
        self.reg_write(0x040,	0x00)
        self.reg_write(0x041,	0x00)
        self.reg_write(0x043,	0x00)
        self.reg_write(0x051,	0x40)
        self.reg_write(0x052,	0x00)
        self.reg_write(0x053,	0xEF)
        self.reg_write(0x054,	0x01)
        self.reg_write(0x055,	0x00)
        self.reg_write(0x05F,	0x00)
        self.reg_write(0x0A0,	0x00)
        self.reg_write(0x0A1,	0x00)
        self.reg_write(0x100,	0x00)
        self.reg_write(0x102,	0x00)
        self.reg_write(0x105,	0x03)
        self.reg_write(0x108,	0x00)
        self.reg_write(0x159,	0x04)
        self.reg_write(0x176,	0x44)
        self.reg_write(0x177,	0x00)
        self.reg_write(0x178,	0x07)
        self.reg_write(0x17D,	0x01)
        self.reg_write(0x17E,	0x50)
        self.reg_write(0x180,	0x02)
        self.reg_write(0x184,	0x01)
        self.reg_write(0x18A,	0x01)
        self.reg_write(0x18C,	0x00)
        self.reg_write(0x18D,	0x00)
        self.reg_write(0x18E,	0x00)
        self.reg_write(0x18F,	0x00)
        self.reg_write(0x192,	0x04)
        self.reg_write(0x193,	0x04)
        self.reg_write(0x200,	0x01)
        self.reg_write(0x202,	0x00)
        self.reg_write(0x203,	0x00)
        self.reg_write(0x204,	0x01)
        self.reg_write(0x206,	0x1F)
        self.reg_write(0x207,	0x00)
        self.reg_write(0x208,	0x00)
        self.reg_write(0x209,	0x00)
        self.reg_write(0x220,	0x00)
        self.reg_write(0x221,	0x00)
        self.reg_write(0x222,	0x00)
        self.reg_write(0x223,	0x00)
        self.reg_write(0x224,	0x00)
        self.reg_write(0x225,	0x00)
        self.reg_write(0x226,	0x00)
        self.reg_write(0x227,	0x00)
        self.reg_write(0x228,	0x00)
        self.reg_write(0x240,	0x00)
        self.reg_write(0x270,	0x00)
        self.reg_write(0x271,	0x00)
        self.reg_write(0x272,	0x00)
        self.reg_write(0x281,	0x00)
        self.reg_write(0x282,	0x00)
        self.reg_write(0x283,	0x01)
        self.reg_write(0x284,	0x00)
        self.reg_write(0x285,	0x01)
        self.reg_write(0x286,	0x00)
        self.reg_write(0x287,	0x01)
        self.reg_write(0x289,	0x42)
        self.reg_write(0x28A,	0x01)
        self.reg_write(0x28B,	0x00)
        self.reg_write(0x28C,	0x00)
        self.reg_write(0x28D,	0x00)
        self.reg_write(0x298,	0x00)
        self.reg_write(0x29B,	0x00)
        self.reg_write(0x2A0,	0x10)
        self.reg_write(0x2A1,	0xBF)
        self.reg_write(0x2A2,	0x10)
        self.reg_write(0x2A3,	0x00)
        self.reg_write(0x2A4,	0x00)
        self.reg_write(0x2A5,	0x00)
        self.reg_write(0x2B0,	0x00)
        self.reg_write(0x600,	0x00)
        self.reg_write(0x601,	0x00)
        self.reg_write(0x602,	0x00)
        self.reg_write(0x603,	0x00)
        self.reg_write(0x780,	0x00)
        self.reg_write(0x781,	0x00)
        self.reg_write(0x800,	0xE0)
        self.reg_write(0x801,	0x00)
        self.reg_write(0x802,	0x00)
        self.reg_write(0x803,	0x00)
        self.reg_write(0x804,	0x00)
        self.reg_write(0x805,	0x00)
        self.reg_write(0x806,	0x00)
        self.reg_write(0x807,	0x00)
        self.reg_write(0x808,	0x00)
        self.reg_write(0x860,	0x03)


# ===================================================================
# TxChain
# ===================================================================

class TxChain:
    """One complete TX signal chain (channel 1-4).

    Composed of:
      * ADMV1320  (up-converter)

    The LO (ADF4382) is managed separately via :class:`LoChain`
    and the tunable filter (ADMV8913) is managed via :class:`FilterChain`.
    Both should be configured before calling :meth:`set_band` on mixer bands.
    """

    BAND_CONFIGS = TX_BAND_CONFIGS

    def __init__(self, channel: int, ctx, gpio: GpioHelper, log=None):
        self.channel = channel
        self._ctx = ctx
        self._gpio = gpio
        self._log = log

        dev = _find_iio_device(ctx, f"admv1320_tx_{channel}")
        self.admv1320 = ADMV1320(dev) if dev else None

        self._current_band = None

    def _info(self, msg):
        if self._log:
            self._log.Info(msg)

    def _warn(self, msg):
        if self._log:
            self._log.Warning(msg)

    # -- Initialization ------------------------------------------------------
    def initialize(self):
        """Bring-up all TX devices: soft-reset, 4-wire SPI, verify PIDs."""
        results = []
        ch = self.channel

        # -- ADMV1320 --------------------------------------------------------
        if self.admv1320:
            try:
                d = self.admv1320
                d.reg_write(0x0, 0x81)
                d.reg_write(0x0, 0x18)
                pid = d.reg_read(0x4)
                ok = pid == 0x1320
                results.append({"device": f"admv1320_tx_{ch}", "pid": pid, "pass": ok})
                self._info(f"admv1320_tx_{ch} PID=0x{pid:04x} {'PASS' if ok else 'FAIL'}")

                d.set_filter_table_en(False)
                d.set_gain_table_en(False)
                d.set_bypass_gain_table_en(True)
                d.set_rf_dsa1_gain("0dB")
                d.set_rf_dsa2_gain("0dB")
                d.set_rf_bypass_dsa1("0dB")
                d.set_rf_bypass_dsa2("0dB")
                d.set_rf_band("0_2GHz")
                d.set_if_mode("baseband")
            except Exception as e:
                self._warn(f"admv1320_tx_{ch} init error: {e}")
                results.append({"device": f"admv1320_tx_{ch}", "pid": None, "pass": False})
        else:
            results.append({"device": f"admv1320_tx_{ch}", "pid": None, "pass": False})

        return results
    # -- Band configuration --------------------------------------------------
    @classmethod
    def list_bands(cls):
        return list(cls.BAND_CONFIGS.keys())

    def set_band(self, band_name: str):
        """Configure the entire TX chain for a system-level band."""
        cfg = self.BAND_CONFIGS.get(band_name)
        if cfg is None:
            raise ValueError(
                f"Unknown TX band '{band_name}'. "
                f"Valid: {', '.join(self.list_bands())}"
            )

        ch = self.channel
        self._info(f"TX{ch}: setting band → {band_name}")

        # ADMV1320
        if self.admv1320:
            self.admv1320.set_rf_band(cfg["admv1320_rf_band"])
            #self.admv1320.set_if_band(cfg.get("admv1320_if_band", "3GHz_12GHz"))
            if cfg["use_mixer"]:
                self.admv1320.set_mixer_bypass_en(cfg.get("admv1320_mixer_bypass_en", False))
                self.admv1320.set_if_band(cfg.get("admv1320_if_band", "3GHz_12GHz"))
                self.admv1320.set_if_mode(cfg.get("admv1320_if_mode", "if"))
                self.admv1320.set_lo_sideband(cfg["admv1320_lo_sideband"])
                self.admv1320.set_lo_x3_filter(cfg["admv1320_lo_x3_filter"])
            else:
                self.admv1320.set_if_mode("baseband")
                self.admv1320.set_mixer_bypass_en(cfg.get("admv1320_mixer_bypass_en", True))

        self._current_band = band_name

    # -- Gain ----------------------------------------------------------------
    def set_direct_gain(self, dsa1="0dB", dsa2="0dB"):
        """Set ADMV1320 DSA values via direct registers."""
        if self.admv1320:
            self.admv1320.set_rf_dsa1_gain(dsa1)
            self.admv1320.set_rf_dsa2_gain(dsa2)

    def set_bypass_gain(self, dsa1="0dB", dsa2="0dB"):
        """Set ADMV1320 DSA values via bypass registers."""
        if self.admv1320:
            self.admv1320.set_rf_bypass_dsa1(dsa1)
            self.admv1320.set_rf_bypass_dsa2(dsa2)

    def set_direct_gain_int(self, dsa1=0, dsa2=0):
        """Set ADMV1320 DSA values via direct registers using integers.

        Convenience wrapper around :meth:`set_direct_gain` that accepts
        plain integers instead of strings.

        Parameters
        ----------
        dsa1 : int
            RF DSA1 attenuation (0-15, in dB).
        dsa2 : int
            RF DSA2 attenuation (0-15, in dB).
        """
        self.set_direct_gain(_dsa_int_to_str(dsa1), _dsa_int_to_str(dsa2))

    def set_bypass_gain_int(self, dsa1=0, dsa2=0):
        """Set ADMV1320 DSA values via bypass registers using integers.

        Convenience wrapper around :meth:`set_bypass_gain` that accepts
        plain integers instead of strings.

        Parameters
        ----------
        dsa1 : int
            RF DSA1 attenuation (0-15, in dB).
        dsa2 : int
            RF DSA2 attenuation (0-15, in dB).
        """
        self.set_bypass_gain(_dsa_int_to_str(dsa1), _dsa_int_to_str(dsa2))

    def reset_gain(self):
        self.set_bypass_gain("0dB", "0dB")

    def configure_gain_int(self, mode="bypass",
                           rf_dsa1=0, rf_dsa2=0,
                           rf_dsa1_offset=0, rf_dsa2_offset=0):
        """Configure the TX gain chain using integer DSA values.

        Convenience wrapper around :meth:`configure_gain` that accepts
        plain integers instead of gain strings.

        Parameters
        ----------
        mode : str
            Gain priority mode: ``"bypass"``, ``"table"``, or ``"direct"``.
        rf_dsa1 : int
            RF DSA1 attenuation (0-15, in dB).
        rf_dsa2 : int
            RF DSA2 attenuation (0-15, in dB).
        rf_dsa1_offset : int
            RF DSA1 offset (0-15).  Table mode only.
        rf_dsa2_offset : int
            RF DSA2 offset (0-15).  Table mode only.
        """
        self.configure_gain(
            mode=mode,
            rf_dsa1=_dsa_int_to_str(rf_dsa1),
            rf_dsa2=_dsa_int_to_str(rf_dsa2),
            rf_dsa1_offset=rf_dsa1_offset,
            rf_dsa2_offset=rf_dsa2_offset,
        )

    def configure_gain(self, mode="bypass",
                       rf_dsa1="0dB", rf_dsa2="0dB",
                       rf_dsa1_offset=0, rf_dsa2_offset=0):
        """Configure the TX gain chain with mode selection and DSA values.

        The ADMV1320 uses a 3-level priority system:

        * **bypass** (highest) — writes ``bypass_dsa*_gain`` registers.
        * **table** — enables the gain lookup table; offsets fine-tune
          the table output.
        * **direct** (lowest) — writes ``direct_dsa*_gain`` registers.

        Parameters
        ----------
        mode : str
            Gain priority mode: ``"bypass"``, ``"table"``, or ``"direct"``.
        rf_dsa1 : str
            RF DSA1 gain (0dB .. -15dB, 1 dB steps).  Used in bypass and
            direct modes.
        rf_dsa2 : str
            RF DSA2 gain (0dB .. -15dB, 1 dB steps).  Used in bypass and
            direct modes.
        rf_dsa1_offset : int
            RF DSA1 offset (0-15).  Only applied in table mode.
        rf_dsa2_offset : int
            RF DSA2 offset (0-15).  Only applied in table mode.
        """
        if self.admv1320 is None:
            return

        self.admv1320.configure_gain_mode(mode)

        if mode == "bypass":
            self.admv1320.set_rf_bypass_dsa1(rf_dsa1)
            self.admv1320.set_rf_bypass_dsa2(rf_dsa2)
        elif mode == "direct":
            self.admv1320.set_rf_dsa1_gain(rf_dsa1)
            self.admv1320.set_rf_dsa2_gain(rf_dsa2)
        elif mode == "table":
            self.admv1320.set_rf_dsa1_offset(rf_dsa1_offset)
            self.admv1320.set_rf_dsa2_offset(rf_dsa2_offset)

        self._info(
            f"TX{self.channel}: gain mode={mode} "
            f"RF(DSA1={rf_dsa1}, DSA2={rf_dsa2})"
        )

    # -- IMR calibration -----------------------------------------------------
    def set_imr(self, dsai="0dB", dsaq="0dB"):
        if self.admv1320:
            self.admv1320.set_if_dsai_0p1db(dsai)
            self.admv1320.set_if_dsaq_0p1db(dsaq)

    # -- LO phase / sideband / filter ----------------------------------------
    def set_lo_phase(self, i_phase: int = 16, q_phase: int = 16):
        if self.admv1320:
            self.admv1320.set_lo_i_phase(i_phase)
            self.admv1320.set_lo_q_phase(q_phase)

    def set_lo_sideband(self, sideband: str = "LSB"):
        if self.admv1320:
            self.admv1320.set_lo_sideband(sideband)

    def set_lo_x3_filter(self, filt: str):
        if self.admv1320:
            self.admv1320.set_lo_x3_filter(filt)

    def set_lo_lon_offset(self, i: int = 32, q: int = 32):
        """Set LON DC offset for LO leakage calibration."""
        if self.admv1320:
            self.admv1320.set_lo_lon_offset_i(i)
            self.admv1320.set_lo_lon_offset_q(q)

    def set_if_vcm(self, val: int = 64):
        """Set IF common-mode voltage (0-127, LSB = 50 mV)."""
        if self.admv1320:
            self.admv1320.set_if_vcm(val)

    # -- Temperature sensor --------------------------------------------------
    def read_temperature(self):
        """ADMV1320 on-chip temperature sensor (raw ADC code)."""
        if self.admv1320 is None:
            return None
        try:
            raw = self.admv1320.reg_read(0x30D)
            return raw
        except Exception:
            return None

    # -- 1320 LO filter (direct register) ------------------------------------
    def set_1320_lo_filter_code(self, code: int):
        """Adjust the internal ADMV1320 LO filter tuning code (0-15)."""
        if self.admv1320:
            current = self.admv1320.reg_read(0x800)
            self.admv1320.reg_write(0x800, (current & 0xF0) | (code & 0x0F))

    # -- LUT programming -----------------------------------------------------

    def load_filter_lut(self, entries, table="A"):
        """Write filter LUT entries to the ADMV1320.

        Parameters
        ----------
        entries : list
            ``ADMV1320FilterEntry`` objects (or pre-formatted strings).
        table : str
            ``"A"`` or ``"B"``.
        """
        if self.admv1320 is None:
            return
        for entry in entries:
            s = entry.format() if hasattr(entry, "format") else str(entry)
            self.admv1320.write_filter_table_entry(s, table)
        self._info(f"TX{self.channel}: loaded {len(entries)} filter LUT "
                   f"entries to table {table}")

    def load_gain_lut(self, entries):
        """Write gain LUT entries to the ADMV1320.

        Parameters
        ----------
        entries : list
            ``ADMV1320GainEntry`` objects (or pre-formatted strings).
        """
        if self.admv1320 is None:
            return
        for entry in entries:
            s = entry.format() if hasattr(entry, "format") else str(entry)
            self.admv1320.write_gain_table_entry(s)
        self._info(f"TX{self.channel}: loaded {len(entries)} gain LUT entries")

    # -- LUT mode control ----------------------------------------------------

    def enable_filter_table(self, table="A"):
        """Switch the filter path to table-driven mode.

        Parameters
        ----------
        table : str
            ``"A"`` or ``"B"`` — selects which pre-loaded table is active.
        """
        if self.admv1320:
            self.admv1320.set_filter_table_sel(table)
            self.admv1320.set_filter_table_en(True)
            self.admv1320.set_filter_load_en(True)

        self._info(f"TX{self.channel}: filter table mode enabled "
                   f"(table {table})")

    def disable_filter_table(self):
        """Return the filter path to bypass / direct mode."""
        if self.admv1320:
            self.admv1320.set_filter_table_en(False)
            self.admv1320.set_filter_load_en(False)

        self._info(f"TX{self.channel}: filter table mode disabled")

    def enable_gain_table(self):
        """Switch gain control to table mode on the ADMV1320."""
        if self.admv1320:
            self.admv1320.configure_gain_mode("table")
            self.admv1320.set_gain_load_en(True)
        self._info(f"TX{self.channel}: gain table mode enabled")

    def disable_gain_table(self):
        """Return gain control to bypass mode."""
        if self.admv1320:
            self.admv1320.configure_gain_mode("bypass")
            self.admv1320.set_gain_load_en(False)
        self._info(f"TX{self.channel}: gain table mode disabled")

    def set_filter_lut_index(self, index: int):
        """Select a filter LUT entry via the ADDF GPIO address bus.

        Writes the 5-bit index to ``ADMV1320_ADDF_0..4`` then pulses
        the channel's ``ADMV1320_TX_LOAD_N`` GPIO to latch.
        """
        ch = self.channel
        for bit in range(5):
            self._gpio.write(f"ADMV1320_ADDF_{bit}", (index >> bit) & 1)
        self._gpio.write(f"ADMV1320_TX_LOAD_{ch}", 0)
        self._gpio.write(f"ADMV1320_TX_LOAD_{ch}", 1)
        self._gpio.write(f"ADMV1320_TX_LOAD_{ch}", 0)
        self._info(f"TX{ch}: filter LUT index → {index}")

    def set_gain_lut_index(self, index: int):
        """Select a gain LUT entry via the ADD GPIO address bus.

        Writes the 5-bit index to ``ADMV1320_ADD_0..4`` then pulses
        the channel's ``ADMV1320_TX_LOAD_N`` GPIO to latch.
        """
        ch = self.channel
        for bit in range(5):
            self._gpio.write(f"ADMV1320_ADD_{bit}", (index >> bit) & 1)
        self._gpio.write(f"ADMV1320_TX_LOAD_{ch}", 0)
        self._gpio.write(f"ADMV1320_TX_LOAD_{ch}", 1)
        self._gpio.write(f"ADMV1320_TX_LOAD_{ch}", 0)
        self._info(f"TX{ch}: gain LUT index → {index}")

    # -- Raw register access -------------------------------------------------
    def reg_read(self, addr):
        if self.admv1320:
            return self.admv1320.reg_read(addr)
        return None

    def reg_write(self, addr, val):
        if self.admv1320:
            self.admv1320.reg_write(addr, val)

    def set_band1(self):
        self.reg_write(0x000,	0x81)
        time.sleep(1e-3)
        self.reg_write(0x000,	0x18)
        self.reg_write(0x004,	0x67)
        self.reg_write(0x005,	0x00)
        self.reg_write(0x00A,	0x00)
        self.reg_write(0x013,	0x01)
        self.reg_write(0x138,	0x04)
        self.reg_write(0x13B,	0x00)
        self.reg_write(0x13E,	0x02)
        self.reg_write(0x200,	0x01)
        self.reg_write(0x202,	0x00)
        self.reg_write(0x203,	0x00)
        self.reg_write(0x204,	0x01)
        self.reg_write(0x207,	0x00)
        self.reg_write(0x208,	0x00)
        self.reg_write(0x209,	0x00)
        self.reg_write(0x210,	0x00)
        self.reg_write(0x220,	0x60)
        self.reg_write(0x221,	0x00)
        self.reg_write(0x222,	0x00)
        self.reg_write(0x223,	0x00)
        self.reg_write(0x224,	0x00)
        self.reg_write(0x225,	0x00)
        self.reg_write(0x226,	0x00)
        self.reg_write(0x227,	0x88)
        self.reg_write(0x228,	0x00)
        self.reg_write(0x240,	0x00)
        self.reg_write(0x281,	0x00)
        self.reg_write(0x282,	0x00)
        self.reg_write(0x283,	0x01)
        self.reg_write(0x284,	0x00)
        self.reg_write(0x285,	0x00)
        self.reg_write(0x286,	0x00)
        self.reg_write(0x287,	0x01)
        self.reg_write(0x28A,	0x01)
        self.reg_write(0x28B,	0x05)
        self.reg_write(0x2A0,	0x1F)
        self.reg_write(0x2A1,	0xBF)
        self.reg_write(0x2A3,	0x00)
        self.reg_write(0x2A4,	0x00)
        self.reg_write(0x2A7,	0x00)
        self.reg_write(0x300,	0x82)
        self.reg_write(0x302,	0x02)
        self.reg_write(0x304,	0x88)
        self.reg_write(0x305,	0x00)
        self.reg_write(0x306,	0x00)
        self.reg_write(0x30D,	0xD1)
        self.reg_write(0x600,	0x00)
        self.reg_write(0x601,	0x00)
        self.reg_write(0x60A,	0x02)
        self.reg_write(0x700,	0x00)
        self.reg_write(0x701,	0x00)
        self.reg_write(0x702,	0x00)
        self.reg_write(0x703,	0x08)
        self.reg_write(0x780,	0x00)
        self.reg_write(0x781,	0x00)
        self.reg_write(0x800,	0x60)
        self.reg_write(0x801,	0x00)
        self.reg_write(0x802,	0x00)
        self.reg_write(0x803,	0x00)
        self.reg_write(0x804,	0x00)
        self.reg_write(0x805,	0x00)
        self.reg_write(0x806,	0x00)
        self.reg_write(0x807,	0x00)
        self.reg_write(0x808,	0x00)
        self.reg_write(0x860,	0x01)

    def set_band2(self):
        self.reg_write(0x000,	0x18)
        self.reg_write(0x004,	0x67)
        self.reg_write(0x005,	0x00)
        self.reg_write(0x00A,	0x00)
        self.reg_write(0x013,	0x01)
        self.reg_write(0x138,	0x04)
        self.reg_write(0x13B,	0x00)
        self.reg_write(0x13E,	0x02)
        self.reg_write(0x200,	0x01)
        self.reg_write(0x202,	0x00)
        self.reg_write(0x203,	0x00)
        self.reg_write(0x204,	0x01)
        self.reg_write(0x207,	0x00)
        self.reg_write(0x208,	0x00)
        self.reg_write(0x209,	0x00)
        self.reg_write(0x210,	0x00)
        self.reg_write(0x220,	0x60)
        self.reg_write(0x221,	0x00)
        self.reg_write(0x222,	0x00)
        self.reg_write(0x223,	0x00)
        self.reg_write(0x224,	0x00)
        self.reg_write(0x225,	0x00)
        self.reg_write(0x226,	0x00)
        self.reg_write(0x227,	0x88)
        self.reg_write(0x228,	0x00)
        self.reg_write(0x240,	0x00)
        self.reg_write(0x281,	0x00)
        self.reg_write(0x282,	0x00)
        self.reg_write(0x283,	0x01)
        self.reg_write(0x284,	0x00)
        self.reg_write(0x285,	0x00)
        self.reg_write(0x286,	0x00)
        self.reg_write(0x287,	0x01)
        self.reg_write(0x28A,	0x01)
        self.reg_write(0x28B,	0x05)
        self.reg_write(0x2A0,	0x1B)
        self.reg_write(0x2A1,	0xBF)
        self.reg_write(0x2A3,	0x00)
        self.reg_write(0x2A4,	0x00)
        self.reg_write(0x2A7,	0x00)
        self.reg_write(0x300,	0x82)
        self.reg_write(0x302,	0x02)
        self.reg_write(0x304,	0x88)
        self.reg_write(0x305,	0x00)
        self.reg_write(0x306,	0x00)
        self.reg_write(0x30D,	0xD1)
        self.reg_write(0x600,	0x00)
        self.reg_write(0x601,	0x00)
        self.reg_write(0x60A,	0x02)
        self.reg_write(0x700,	0x00)
        self.reg_write(0x701,	0x00)
        self.reg_write(0x702,	0x00)
        self.reg_write(0x703,	0x08)
        self.reg_write(0x780,	0x00)
        self.reg_write(0x781,	0x00)
        self.reg_write(0x800,	0x60)
        self.reg_write(0x801,	0x00)
        self.reg_write(0x802,	0x00)
        self.reg_write(0x803,	0x00)
        self.reg_write(0x804,	0x00)
        self.reg_write(0x805,	0x00)
        self.reg_write(0x806,	0x00)
        self.reg_write(0x807,	0x00)
        self.reg_write(0x808,	0x00)
        self.reg_write(0x860,	0x01)
