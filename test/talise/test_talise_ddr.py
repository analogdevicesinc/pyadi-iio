"""PL DDR4 per-part checks for the ADRV9009-ZU11EG production builds.

Each MIG drives two x16 parts (MIG 0: U30/U31, MIG 1: U41/U42); the
adrv2crr_fmc_production_ddr_lo / _ddr_hi builds narrow both MIGs to one part,
so a failure here points at a single part. See ddr_layout.py.

Ordering matters on hardware: an access to the window of a MIG that did not
calibrate can stall the AXI port and hang the CPU, which would hide the
result. Every PL DDR access is therefore gated on the calibration bit read
by the ``calib`` fixture.
"""

import os

import ddr_layout
import pytest
from talise_hw import run_memtest

pytestmark = pytest.mark.talise_hw


def _parts_for_lanes(config, mig, lane_errors):
    parts = {}
    for lane, count in lane_errors.items():
        part = ddr_layout.lane_part(config, mig, int(lane))
        parts[part] = parts.get(part, 0) + count
    return parts


def test_production_design_loaded(talise_board, design_identity, record_property):
    version = talise_board.check("cat /proc/version")
    record_property("kernel", version)
    record_property("axi_sysid", design_identity)
    record_property(
        "axi_sysid_before_load", talise_board.props.get("design_before", "")
    )
    assert (
        ddr_layout.SYSID_PROJECT_PREFIX in design_identity
    ), f"axi_sysid does not report {ddr_layout.SYSID_PROJECT_PREFIX}: {design_identity!r}"


@pytest.mark.parametrize("mig", [0, 1])
def test_pl_ddr_calibration(talise_board, calib, mig, record_property):
    record_property("calib_gpio", hex(calib["raw"]))
    record_property(
        "parts", "+".join(ddr_layout.active_parts(talise_board.config, mig))
    )
    assert calib[mig], (
        f"{ddr_layout.describe(talise_board.config, mig)} did not calibrate "
        f"(ddr_calib_gpio={calib['raw']:#x}, build {talise_board.config})"
    )


@pytest.mark.parametrize("test", ["data_bus", "address_bus", "pattern"])
def test_mig0_memory(talise_board, calib, memtest_helper, test, record_property):
    config = talise_board.config
    where = ddr_layout.describe(config, 0)
    if not calib[0]:
        pytest.skip(f"{where} not calibrated; not accessing its address window")
    result = run_memtest(talise_board, memtest_helper, test, mig=0)
    record_property("result", result)
    if result.get("status") == "no_access":
        pytest.skip(f"/dev/mem mapping refused on the target: {result.get('error')}")
    failing_parts = _parts_for_lanes(config, 0, result.get("lane_errors", {}))
    record_property("failing_parts", failing_parts)
    bad_addr = result.get("failing_address_bits", [])
    msg = []
    if failing_parts:
        msg.append(
            "data errors per part: "
            + ", ".join(f"{p}: {n}" for p, n in sorted(failing_parts.items()))
        )
    if bad_addr:
        msg.append(
            f"address bits {bad_addr} alias/stuck (address lines are shared by {where})"
        )
    if result.get("first_errors"):
        msg.append(f"first errors: {result['first_errors'][:4]}")
    assert result.get("status") == "pass", f"{where} {test} failed: " + "; ".join(msg)


@pytest.mark.skipif(
    os.environ.get("TALISE_MIG1_DATAPATH") != "1",
    reason="MIG 1 data path test needs TALISE_MIG1_DATAPATH=1 and network IIO access",
)
def test_mig1_dacfifo_loopback(talise_board, calib, record_property):
    """MIG 1 is only reachable through the TX DAC FIFO: send a cyclic ramp and
    look for it, bit exact, in the Talise digital (framer) loopback."""
    np = pytest.importorskip("numpy")
    adi = pytest.importorskip("adi")
    where = ddr_layout.describe(talise_board.config, 1)
    if not calib[1]:
        pytest.skip(f"{where} not calibrated; the DAC FIFO cannot use it")
    ip = talise_board.strategy.shell.get_ip_addresses(
        talise_board.strategy.eth_interface
    )
    ipv4 = [str(a.ip) for a in ip or [] if a.ip.version == 4]
    if not ipv4:
        pytest.skip("target has no IPv4 address for network IIO")
    try:
        sdr = adi.adrv9009_zu11eg(uri=f"ip:{ipv4[0]}")
    except Exception as e:  # noqa: BLE001
        pytest.skip(f"no IIO context at ip:{ipv4[0]} from this runner: {e}")
    phys = [sdr._ctrl, sdr._ctrl_b]
    old = [p.debug_attrs["bist_framer_a_loopback"].value for p in phys]
    try:
        for p in phys:
            p.debug_attrs["bist_framer_a_loopback"].value = "1"
        n = 2**14
        ramp = (np.arange(n) % 4096 - 2048).astype(np.int16) * 8
        sdr.tx_enabled_channels = [0]
        sdr.rx_enabled_channels = [0]
        sdr.tx_cyclic_buffer = True
        sdr.rx_buffer_size = 4 * n
        sdr.tx(ramp + 1j * ramp[::-1])
        rx = sdr.rx()
        sdr.tx_destroy_buffer()
        seqs = [np.real(rx).astype(np.int16), np.imag(rx).astype(np.int16)]
        target = ramp[:256]
        found = any(
            np.array_equal(s[i : i + 256], target)
            for s in seqs
            for i in range(0, len(s) - 256)
        )
        record_property("found_ramp", found)
        assert (
            found
        ), f"cyclic TX ramp not found in loopback: {where} DAC FIFO data path corrupt"
    finally:
        for p, v in zip(phys, old):
            p.debug_attrs["bist_framer_a_loopback"].value = v
