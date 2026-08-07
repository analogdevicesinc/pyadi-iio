# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from .sshfs import sshfs


class adxcvr:
    """GTY/GTH Transceiver PRBS and DRP control via axi_adxcvr.

    Wraps the sysfs interface of the ADI axi_adxcvr Linux driver
    (drivers/iio/jesd204/axi_adxcvr.c) to enable PRBS pattern generation
    and checking, per-lane error count readback, and raw DRP register access
    over SSH.

    The washington (apollo_som_vu11p) design exposes four adxcvr instances
    for the JESD data lanes:
        axi_apollo_rx_xcvr   (A-side RX, lanes 0-11)
        axi_apollo_tx_xcvr   (A-side TX, lanes 0-11)
        axi_apollo_rx_b_xcvr (B-side RX, lanes 0-11)
        axi_apollo_tx_b_xcvr (B-side TX, lanes 0-11)
    """

    _SYSFS_ROOT = "/sys/bus/platform/devices/"

    # PRBS polynomial orders (GTH4/GTY4 support all; GTX2 excludes PRBS_9)
    PRBS_OFF = 0
    PRBS_7 = 7
    PRBS_9 = 9
    PRBS_15 = 15
    PRBS_23 = 23
    PRBS_31 = 31

    # DRP port address helpers
    DRP_PORT_COMMON = 0x000
    DRP_PORT_CHANNEL_BASE = 0x100  # channel n is DRP_PORT_CHANNEL_BASE + n

    # GT type codes from ADXCVR_REG_SYNTH bits [19:16]
    # For IP version <= 0x10 these are legacy codes; for version > 0x10 they are
    # the raw xilinx_xcvr_type enum values (from xilinx_transceiver.h):
    #   GTX2=2, GTH3=5, GTH4=8, GTY4=9
    # Legacy codes (IP version <= 0x10): GTX2=1, GTH3=2, GTH4=3, GTY4=4
    GT_TYPE_GTX2 = 2
    GT_TYPE_GTH3 = 5
    GT_TYPE_GTH4 = 8
    GT_TYPE_GTY4 = 9
    _GT_TYPE_NAMES = {2: "GTX2", 5: "GTH3", 8: "GTH4", 9: "GTY4"}
    # Legacy type mapping for IP version <= 0x10
    _GT_LEGACY_MAP = {1: 2, 2: 5, 3: 8, 4: 9}

    # Per-GT DRP addresses for PRBS error count (from xilinx_transceiver.h)
    # GTX2: 16-bit at 0x15C
    # GTH3: 32-bit at 0x15E/0x15F
    # GTH4/GTY4: 32-bit at 0x25E/0x25F
    _PRBS_ERR_CNT_ADDR = {
        2: (0x15C, False),  # GTX2: (base_addr, has_high_word)
        5: (0x15E, True),   # GTH3
        8: (0x25E, True),   # GTH4
        9: (0x25E, True),   # GTY4
    }

    _ADXCVR_REG_SYNTH = 0x24

    def __init__(self, address, device_name, username="root", password="analog"):
        if "ip:" in address:
            address = address[3:]
        self.address = address
        self.username = username
        self.password = password
        self.fs = sshfs(address, username, password)
        self._path = self._find_device(device_name)

    def _find_device(self, device_name):
        # Match on the device name suffix (after the address prefix "XXXXXXXX.")
        # to avoid "axi-adxcvr-rx" matching "axi-adxcvr-rx-b".
        for entry in self.fs.listdir(self._SYSFS_ROOT):
            suffix = entry.split(".", 1)[-1] if "." in entry else entry
            if suffix == device_name:
                return self._SYSFS_ROOT + entry + "/"
        raise RuntimeError(
            f"adxcvr device '{device_name}' not found in {self._SYSFS_ROOT}"
        )

    def _read(self, attr):
        return self.fs.gettext(self._path + attr)

    def _write(self, attr, value):
        self.fs._run(f"echo '{value}' > {self._path}{attr}")

    @property
    def prbs_select(self):
        """Active PRBS polynomial order (0=off, 7, 9, 15, 23, 31)."""
        return int(self._read("prbs_select"))

    @prbs_select.setter
    def prbs_select(self, polynomial):
        self._write("prbs_select", polynomial)

    @property
    def prbs_status(self):
        """RX only: 'valid', 'error', or 'unlocked'."""
        return self._read("prbs_status").strip()

    @property
    def prbs_error_counters(self):
        """RX only: per-lane PRBS error counts as a list of ints."""
        raw = self._read("prbs_error_counters").strip()
        if not raw:
            return []
        return [int(x) for x in raw.split()]

    def reset_prbs_counters(self):
        """RX only: clear all per-lane PRBS error counters."""
        self._write("prbs_error_counters", 1)

    def inject_prbs_error(self):
        """TX only: force a single PRBS error burst on all TX lanes."""
        self._write("prbs_error_inject", 1)

    @property
    def gt_type(self):
        """GT primitive type as an int (GTX2=2, GTH3=5, GTH4=8, GTY4=9)."""
        ver   = self.axi_read(0x00)
        synth = self.axi_read(self._ADXCVR_REG_SYNTH)
        raw   = (synth >> 16) & 0xF
        if ((ver >> 16) & 0xFF) <= 0x10:
            return self._GT_LEGACY_MAP.get(raw, raw)
        return raw

    @property
    def gt_type_name(self):
        """GT primitive type as a string, e.g. 'GTY4'."""
        return self._GT_TYPE_NAMES.get(self.gt_type, f"UNKNOWN({self.gt_type})")

    @property
    def num_lanes(self):
        """Number of lanes in this adxcvr instance (from SYNTH register)."""
        synth = self.axi_read(self._ADXCVR_REG_SYNTH)
        return synth & 0xFF

    def prbs_error_counts_drp(self):
        """Read per-lane PRBS error counts directly from GTY/GTH DRP registers.

        Reads the same hardware counters that the kernel driver serves via
        prbs_error_counters sysfs, but bypasses the driver — useful when you
        want raw DRP access or need to confirm the kernel readback.

        Returns a list of ints, one per lane.  Counter is 16-bit on GTX2,
        32-bit on GTH3/GTH4/GTY4.  Saturates at max value; reset by writing
        to prbs_error_counters sysfs (which calls the driver reset path).
        """
        gt = self.gt_type
        addr, has_high = self._PRBS_ERR_CNT_ADDR.get(gt, (None, None))
        if addr is None:
            raise RuntimeError(f"Unknown GT type {gt}, cannot read DRP error counters")

        counts = []
        for lane in range(self.num_lanes):
            port = self.DRP_PORT_CHANNEL_BASE + lane
            lo = self.drp_read(port, addr)
            hi = self.drp_read(port, addr + 1) if has_high else 0
            counts.append((hi << 16) | lo)
        return counts

    def drp_read(self, port, addr):
        """Read a GTY DRP register. Returns 16-bit int."""
        self._write("reg_access", f"drp {port} {addr}")
        return int(self._read("reg_access"), 16)

    def drp_write(self, port, addr, data):
        """Write a GTY DRP register."""
        self._write("reg_access", f"drp {port} {addr} {data}")

    def axi_read(self, addr):
        """Read an axi_adxcvr AXI-Lite register. Returns int."""
        self._write("reg_access", f"axi {addr}")
        return int(self._read("reg_access"), 16)

    def axi_write(self, addr, data):
        """Write an axi_adxcvr AXI-Lite register."""
        self._write("reg_access", f"axi {addr} {data}")
