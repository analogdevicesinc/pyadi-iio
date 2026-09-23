# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""AD9084 JESD204 link and lane diagnostics.

Prints the state of every JESD204 lane in both directions and says which lanes,
if any, are broken. Read-only: no buffers are created, nothing is transmitted
and no chip setting is changed, so it is safe to run at any time, including
while another script holds the board.

  python ad9084_jesd_status.py                     default URI
  python ad9084_jesd_status.py --uri ip:10.48.65.177
  python ad9084_jesd_status.py --recheck 10        watch error counters for 10 s
  python ad9084_jesd_status.py --raw               also dump the unparsed strings

Exits 0 when every link is healthy and 1 when a fault is reported, so it can
gate a test script.

The two directions are reported by whichever end can see individual lanes:

  FPGA -> chip   the chip's JRX deframers report per-lane state themselves
  chip -> FPGA   the chip's JTX framers report only a summary, so the per-lane
                 detail comes from the FPGA's axi-jesd204-rx link core

Lane naming follows the link the lane belongs to, so lane 2 of the side-B
deframer is reported as B2.
"""

import argparse
import ctypes
import re
import sys
import time

import iio

import adi

DEFAULT_URI = "ip:10.48.65.177"

# The chip's "status" debug attribute is around 1.2 kB with four links enabled,
# and pylibiio reads every attribute into a fixed 1024 byte buffer, so going
# through DeviceDebugAttr.value fails with EIO on exactly the device this script
# exists to look at. The C entry point is called directly with room to spare.
ATTR_BUFFER_SIZE = 65536

# A chip JRX lane sits in one of three kinds of state. "Reset" is not a fault:
# the chip reports a fixed set of lane slots per link and parks the ones this
# configuration does not use, so a healthy L=8 link shows 8 good lanes and 4 in
# reset. Anything that is neither good nor parked has started training and
# stalled part way, which is what a real lane fault looks like.
LANE_GOOD = "good"
LANE_IDLE = "idle"
LANE_STALLED = "stalled"

GOOD_LANE_STATES = ("link is good",)
IDLE_LANE_STATES = ("reset",)

# The FPGA link core reports extended multiblock alignment per lane. Anything
# other than a lock means that lane never aligned.
EMB_LOCKED = "EMB_LOCK"


def parse_args():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--uri", default=DEFAULT_URI, help=f"IIO URI, default {DEFAULT_URI}",
    )
    parser.add_argument(
        "--recheck",
        type=float,
        default=2.0,
        metavar="SECONDS",
        help="re-read the FPGA lane error counters after this long and report "
        "the growth, which is what separates a lane that is failing now from "
        "one that logged errors while the link was training. 0 to skip. "
        "Default 2",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="also print the unparsed status strings from the chip and the FPGA "
        "link cores",
    )
    return parser.parse_args()


def read_debug_attr(device, name):
    """Read a device debug attribute without pylibiio's 1 kB buffer limit."""
    buf = ctypes.create_string_buffer(ATTR_BUFFER_SIZE)
    ret = iio._d_read_debug_attr(device._device, name.encode("ascii"), buf, len(buf))
    if ret < 0:
        raise OSError(-ret, f"reading debug attribute '{name}'")
    return buf.value.decode("ascii", "replace")


def find_by_label(ctx, label):
    """Find an IIO device by its label.

    The JESD204 link cores and the transceiver PHYs are all "adi-iio-fakedev",
    so the device name does not identify them and the label has to be used.
    """
    for device in ctx.devices:
        if "label" in device.attrs and device.attrs["label"].value == label:
            return device
    return None


def classify_lane(state):
    lowered = state.strip().lower()
    if lowered in GOOD_LANE_STATES:
        return LANE_GOOD
    if lowered in IDLE_LANE_STATES:
        return LANE_IDLE
    return LANE_STALLED


def parse_chip_status(text):
    """Parse the chip's JESD204 status string into a list of links.

    Each link comes back as a dict with its direction, side, configuration
    parameters, per-lane states and whatever summary line the chip appended.
    """
    links = []
    current = None

    header = re.compile(r"^(JRX|JTX)\s+(\S+?):\s*(.*)$")
    lane = re.compile(r"^\s+Lane(\d+)\s+status:\s*(.*)$", re.IGNORECASE)
    user = re.compile(r"^\s+User status:\s*(.*)$", re.IGNORECASE)

    for line in text.splitlines():
        if not line.strip():
            continue

        match = header.match(line)
        if match:
            direction, name, params = match.groups()
            side = re.search(r"LINK_([AB])", name)
            lanes_wanted = re.search(r"\bL=(\d+)", params)
            current = {
                "direction": direction,
                "name": name,
                "side": side.group(1) if side else "?",
                "params": params.strip(),
                "lanes_wanted": int(lanes_wanted.group(1)) if lanes_wanted else None,
                "enabled": "link_en=Enabled" in params,
                "lanes": {},
                "user": None,
                "notes": [],
            }
            links.append(current)
            continue

        if current is None:
            continue

        match = lane.match(line)
        if match:
            current["lanes"][int(match.group(1))] = match.group(2).strip()
            continue

        match = user.match(line)
        if match:
            current["user"] = match.group(1).strip()
            continue

        current["notes"].append(line.strip())

    return links


def parse_fpga_lanes(core):
    """Parse the per-lane blocks of an FPGA JESD204 link core.

    Returns {lane index: {"errors": int, "emb": str, "latency": str}}.
    """
    lanes = {}
    for name in core.attrs:
        match = re.fullmatch(r"lane(\d+)_info", name)
        if not match:
            continue
        lines = core.attrs[name].value.splitlines()
        entry = {"errors": None, "emb": "?", "latency": "?"}
        for line in lines:
            if "Errors" in line:
                digits = re.search(r"(\d+)", line)
                if digits:
                    entry["errors"] = int(digits.group(1))
            elif "multiblock alignment" in line:
                entry["emb"] = line.split(":")[-1].strip()
            elif "Latency" in line:
                digits = re.search(r"(\d+)", line.split(":", 1)[-1])
                if digits:
                    entry["latency"] = digits.group(1)
        lanes[int(match.group(1))] = entry
    return lanes


def summarize_core_status(text):
    """Pull the interesting lines out of an FPGA link core status string."""
    keep = ("Link status", "Lane rate:", "LEMC rate", "SYSREF captured",
            "SYSREF alignment error", "Link is")
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(k) or k in stripped for k in keep):
            out.append(stripped)
    return out


def report_chip_jrx(links, problems):
    """Report the FPGA -> chip direction from the chip's own deframer state."""
    print("FPGA -> CHIP   chip JRX deframers, per-lane state read from the chip")
    jrx = [link for link in links if link["direction"] == "JRX"]
    if not jrx:
        print("   the chip reported no JRX links")
        return

    for link in jrx:
        buckets = {LANE_GOOD: [], LANE_IDLE: [], LANE_STALLED: []}
        for index in sorted(link["lanes"]):
            buckets[classify_lane(link["lanes"][index])].append(index)

        wanted = link["lanes_wanted"]
        good = len(buckets[LANE_GOOD])
        stalled = buckets[LANE_STALLED]
        user_ok = link["user"] is not None and "fail" not in link["user"].lower()
        lanes_ok = wanted is None or good == wanted

        print()
        print(f"   {link['name']}   {link['params']}")
        print(f"      user status   {link['user'] or '(not reported)'}")
        counts = f"{good} good"
        if buckets[LANE_IDLE]:
            counts += f", {len(buckets[LANE_IDLE])} parked (unused by this config)"
        if stalled:
            counts += f", {len(stalled)} stalled"
        if wanted is not None:
            counts += f"   [config needs {wanted}]"
        print(f"      lanes         {counts}")

        for index in stalled:
            name = f"{link['side']}{index}"
            print(f"      {name:<13} {link['lanes'][index]}   <-- LANE FAULT")
            problems.append(
                f"lane {name} stalled in '{link['lanes'][index]}' on {link['name']}"
            )

        if not link["enabled"]:
            print("      NOTE          link_en is not Enabled")
            problems.append(f"{link['name']} is not enabled")

        if lanes_ok and user_ok and not stalled:
            print("      verdict       OK")
        else:
            if not stalled and not lanes_ok:
                print(
                    f"      verdict       FAIL, only {good} of {wanted} lanes good "
                    "and none report a partial state"
                )
                problems.append(
                    f"{link['name']} has {good} good lanes, config needs {wanted}"
                )
            elif not user_ok and not stalled:
                print("      verdict       FAIL, no lane blamed itself")
                problems.append(f"{link['name']} user status is '{link['user']}'")
            else:
                print("      verdict       FAIL")


def report_chip_jtx(links, rx_core, args, problems):
    """Report the chip -> FPGA direction.

    The chip's framers only publish a summary, so the per-lane detail is taken
    from the FPGA link core that receives them.
    """
    print()
    print("CHIP -> FPGA   chip JTX framers, per-lane state read from the FPGA core")

    for link in [l for l in links if l["direction"] == "JTX"]:
        print()
        print(f"   {link['name']}   {link['params']}")
        for note in link["notes"]:
            print(f"      chip reports  {note}")
        if not link["enabled"]:
            print("      NOTE          link_en is not Enabled")
            problems.append(f"{link['name']} is not enabled")

    if rx_core is None:
        print()
        print("   axi-jesd204-rx not found, no per-lane detail available")
        return

    lanes = parse_fpga_lanes(rx_core)
    if not lanes:
        print()
        print("   axi-jesd204-rx exposes no per-lane counters")
        return

    later = None
    if args.recheck > 0:
        print()
        print(f"   sampling lane error counters over {args.recheck:g} s ...")
        time.sleep(args.recheck)
        later = parse_fpga_lanes(rx_core)

    print()
    print(f"   axi-jesd204-rx, {len(lanes)} lanes")
    print(f"      {'lane':<7}{'errors':>12}  {'growth':>10}  {'alignment':<12}latency")
    for index in sorted(lanes):
        entry = lanes[index]
        growth = ""
        grew = False
        if later and index in later and entry["errors"] is not None:
            delta = later[index]["errors"] - entry["errors"]
            grew = delta > 0
            growth = f"{delta:+d}"
        flag = ""
        if entry["emb"] != EMB_LOCKED:
            flag = "   <-- NOT ALIGNED"
            problems.append(f"FPGA lane {index} alignment is '{entry['emb']}'")
        elif grew:
            flag = "   <-- ERRORS RISING"
            problems.append(f"FPGA lane {index} gained {growth} errors while idle")
        print(
            f"      {index:<7}{entry['errors']:>12}  {growth:>10}  "
            f"{entry['emb']:<12}{entry['latency']}{flag}"
        )

    print()
    print(
        "      A large error total on its own is not a fault: the counters climb\n"
        "      while the link trains and then stop. Growth with no traffic is."
    )
    print(
        "      This core numbers its lanes 0..%d across both sides. The mapping to\n"
        "      the side-A and side-B framers is fixed by the FPGA design and is not\n"
        "      exposed here, so these are not the same numbers as the A/B lanes above."
        % (max(lanes))
    )


def report_core_summary(rx_core, tx_core):
    print()
    print("LINK CORE SUMMARY")
    for label, core in (("axi-jesd204-rx", rx_core), ("axi-jesd204-tx", tx_core)):
        print()
        print(f"   {label}")
        if core is None:
            print("      not present in this context")
            continue
        if "status" not in core.attrs:
            print("      no status attribute")
            continue
        for line in summarize_core_status(core.attrs["status"].value):
            print(f"      {line}")


def main():
    args = parse_args()

    try:
        dev = adi.ad9084(args.uri)
    except Exception as exc:
        raise SystemExit(f"cannot reach the AD9084 at {args.uri}: {exc}")

    print(f"AD9084 JESD204 lane diagnostics -- {args.uri}")
    try:
        print(f"chip {dev.chip_version}, API {dev.api_version}")
    except Exception:
        pass
    print()

    problems = []

    try:
        chip_status = read_debug_attr(dev._rxadc, "status")
    except OSError as exc:
        raise SystemExit(f"cannot read the chip JESD204 status: {exc}")

    links = parse_chip_status(chip_status)
    if not links:
        raise SystemExit("the chip status string held no recognisable links")

    ctx = dev._ctx
    rx_core = find_by_label(ctx, "axi-jesd204-rx")
    tx_core = find_by_label(ctx, "axi-jesd204-tx")

    report_chip_jrx(links, problems)
    report_chip_jtx(links, rx_core, args, problems)
    report_core_summary(rx_core, tx_core)

    if args.raw:
        print()
        print("RAW  chip status")
        for line in chip_status.splitlines():
            print(f"   {line}")
        for label, core in (("axi-jesd204-rx", rx_core), ("axi-jesd204-tx", tx_core)):
            if core is None or "status" not in core.attrs:
                continue
            print()
            print(f"RAW  {label} status")
            for line in core.attrs["status"].value.splitlines():
                print(f"   {line}")

    print()
    if problems:
        print(f"RESULT   {len(problems)} problem(s) found")
        for item in problems:
            print(f"   - {item}")
        return 1

    print("RESULT   all links healthy, every configured lane good and aligned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
