# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from .sshfs import sshfs


class apollo_serdes:
    """Apollo digitizer SerDes PRBS control via ad9088/ad9084 IIO debugfs.

    The ad9088 kernel driver (drivers/iio/adc/apollo/ad9088.c) exposes three
    debugfs files under /sys/kernel/debug/iio/iio:deviceN/ that wrap the
    Apollo C API for JRx (receiver) and JTx (transmitter) PRBS:

        bist_prbs_select_jrx   -- enable JRx PRBS checker (0=off, 7/9/15/31)
        bist_prbs_select_jtx   -- enable JTx PRBS generator (0=off, 7/9/15/31)
        bist_prbs_error_counters_jrx -- read per-lane error counts

    On Washington (apollo_som_vu11p) the relevant IIO device is the one whose
    name contains 'ad9084-rx-hpc' (typically iio:device7).  That single device
    controls all 24 JESD lanes across both A-side and B-side Apollo channels.

    Usage:
        apollo = apollo_serdes("ip:10.48.65.110")
        apollo.prbs_select_jrx = 7   # PRBS7 checker on all JRx lanes
        apollo.prbs_select_jtx = 7   # PRBS7 generator on all JTx lanes
        print(apollo.prbs_error_counters_jrx)
        apollo.prbs_select_jrx = 0   # restore
        apollo.prbs_select_jtx = 0
    """

    _DEBUGFS_IIO = "/sys/kernel/debug/iio/"
    _DEVICE_SUBSTR = "ad9084-rx-hpc"

    PRBS_OFF = 0
    PRBS_7 = 7
    PRBS_9 = 9
    PRBS_15 = 15
    PRBS_31 = 31

    def __init__(self, address, device_name=None, username="root", password="analog"):
        if address.startswith("ip:"):
            address = address[3:]
        self.address = address
        self.fs = sshfs(address, username, password)
        substr = device_name if device_name is not None else self._DEVICE_SUBSTR
        self._dbgfs = self._find_debugfs(substr)

    def _find_debugfs(self, device_substr):
        iio_dirs = self.fs.listdir(self._DEBUGFS_IIO)
        for iio_dir in iio_dirs:
            sysfs_name_path = f"/sys/bus/iio/devices/{iio_dir}/name"
            name = self.fs.gettext(sysfs_name_path).strip()
            if device_substr in name:
                return self._DEBUGFS_IIO + iio_dir + "/"
        raise RuntimeError(
            f"apollo_serdes: no IIO device containing '{device_substr}' found in {self._DEBUGFS_IIO}"
        )

    def _read(self, attr):
        return self.fs.gettext(self._dbgfs + attr)

    def _write(self, attr, value):
        self.fs._run(f"echo '{value}' > {self._dbgfs}{attr}")

    @property
    def prbs_select_jrx(self):
        """JRx PRBS checker polynomial (0=off, 7, 9, 15, 31).

        Writes 7/9/15/31 to enable the checker and clear error counters.
        Writes 0 to disable and return to normal JESD operation.
        """
        return int(self._read("bist_prbs_select_jrx").strip() or "0")

    @prbs_select_jrx.setter
    def prbs_select_jrx(self, polynomial):
        self._write("bist_prbs_select_jrx", polynomial)

    @property
    def prbs_select_jtx(self):
        """JTx PRBS generator polynomial (0=off, 7, 9, 15, 31)."""
        return int(self._read("bist_prbs_select_jtx").strip() or "0")

    @prbs_select_jtx.setter
    def prbs_select_jtx(self, polynomial):
        self._write("bist_prbs_select_jtx", polynomial)

    @property
    def prbs_error_counters_jrx(self):
        """Per-lane JRx PRBS error counts.

        Returns a list of dicts, one per active lane:
            [{'side': 'A', 'lane': 4, 'err_count': 0, 'err_sticky': 0}, ...]

        The kernel formats each line as:
            <A|B>: lane-<n> <err_count>/<err_sticky>
        """
        raw = self._read("bist_prbs_error_counters_jrx").strip()
        if not raw:
            return []
        results = []
        for line in raw.splitlines():
            # Expected: "A: lane-4 12/1"
            parts = line.split()
            if len(parts) != 3:
                continue
            side = parts[0].rstrip(":")
            lane = int(parts[1].split("-")[1])
            counts = parts[2].split("/")
            results.append({
                "side": side,
                "lane": lane,
                "err_count": int(counts[0]),
                "err_sticky": int(counts[1]) if len(counts) > 1 else 0,
            })
        return results
