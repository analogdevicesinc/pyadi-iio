"""Hardware-free checks of the chip mapping and the memtest helper (fault injection)."""

import ddr_layout
import pl_ddr_memtest as mt
import pytest


@pytest.mark.parametrize(
    "config,mig,lane,part",
    [
        ("full", 0, 0, "U30"),
        ("full", 0, 1, "U30"),
        ("full", 0, 2, "U31"),
        ("full", 0, 3, "U31"),
        ("full", 1, 0, "U41"),
        ("full", 1, 3, "U42"),
        ("ddr_lo", 0, 0, "U30"),
        ("ddr_lo", 0, 1, "U30"),
        ("ddr_lo", 1, 1, "U41"),
        ("ddr_hi", 0, 0, "U31"),
        ("ddr_hi", 0, 1, "U31"),
        ("ddr_hi", 1, 0, "U42"),
    ],
)
def test_lane_part(config, mig, lane, part):
    assert ddr_layout.lane_part(config, mig, lane) == part


def test_lane_out_of_range():
    with pytest.raises(ValueError):
        ddr_layout.lane_part("ddr_lo", 0, 2)


def test_sizes():
    assert ddr_layout.mig_size(0) == 2 << 30
    assert ddr_layout.mig_size(1) == ddr_layout.mig_size(2) == 1 << 30
    assert ddr_layout.describe("ddr_hi", 1) == "MIG 1 (U42)"


class FakeWindow(mt.Window):
    """In-memory window with optional stuck-at-1 data bit or aliased address bit."""

    def __init__(self, size, stuck_bit=None, alias_bit=None):
        self.buf = bytearray(size)
        self.mm = self.buf
        self.q = memoryview(self.buf).cast("Q")
        self.size = size
        self.stuck = 0 if stuck_bit is None else 1 << stuck_bit
        self.alias = 0 if alias_bit is None else 1 << alias_bit

    def close(self):
        pass

    def wr(self, off, val):
        self.q[(off & ~self.alias) // 8] = val & mt.MASK64

    def rd(self, off):
        return self.q[(off & ~self.alias) // 8] | self.stuck


@pytest.mark.parametrize(
    "bit,bus,lane",
    [(0, 4, 0), (17, 4, 2), (31, 4, 3), (40, 4, 1), (9, 2, 1), (16, 2, 0)],
)
def test_data_bus_names_lane(bit, bus, lane):
    res = mt.test_data_bus(FakeWindow(1 << 20, stuck_bit=bit), bus)
    assert set(res["lane_errors"]) == {lane}
    assert bit in res["failing_word_bits"]


def test_data_bus_clean():
    assert mt.test_data_bus(FakeWindow(1 << 20), 4)["lane_errors"] == {}


def test_address_bus_finds_alias():
    res = mt.test_address_bus(FakeWindow(1 << 20, alias_bit=12), 4)
    assert 12 in res["failing_address_bits"]
    assert mt.test_address_bus(FakeWindow(1 << 20), 4)["failing_address_bits"] == []


def test_pattern_clean_and_stuck():
    clean = mt.test_pattern(FakeWindow(8 << 20), 4, blocks=4, block_size=1 << 16)
    assert clean["lane_errors"] == {} and clean["blocks"] == 4

    class StuckMM(bytearray):
        """Stuck-at-1 bit 3 of every byte on lane 2 when read back as a block."""

        def __getitem__(self, key):
            data = bytearray(super().__getitem__(key))
            if isinstance(key, slice):
                start = key.start or 0
                for i in range((2 - start) % 4, len(data), 4):
                    data[i] |= 0x08
                return bytes(data)
            return data

    w = FakeWindow(8 << 20)
    w.mm = StuckMM(w.size)
    res = mt.test_pattern(w, 4, blocks=4, block_size=1 << 16)
    assert set(res["lane_errors"]) == {2}
    assert ddr_layout.lane_part("full", 0, 2) == "U31"


@pytest.mark.parametrize(
    "strings,expected",
    [
        (
            "ctalise_prod_ddr_parts 9b57cc3a8a134f8c vadj1793824817 adrv2crr_fmc prod",
            True,
        ),
        ("ctalise_prod_ddr_parts 9b57cc3a8 vadj17 adrv2crr_fmc_prod_ddr", True),
        ("cmain 085a6ed747a5f2fc vadj1781005315 adrv9009zu11eg", False),
        ("Traceback ... PermissionError", False),
    ],
)
def test_is_production_design(strings, expected):
    assert ddr_layout.is_production_design(strings) is expected
