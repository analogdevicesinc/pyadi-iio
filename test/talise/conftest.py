"""Labgrid fixtures for the ADRV9009-ZU11EG (ADRV2CRR-FMC) production PL DDR4 tests.

The board must be strapped for SD boot and its labgrid place driven by the
``BootFPGASoCSSH`` strategy. The suite is launched inside a reservation, e.g.::

    adi-lg request --part adrv9009zu11eg --carrier adrv2crr-fmc --mode reserve \\
        --run 'python -m pytest test/talise'

which exports ``LG_ENV``. The fixture then

1. boots the image already on the card and saves its ``/boot/BOOT.BIN`` once
   as ``/boot/BOOT.BIN.stock-ci``,
2. uploads ``TALISE_BOOT_BIN`` over SSH as ``/boot/BOOT.BIN`` and
   power-cycles into it (BootFPGASoCSSH),
3. on teardown, restores the stock ``BOOT.BIN`` and powers the board off.

Environment:
    TALISE_HW=1            enable the hardware tests (skipped otherwise)
    TALISE_CONFIG          full | ddr_lo | ddr_hi (selects the chip mapping)
    TALISE_BOOT_BIN        path to the BOOT.BIN under test
    LG_ENV                 labgrid env of the reserved place
    TALISE_LOG_DIR         where boot/console logs go (default: ./boot_logs)
"""

import os

import ddr_layout
import pytest
from talise_hw import (
    HELPER_PATH,
    HELPER_SRC,
    STOCK_BACKUP,
    TaliseBoard,
    _log_dir,
    _out,
    _sha256,
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
    boot_bin = os.environ.get("TALISE_BOOT_BIN")
    if not env_path or not boot_bin or not os.path.isfile(boot_bin):
        pytest.fail("LG_ENV and an existing TALISE_BOOT_BIN are required")
    boot_bin = os.path.abspath(boot_bin)
    boot_bin_sha = _sha256(boot_bin)
    record_testsuite_property("talise_config", talise_config)
    record_testsuite_property("boot_bin_sha256", boot_bin_sha)
    record_testsuite_property("lg_place", os.environ.get("LG_PLACE", ""))

    import adi_lg_plugins  # noqa: F401  (registers the ADI drivers and strategies)
    from labgrid import Environment

    # BootFPGASoCSSH collects the Kuiper release boot files when the target is
    # built, which can download a full image to this host. Only BOOT.BIN is
    # replaced here (the card keeps its kernel and devicetree): skip that lookup.
    patched = []
    for cls in _boot_file_drivers():
        patched.append((cls, cls.get_boot_files_from_release))
        cls.get_boot_files_from_release = (
            lambda self, get_all_files=False: self._boot_files
        )
    try:
        env = Environment(env_path)
        target = env.get_target("main")
        strategy = target.get_driver("BootFPGASoCSSH")
    finally:
        for cls, orig in patched:
            cls.get_boot_files_from_release = orig
    if strategy.kuiper is None:
        pytest.fail(
            "the place's env has no KuiperDLDriver; BootFPGASoCSSH cannot upload BOOT.BIN"
        )
    shell = strategy.shell
    logs = _log_dir()
    restore_needed = False
    stock_sha = None
    try:
        # 1. Boot whatever is on the card and keep its BOOT.BIN once
        strategy.transition("booted")
        target.activate(shell)
        _, _, code = shell.run(f"test -f {STOCK_BACKUP}")
        if code != 0:
            shell.run_check(f"cp /boot/BOOT.BIN {STOCK_BACKUP} && sync")
        stock_sha = _out(shell.run_check(f"sha256sum {STOCK_BACKUP} | cut -d' ' -f1"))
        record_testsuite_property("stock_boot_bin_sha256", stock_sha)
        target.deactivate(shell)

        # 2. Upload only the BOOT.BIN under test (the strategy also collected the
        #    Kuiper release files at init; the card already has those)
        strategy.kuiper._boot_files = [boot_bin]
        restore_needed = True
        strategy.transition("shell")
        (logs / f"boot_{talise_config}.log").write_text(strategy.boot_log or "")

        board = TaliseBoard(target, strategy, shell, talise_config, boot_bin_sha)
        board.check("dmesg -n 1")  # keep printk off the console
        on_card = board.check("sha256sum /boot/BOOT.BIN | cut -d' ' -f1")
        if on_card != boot_bin_sha:
            pytest.fail(f"/boot/BOOT.BIN is {on_card}, expected {boot_bin_sha}")
        yield board
    finally:
        if restore_needed and stock_sha:
            try:
                target.activate(shell)
                shell.run_check(f"cp {STOCK_BACKUP} /boot/BOOT.BIN && sync")
                restored = _out(
                    shell.run_check("sha256sum /boot/BOOT.BIN | cut -d' ' -f1")
                )
                if restored != stock_sha:
                    print(
                        f"WARNING: restored BOOT.BIN is {restored}, stock was {stock_sha}"
                    )
            except Exception as e:  # noqa: BLE001
                print(
                    f"ERROR: board left on the test BOOT.BIN, restore {STOCK_BACKUP} manually: {e}"
                )
                (logs / "RESTORE_FAILED").write_text(
                    f"{e}\nplace={os.environ.get('LG_PLACE', '')}\n"
                )
        _power_off(target, strategy)


@pytest.fixture(scope="session")
def design_identity(talise_board):
    """Proof that the production PL design (not the stock one) is running.

    Reads the strings in the axi_sysid ROM (0x45000800, present at the same
    address in every ADI ZynqMP design, so it is safe to read on any image)
    and adds the kernel's sysid log lines.
    """
    rom = (
        "python3 -c \"import mmap,os,re;f=os.open('/dev/mem',os.O_RDONLY|os.O_SYNC);"
        "m=mmap.mmap(f,0x1000,mmap.MAP_SHARED,mmap.PROT_READ,offset=0x45000000);"
        "w=memoryview(m).cast('I');b=b''.join(w[i].to_bytes(4,'little') for i in range(0x200,0x400));"
        "print(' '.join(s.decode() for s in re.findall(rb'[ -~]{4,}',b)))\""
    )
    rom_out, _ = talise_board.run(rom, timeout=30)
    log_out, _ = talise_board.run(
        "dmesg | grep -i 'sysid\\|System ID' | head -5 || true"
    )
    return f"{rom_out}\n{log_out}".strip()


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
