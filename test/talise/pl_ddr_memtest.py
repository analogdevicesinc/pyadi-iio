#!/usr/bin/env python3
"""PL DDR4 memory test, run ON THE TARGET (pushed over SSH by test_talise_ddr.py).

Maps the MIG window through /dev/mem and runs one test, printing a single JSON
line. Errors are reported per DDR byte lane (lane = byte offset % bus bytes);
the host maps lanes to physical parts. Only standard library, python3.

Usage: pl_ddr_memtest.py <data_bus|address_bus|pattern> --base 0x400000000
           --size <bytes> --bus-bytes <2|4> [--blocks N] [--block-size B]

All accesses are 8-byte aligned (memoryview 'Q' stores) or page-aligned
block copies: the window is mapped as Device memory, where unaligned
accesses fault.
"""

import argparse
import array
import json
import mmap
import os
import sys
import time

PATTERNS_64 = (
    0x5555555555555555,
    0xAAAAAAAAAAAAAAAA,
    0x0000000000000000,
    0xFFFFFFFFFFFFFFFF,
)
MASK64 = (1 << 64) - 1


def lanes_of_bits(word_offset, xor_bits, bus_bytes):
    """Byte lanes touched by the set bits of ``xor_bits`` in the word at ``word_offset``."""
    lanes = set()
    for byte in range(8):
        if (xor_bits >> (8 * byte)) & 0xFF:
            lanes.add((word_offset + byte) % bus_bytes)
    return lanes


class Window:
    def __init__(self, base, size):
        self.fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
        self.mm = mmap.mmap(
            self.fd,
            size,
            mmap.MAP_SHARED,
            mmap.PROT_READ | mmap.PROT_WRITE,
            offset=base,
        )
        self.q = memoryview(self.mm).cast("Q")
        self.size = size

    def close(self):
        self.q.release()
        self.mm.close()
        os.close(self.fd)

    def wr(self, off, val):
        self.q[off // 8] = val & MASK64

    def rd(self, off):
        return self.q[off // 8]


def test_data_bus(w, bus_bytes, **_):
    """Walking one / walking zero on 64-bit words at the start, middle and end."""
    lane_errors = {}
    bit_errors = set()
    offsets = sorted({0, (w.size // 2) & ~0xFFF, w.size - 4096})
    for base_off in offsets:
        # Two words so every lane sees both beat positions for any bus width
        for word in range(2):
            off = base_off + 8 * word
            for bit in range(64):
                for val in (1 << bit, MASK64 ^ (1 << bit)):
                    w.wr(off, val)
                    got = w.rd(off)
                    diff = got ^ val
                    if diff:
                        bit_errors.add(bit)
                        for lane in lanes_of_bits(off, diff, bus_bytes):
                            lane_errors[lane] = lane_errors.get(lane, 0) + 1
    return {"lane_errors": lane_errors, "failing_word_bits": sorted(bit_errors)}


def test_address_bus(w, bus_bytes, **_):
    """Power-of-two address line test (aliasing / stuck address bits)."""
    pat, anti = 0xAAAAAAAAAAAAAAAA, 0x5555555555555555
    offsets = [0]
    step = 8
    while step < w.size:
        offsets.append(step)
        step <<= 1
    for off in offsets:
        w.wr(off, pat)
    stuck_high = []
    w.wr(0, anti)
    for off in offsets[1:]:
        if w.rd(off) != pat:
            stuck_high.append(off.bit_length() - 1)
    w.wr(0, pat)
    stuck_low_or_short = []
    for test_off in offsets[1:]:
        w.wr(test_off, anti)
        if w.rd(0) != pat:
            stuck_low_or_short.append(test_off.bit_length() - 1)
        for off in offsets[1:]:
            if off != test_off and w.rd(off) != pat:
                stuck_low_or_short.append(test_off.bit_length() - 1)
                break
        w.wr(test_off, pat)
    bad = sorted(set(stuck_high) | set(stuck_low_or_short))
    # Address lines are shared by both parts of a MIG: no per-lane attribution
    return {
        "lane_errors": {},
        "failing_address_bits": bad,
        "address_lines_tested": len(offsets) - 1,
    }


def _block_bytes(kind, off, n):
    if kind == "addr":
        return array.array("Q", range(off, off + n, 8)).tobytes()
    if kind == "naddr":
        return array.array(
            "Q", ((~a) & MASK64 for a in range(off, off + n, 8))
        ).tobytes()
    val = PATTERNS_64[kind]
    return array.array("Q", [val]).tobytes() * (n // 8)


def test_pattern(w, bus_bytes, blocks=64, block_size=1 << 20, **_):
    """Fixed and address-unique patterns over evenly spread, page-aligned blocks."""
    lane_errors = {}
    first_errors = []
    span = w.size - block_size
    starts = sorted({(span * i // max(blocks - 1, 1)) & ~0xFFF for i in range(blocks)})
    kinds = list(range(len(PATTERNS_64))) + ["addr", "naddr"]
    t0 = time.time()
    for kind in kinds:
        expected = {}
        for off in starts:
            buf = _block_bytes(kind, off, block_size)
            w.mm[off : off + block_size] = buf
            expected[off] = buf
        for off in starts:
            got = w.mm[off : off + block_size]
            exp = expected[off]
            if got == exp:
                continue
            gq = memoryview(got).cast("Q")
            eq = memoryview(exp).cast("Q")
            for i in range(len(eq)):
                diff = gq[i] ^ eq[i]
                if diff:
                    word_off = off + 8 * i
                    for lane in lanes_of_bits(word_off, diff, bus_bytes):
                        lane_errors[lane] = lane_errors.get(lane, 0) + 1
                    if len(first_errors) < 16:
                        first_errors.append(
                            {
                                "offset": hex(word_off),
                                "expected": hex(eq[i]),
                                "got": hex(gq[i]),
                                "pattern": str(kind),
                            }
                        )
    return {
        "lane_errors": lane_errors,
        "first_errors": first_errors,
        "blocks": len(starts),
        "block_size": block_size,
        "bytes_checked": len(starts) * block_size * len(kinds),
        "seconds": round(time.time() - t0, 1),
    }


TESTS = {
    "data_bus": test_data_bus,
    "address_bus": test_address_bus,
    "pattern": test_pattern,
}


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("test", choices=sorted(TESTS))
    p.add_argument("--base", type=lambda s: int(s, 0), required=True)
    p.add_argument("--size", type=lambda s: int(s, 0), required=True)
    p.add_argument("--bus-bytes", type=int, choices=(2, 4), required=True)
    p.add_argument("--blocks", type=int, default=64)
    p.add_argument("--block-size", type=lambda s: int(s, 0), default=1 << 20)
    a = p.parse_args(argv)
    result = {
        "test": a.test,
        "base": hex(a.base),
        "size": a.size,
        "bus_bytes": a.bus_bytes,
    }
    try:
        w = Window(a.base, a.size)
    except OSError as e:
        result.update(status="no_access", error=f"{type(e).__name__}: {e}")
        print(json.dumps(result))
        return 0
    try:
        out = TESTS[a.test](w, a.bus_bytes, blocks=a.blocks, block_size=a.block_size)
        out["lane_errors"] = {str(k): v for k, v in sorted(out["lane_errors"].items())}
        failed = bool(out["lane_errors"]) or bool(out.get("failing_address_bits"))
        result.update(out, status="fail" if failed else "pass")
    finally:
        w.close()
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
