"""Helpers shared by the Talise PL DDR4 hardware tests (see conftest.py)."""

import base64
import hashlib
import json
import os
import shlex
from pathlib import Path

import ddr_layout
import pytest

STOCK_BACKUP = "/boot/BOOT.BIN.stock-ci"
HELPER_PATH = "/tmp/pl_ddr_memtest.py"
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

    def __init__(self, target, strategy, shell, config, boot_bin_sha):
        self.target = target
        self.strategy = strategy
        self.shell = shell
        self.config = config
        self.boot_bin_sha = boot_bin_sha
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
