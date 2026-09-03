# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import re


class GtDebugGpio:
    """axi_pcie_xcvr_gpio, reached through its gpiochip.

    Needs an axi_pcie_xcvr_gpio node in the device tree so gpio-xilinx binds,
    and libgpiod on the target. The two axi_gpio channels appear as one
    contiguous gpiochip (gpio-xilinx sw_map): channel 1 is LOOPBACK, 3 bits per
    lane on lines 0..3N-1, channel 2 is TXINHIBIT, one bit per lane on lines
    3N..4N-1. Channel 1 carries the GTY LOOPBACK encoding from UG578.
    """

    NORMAL = 0b000
    NEAR_END_PCS = 0b001
    NEAR_END_PMA = 0b010
    FAR_END_PMA = 0b100
    FAR_END_PCS = 0b110

    # NEAR_END_* loop inside the transmitting transceiver, so they need no partner
    # and no loopback module. FAR_END_* return received data to the sender.
    MODE_NAMES = {
        NORMAL: "disabled (external path)",
        NEAR_END_PCS: "internal near-end PCS",
        NEAR_END_PMA: "internal near-end PMA",
        FAR_END_PMA: "far-end PMA",
        FAR_END_PCS: "far-end PCS",
    }

    @classmethod
    def mode_name(cls, mode):
        return cls.MODE_NAMES.get(mode, "unknown")

    def __init__(self, fs, phys_addr, num_lanes):
        self.fs = fs
        self.num_lanes = num_lanes
        self.label = f"{phys_addr:x}.gpio"
        self.chip = self._find_chip()
        self.v2 = self._is_libgpiod_v2()

    def _find_chip(self):
        out, _ = self.fs._run("gpiodetect")
        if not out:
            raise RuntimeError(
                "gpiodetect produced no output; install libgpiod on the target"
            )
        for line in out.splitlines():
            # e.g. "gpiochip2 [88230000.gpio] (32 lines)"
            if f"[{self.label}]" in line:
                return line.split()[0]
        raise RuntimeError(
            f"no gpiochip labelled {self.label}; is the axi_pcie_xcvr_gpio node "
            "present in the device tree?"
        )

    def _is_libgpiod_v2(self):
        out, err = self.fs._run("gpioset --version")
        match = re.search(r"(\d+)\.", out or err)
        return bool(match) and int(match.group(1)) >= 2

    def _set_lines(self, assignments):
        args = " ".join(f"{offset}={value}" for offset, value in assignments)
        chip = f"-c {self.chip}" if self.v2 else self.chip
        # libgpiod v2's gpioset holds the lines until it exits, v1 exits at once.
        # Either is fine: the axi_gpio output register latches the value and
        # xgpio_free() only drops a runtime-PM reference, it does not clear the
        # register. So cap the runtime instead of waiting; 124 is timeout's
        # "killed at the deadline", which here means the value was applied.
        out, err = self.fs._run(f"timeout 2 gpioset {chip} {args}; echo rc=$?")
        rc = int(out.rsplit("rc=", 1)[-1])
        if rc not in (0, 124):
            raise RuntimeError(f"gpioset {chip} {args} failed (rc={rc}): {err}")

    def set_loopback(self, mode):
        self._set_lines(
            (lane * 3 + bit, (mode >> bit) & 1)
            for lane in range(self.num_lanes)
            for bit in range(3)
        )

    def set_txinhibit(self, enable):
        base = self.num_lanes * 3
        self._set_lines(
            (base + lane, 1 if enable else 0) for lane in range(self.num_lanes)
        )
