"""Labgrid fixtures for the ADRV9009-ZU11EG (ADRV2CRR-FMC) production PL DDR4 tests.

The board boots its own (stock) SD card image; only the PL is replaced, at
runtime, so the card is never modified and a power cycle always brings the
board back. Its labgrid place is driven by ``BootFPGASoCSSH`` (power, serial
shell, SSH). The suite is launched inside a reservation, e.g.::

    adi-lg request --part adrv9009zu11eg --mode reserve \\
        --run 'python -m pytest test/talise'

which exports ``LG_ENV``. The fixture then

1. powers the board on and logs in to the stock Linux,
2. uploads ``TALISE_PL_BIN`` (bootgen ``-process_bitstream bin`` output) over
   SSH to /lib/firmware and does a full PL reconfiguration through
   fpga_manager (or a /fpga-full overlay),
3. sets the HPM0_FPD port width the production design expects,
4. on teardown, removes the firmware file and powers the board off.

Environment:
    TALISE_HW=1            enable the hardware tests (skipped otherwise)
    TALISE_CONFIG          full | ddr_lo | ddr_hi (selects the chip mapping)
    TALISE_PL_BIN          path to the .bit.bin of the build under test
    LG_ENV                 labgrid env of the reserved place
    TALISE_LOG_DIR         where boot/console logs go (default: ./boot_logs)
"""

import os
import shlex

import ddr_layout
import pytest
from talise_hw import (
    FIRMWARE_PATH,
    HELPER_PATH,
    HELPER_SRC,
    OVERLAY_NAME,
    OVERLAY_SRC,
    TaliseBoard,
    _log_dir,
    _sha256,
    load_pl,
    set_hpm0_fpd_width,
)


def pytest_configure(config):
    config.addinivalue_line("markers", "talise_hw: needs the reserved ADRV9009-ZU11EG")


@pytest.fixture(scope="session")
def talise_config():
    if os.environ.get("TALISE_HW") != "1":
        pytest.skip(
            "set TALISE_HW=1 inside an adi-lg reservation to run the hardware tests"
        )
    config = os.environ.get("TALISE_CONFIG", "")
    if config not in ddr_layout.CONFIG_MAPS:
        pytest.fail(
            f"TALISE_CONFIG must be one of {sorted(ddr_layout.CONFIG_MAPS)}, got {config!r}"
        )
    return config


_MISSING = object()


def _boot_file_drivers():
    """Driver classes BootFPGASoCSSH may bind as ``kuiper`` (both collect files at init)."""
    import importlib

    classes = []
    for mod, name in (
        ("adi_lg_plugins.drivers.kuiperdldriver", "KuiperDLDriver"),
        ("adi_lg_plugins.drivers.cloudsmithdldriver", "CloudsmithDLDriver"),
    ):
        try:
            cls = getattr(importlib.import_module(mod), name)
        except (ImportError, AttributeError):
            continue
        if hasattr(cls, "get_boot_files_from_release"):
            classes.append(cls)
    return classes


def _power_off(target, strategy):
    """Power off even when @never_retry has marked the strategy broken."""
    try:
        strategy.transition("powered_off")
    except Exception:
        if strategy.power is not None:
            target.activate(strategy.power)
            strategy.power.off()


@pytest.fixture(scope="session")
def talise_board(talise_config, record_testsuite_property):
    if os.environ.get("TALISE_HW") != "1":
        pytest.skip(
            "set TALISE_HW=1 inside an adi-lg reservation to run the hardware tests"
        )
    env_path = os.environ.get("LG_ENV")
    pl_bin = os.environ.get("TALISE_PL_BIN")
    if not env_path or not pl_bin or not os.path.isfile(pl_bin):
        pytest.fail("LG_ENV and an existing TALISE_PL_BIN are required")
    pl_bin = os.path.abspath(pl_bin)
    pl_bin_sha = _sha256(pl_bin)
    record_testsuite_property("talise_config", talise_config)
    record_testsuite_property("pl_bin_sha256", pl_bin_sha)
    record_testsuite_property("lg_place", os.environ.get("LG_PLACE", ""))

    import adi_lg_plugins  # noqa: F401  (registers the ADI drivers and strategies)
    from labgrid import Environment

    # BootFPGASoCSSH activates its Kuiper/Cloudsmith download driver and
    # collects the release boot files when the target is built. Activation
    # starts an agent on the exporter over SSH and the lookup can download a
    # full image; neither is needed (the card's own image is booted as is and
    # only the PL is replaced), and the CI runner has no SSH access to the
    # exporter. Make both no-ops while the target is built.
    stubs = {
        "get_boot_files_from_release": lambda self, get_all_files=False: self._boot_files,
        "on_activate": lambda self: None,
        "on_deactivate": lambda self: None,
    }
    patched = []
    for cls in _boot_file_drivers():
        for name, stub in stubs.items():
            patched.append((cls, name, cls.__dict__.get(name, _MISSING)))
            setattr(cls, name, stub)
    try:
        env = Environment(env_path)
        target = env.get_target("main")
        kind, strategy = _strategy(target)
    finally:
        for cls, name, orig in reversed(patched):
            if orig is _MISSING:
                delattr(cls, name)
            else:
                setattr(cls, name, orig)
    record_testsuite_property("boot_strategy", kind)
    logs = _log_dir()
    loaded = False
    shell = None
    try:
        # 1. Boot the board's stock image and log in on the serial console
        shell = _boot_stock(kind, target, strategy)
        board = TaliseBoard(target, strategy, shell, talise_config, pl_bin_sha)
        board.check("dmesg -n 1")  # keep printk off the console
        stock = board.check("sha256sum /boot/BOOT.BIN | cut -d' ' -f1")
        record_testsuite_property("card_boot_bin_sha256", stock)
        board.props["design_before"] = _sysid_strings(board)

        # 2. Upload the bitstream (15 MB; the serial line is too slow): pulled
        #    by the board from TALISE_PL_URL when set, else pushed over SSH
        board.check("mkdir -p /lib/firmware")
        url = os.environ.get("TALISE_PL_URL")
        if url:
            record_testsuite_property("pl_upload", "http")
            board.check(f"wget -q -O {FIRMWARE_PATH} {shlex.quote(url)}", timeout=300)
            board.push_file(OVERLAY_SRC, f"/tmp/{OVERLAY_NAME}.dtbo")
        else:
            record_testsuite_property("pl_upload", "ssh")
            ssh = strategy.ssh
            ip = _ipv4(board, getattr(strategy, "eth_interface", "eth0"))
            strategy._override_networkservice_address(ssh.networkservice, ip)
            target.activate(ssh)
            ssh.put(pl_bin, FIRMWARE_PATH)
            ssh.put(str(OVERLAY_SRC), f"/tmp/{OVERLAY_NAME}.dtbo")
            target.deactivate(ssh)
        on_target = board.check(f"sha256sum {FIRMWARE_PATH} | cut -d' ' -f1")
        if on_target != pl_bin_sha:
            pytest.fail(f"{FIRMWARE_PATH} is {on_target}, expected {pl_bin_sha}")

        # 3. Quiesce userspace that polls PL IP, then reconfigure the PL. The
        #    stock design's kernel drivers stay bound to addresses the
        #    production design mostly shares; the tests use /dev/mem only.
        board.run("systemctl stop iiod 2>/dev/null; true")
        loaded = True
        method = load_pl(board)
        record_testsuite_property("pl_load_method", method)
        old, new = set_hpm0_fpd_width(board)
        record_testsuite_property("afi_fs_fpd", f"{old:#x}->{new:#x}")
        (logs / f"boot_{talise_config}.log").write_text(
            getattr(strategy, "boot_log", "") or ""
        )
        yield board
    finally:
        if loaded and shell is not None:
            try:
                target.activate(shell)
                shell.run(f"rm -f {FIRMWARE_PATH} /tmp/{OVERLAY_NAME}.dtbo; sync")
            except Exception as e:  # noqa: BLE001
                print(f"cleanup of {FIRMWARE_PATH} failed (harmless): {e}")
        _power_off(target, strategy)


def _strategy(target):
    """The place's boot strategy: BootFPGASoCSSH (SD) or BootZynqMPJTAG (JTAG)."""
    for kind in ("BootFPGASoCSSH", "BootZynqMPJTAG"):
        try:
            return kind, target.get_driver(kind)
        except Exception:  # noqa: BLE001  (labgrid NoDriverFoundError)
            continue
    pytest.fail(
        "the place's env has neither a BootFPGASoCSSH nor a BootZynqMPJTAG strategy"
    )


def _boot_stock(kind, target, strategy):
    """Boot the board's stock image to a logged-in serial shell; nothing is written."""
    if kind == "BootFPGASoCSSH":
        strategy.transition("booted")
        target.activate(strategy.shell)
        return strategy.shell
    # JTAG boot: the stock PL and psu_init (paths on the exporter, as used by
    # the place's other users) are loaded over JTAG, then U-Boot boots the
    # card's stock kernel. The bitstream under test is loaded later, at runtime.
    bit = os.environ.get("TALISE_STOCK_BITSTREAM_REMOTE")
    psu = os.environ.get("TALISE_STOCK_PSU_INIT_REMOTE")
    if not bit or not psu:
        pytest.fail(
            "BootZynqMPJTAG needs TALISE_STOCK_BITSTREAM_REMOTE and "
            "TALISE_STOCK_PSU_INIT_REMOTE (stock PL and psu_init.tcl on the exporter)"
        )
    strategy.bitstream_path = bit
    strategy.psu_init_tcl = psu
    strategy.transition("shell")
    return target.get_driver("ADIShellDriver")


def _ipv4(board, iface, timeout=60.0):
    """The board's IPv4 on ``iface`` (DHCP can lag the login prompt)."""
    import ipaddress
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        addrs = board.shell.get_ip_addresses(iface) or []
        v4 = [str(a.ip) for a in addrs if isinstance(a.ip, ipaddress.IPv4Address)]
        if v4:
            return v4[0]
        time.sleep(3)
    pytest.fail(f"no IPv4 address on {iface} after {timeout:.0f} s")


_SYSID_CMD = (
    "python3 -c \"import mmap,os,re;f=os.open('/dev/mem',os.O_RDONLY|os.O_SYNC);"
    "m=mmap.mmap(f,0x1000,mmap.MAP_SHARED,mmap.PROT_READ,offset=0x45000000);"
    "w=memoryview(m).cast('I');b=b''.join(w[i].to_bytes(4,'little') for i in range(0x200,0x400));"
    "print(' '.join(s.decode() for s in re.findall(rb'[ -~]{4,}',b)))\""
)


def _sysid_strings(board):
    """Strings in the axi_sysid ROM (0x45000800 in every ADI ZynqMP design)."""
    out, _ = board.run(_SYSID_CMD, timeout=30)
    return out


@pytest.fixture(scope="session")
def design_identity(talise_board):
    """Proof that the production PL design (not the stock one) is running."""
    return _sysid_strings(talise_board)


@pytest.fixture(scope="session")
def calib(talise_board, design_identity):
    """ddr_calib_gpio, read once before anything touches PL DDR."""
    if ddr_layout.SYSID_PROJECT_PREFIX not in design_identity:
        pytest.fail(
            f"production design not identified from axi_sysid ({design_identity!r}); "
            "not touching PL addresses of an unknown design"
        )
    value = talise_board.devmem32(ddr_layout.CALIB_GPIO_ADDR)
    return {0: bool(value & 1), 1: bool(value & 2), "raw": value}


@pytest.fixture(scope="session")
def memtest_helper(talise_board):
    talise_board.push_file(HELPER_SRC, HELPER_PATH)
    return HELPER_PATH
