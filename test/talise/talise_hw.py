"""Helpers shared by the Talise PL DDR4 hardware tests (see conftest.py)."""

import base64
import hashlib
import json
import os
import shlex
from pathlib import Path

import ddr_layout
import pytest

HELPER_PATH = "/tmp/pl_ddr_memtest.py"
FIRMWARE_NAME = "talise_pl.bit.bin"
FIRMWARE_PATH = f"/lib/firmware/{FIRMWARE_NAME}"
OVERLAY_NAME = "talise_pl"
OVERLAY_SRC = Path(__file__).with_name("talise_pl.dtbo")

# FPD_SLCR.AFI_FS: M_AXI_HPM0_FPD data width (bits 9:8; 0 = 32, 1 = 64,
# 2 = 128 bit). The production design uses a 128-bit HPM0_FPD to reach MIG 0
# (its psu_init writes 0x200 under mask 0x300); a stock FSBL may set it
# otherwise, and a runtime PL load does not rerun psu_init.
AFI_FS_FPD = 0xFD61_5000
AFI_FS_HPM0_FPD_MASK = 0x300
AFI_FS_HPM0_FPD_128 = 0x200
HELPER_SRC = Path(__file__).with_name("pl_ddr_memtest.py")


def _log_dir():
    path = Path(os.environ.get("TALISE_LOG_DIR", Path(__file__).with_name("boot_logs")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _out(lines):
    if isinstance(lines, (list, tuple)):
        return "\n".join(str(x) for x in lines).strip()
    return str(lines).strip()


class TaliseBoard:
    """Booted board handle: serial shell plus the expected build identity."""

    def __init__(self, target, strategy, shell, config, pl_bin_sha):
        self.target = target
        self.strategy = strategy
        self.shell = shell
        self.config = config
        self.pl_bin_sha = pl_bin_sha
        self.props = {}

    def run(self, cmd, timeout=60):
        """Run on the target, return (stdout, exit code)."""
        stdout, _, code = self.shell.run(cmd, timeout=timeout)
        return _out(stdout), code

    def check(self, cmd, timeout=60):
        out, code = self.run(cmd, timeout=timeout)
        if code != 0:
            raise AssertionError(f"`{cmd}` exited {code}: {out}")
        return out

    def devmem32(self, address):
        cmd = (
            f"(command -v devmem >/dev/null && devmem {address:#x} 32) || "
            f"busybox devmem {address:#x} 32"
        )
        return int(self.check(cmd, timeout=20).splitlines()[-1], 16)

    def devmem32_write(self, address, value):
        cmd = (
            f"(command -v devmem >/dev/null && devmem {address:#x} 32 {value:#x}) || "
            f"busybox devmem {address:#x} 32 {value:#x}"
        )
        self.check(cmd, timeout=20)

    def push_file(self, local, remote, chunk=768):
        """Copy a small file over the serial shell (base64 chunks, hash checked)."""
        data = Path(local).read_bytes()
        enc = base64.b64encode(data).decode()
        staging = remote + ".b64"
        self.check(f": > {shlex.quote(staging)}")
        for i in range(0, len(enc), chunk):
            self.check(
                f"printf %s {shlex.quote(enc[i:i + chunk])} >> {shlex.quote(staging)}"
            )
        digest = hashlib.sha256(data).hexdigest()
        self.check(
            f"base64 -d {shlex.quote(staging)} > {shlex.quote(remote)} && rm -f {shlex.quote(staging)} && "
            f"echo {shlex.quote(f'{digest}  {remote}')} | sha256sum -c -"
        )


def run_memtest(board, helper, test, mig=0, timeout=300, **kw):
    """Run one helper test on MIG ``mig``; returns the parsed JSON result."""
    if mig != 0:
        raise ValueError("only MIG 0 is mapped into the PS address space")
    m = ddr_layout.mig_map(board.config, mig)
    args = [
        helper,
        test,
        "--base",
        hex(ddr_layout.MIG0_BASE),
        "--size",
        str(ddr_layout.mig_size(m)),
        "--bus-bytes",
        str(ddr_layout.bus_bytes(m)),
    ]
    for k, v in kw.items():
        args += [f"--{k.replace('_', '-')}", str(v)]
    cmd = f"timeout {timeout} python3 " + " ".join(shlex.quote(a) for a in args)
    try:
        out, code = board.run(cmd, timeout=timeout + 30)
    except Exception as e:  # noqa: BLE001  (pexpect TIMEOUT / lost console)
        pytest.fail(
            f"{ddr_layout.describe(board.config, mig)} access hung during {test} "
            f"(no prompt within {timeout + 30} s): {type(e).__name__}"
        )
    if code == 124:
        pytest.fail(
            f"{ddr_layout.describe(board.config, mig)} {test} timed out after {timeout} s"
        )
    line = next((l for l in reversed(out.splitlines()) if l.startswith("{")), None)
    if line is None:
        pytest.fail(f"memtest {test} produced no result (exit {code}): {out[-500:]}")
    return json.loads(line)


def load_pl(board, logger=print):
    """Full PL reconfiguration with FIRMWARE_PATH, already on the target.

    Uses the fpga_manager sysfs ``firmware`` attribute when the kernel has it
    (Xilinx/ADI kernels), else a configfs overlay on /fpga-full. Returns the
    method used. The SD card is not touched: a power cycle brings the stock
    design back.
    """
    mgr = "/sys/class/fpga_manager/fpga0"
    _, code = board.run(f"test -w {mgr}/firmware")
    if code == 0:
        board.check(f"echo 0 > {mgr}/flags")  # 0 = full reconfiguration
        out, code = board.run(f"echo {FIRMWARE_NAME} > {mgr}/firmware", timeout=120)
        method = "fpga_manager firmware"
    else:
        _, code = board.run("test -d /proc/device-tree/fpga-full")
        if code != 0:
            pytest.fail(
                "no way to load the PL: neither fpga_manager/fpga0/firmware nor a "
                "/fpga-full region exist on this kernel"
            )
        board.check(
            "mountpoint -q /sys/kernel/config || mount -t configfs none /sys/kernel/config"
        )
        ovl = f"/sys/kernel/config/device-tree/overlays/{OVERLAY_NAME}"
        board.run(f"rmdir {ovl} 2>/dev/null")
        board.check(f"mkdir {ovl}")
        out, code = board.run(f"cat /tmp/{OVERLAY_NAME}.dtbo > {ovl}/dtbo", timeout=120)
        method = "fpga-full overlay"
    state, _ = board.run(f"cat {mgr}/state")
    log, _ = board.run("dmesg | grep -iE 'fpga|pcap|zynqmp' | tail -8")
    logger(f"PL load via {method}: exit {code}, state {state!r}\n{log}")
    if code != 0 or state.strip() != "operating":
        pytest.fail(
            f"PL load via {method} failed (exit {code}, state {state!r}): {out} {log}"
        )
    return method


def set_hpm0_fpd_width(board):
    """Set M_AXI_HPM0_FPD to the production design's 128 bits; returns (old, new)."""
    old = board.devmem32(AFI_FS_FPD)
    new = (old & ~AFI_FS_HPM0_FPD_MASK) | AFI_FS_HPM0_FPD_128
    if new != old:
        board.devmem32_write(AFI_FS_FPD, new)
    got = board.devmem32(AFI_FS_FPD)
    if got & AFI_FS_HPM0_FPD_MASK != AFI_FS_HPM0_FPD_128:
        pytest.fail(f"FPD_SLCR.AFI_FS write did not stick: {old:#x} -> {got:#x}")
    return old, got
