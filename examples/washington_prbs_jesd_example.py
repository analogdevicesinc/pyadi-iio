# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""JESD SerDes PRBS test for Washington (apollo_som_vu11p / ADSY1100).

Both ends of each JESD lane must be in PRBS mode simultaneously:
  - FPGA GTY TX sends PRBS -> Apollo JRx checker (bist_prbs_select_jrx)
  - Apollo JTx sends PRBS  -> FPGA GTY RX checker (rx_a/rx_b prbs_select)

There is no internal loopback here: the external loopbacks connect FPGA TX to
Apollo JRx and Apollo JTx to FPGA RX. Because the Apollo PCS re-encodes data, raw
PRBS only survives if both ends agree on the polynomial.

Three checker groups are reported:
  gty-rx-a / gty-rx-b   FPGA GTY RX checkers, fed by the Apollo JTx generators
  apollo-jrx            Apollo JRx checkers, fed by the FPGA GTY TX generators

The FPGA RX checkers cannot be verified by error injection: apollo_serdes exposes
no force-error control, so nothing can deliberately corrupt what they receive.
They are reported as untested rather than counted as a pass.

This takes the JESD links down for the duration; re-initialise them afterwards.
"""

import time

from adi.adxcvr import adxcvr
from adi.apollo_serdes import apollo_serdes

IP = "ip:10.48.65.198"
PRBS = adxcvr.PRBS_7
NUM_OF_LANES = 12
MEASURE_SECONDS = 1 * 60
# Interval between progress lines. Set MEASURE_SECONDS to 0 to run until Ctrl-C.
UPDATE_SECONDS = 5

rx_a = adxcvr(IP, "axi-adxcvr-rx")
tx_a = adxcvr(IP, "axi-adxcvr-tx")
rx_b = adxcvr(IP, "axi-adxcvr-rx-b")
tx_b = adxcvr(IP, "axi-adxcvr-tx-b")
apollo = apollo_serdes(IP)

print(f"GT type       : {rx_a.gt_type_name}")
print(f"lanes (a/b)   : {rx_a.num_lanes}/{rx_b.num_lanes}")
if rx_a.num_lanes != NUM_OF_LANES:
    print(
        f"  warning: expected {NUM_OF_LANES} lanes per side, "
        f"bitstream reports {rx_a.num_lanes}"
    )
print("loopback      : external (FPGA TX -> Apollo JRx, Apollo JTx -> FPGA RX)")


def sample_adxcvr(dev):
    return dev.prbs_status, {
        f"L{lane}": count for lane, count in enumerate(dev.prbs_error_counters)
    }


def sample_apollo(dev):
    counts = {}
    sticky = False
    for entry in dev.prbs_error_counters_jrx:
        counts[f"{entry['side']}{entry['lane']}"] = entry["err_count"]
        sticky = sticky or bool(entry["err_sticky"])
    # The Apollo BIST exposes no lock flag, only a sticky error bit.
    return ("sticky" if sticky else "clean"), counts


# injectors is empty where nothing can force an error into that checker's feed.
GROUPS = [
    ("gty-rx-a", lambda: sample_adxcvr(rx_a), rx_a, []),
    ("gty-rx-b", lambda: sample_adxcvr(rx_b), rx_b, []),
    ("apollo-jrx", lambda: sample_apollo(apollo), None, [tx_a, tx_b]),
]

try:
    # Generators before checkers: a checker armed first latches errors from the
    # idle line.
    tx_a.prbs_select = PRBS
    tx_b.prbs_select = PRBS
    apollo.prbs_select_jtx = PRBS
    rx_a.prbs_select = PRBS
    rx_b.prbs_select = PRBS
    apollo.prbs_select_jrx = PRBS

    time.sleep(1)
    rx_a.reset_prbs_counters()
    rx_b.reset_prbs_counters()

    width = max(len(name) for name, _, _, _ in GROUPS)
    duration = f"{MEASURE_SECONDS}s total" if MEASURE_SECONDS else "until Ctrl-C"
    print()
    print(f"=== PRBS-{PRBS}, sampling every {UPDATE_SECONDS}s, {duration} ===")
    print(f"{'t':>6}  {'group':<{width}}  {'status':<8}  "
          f"{'lanes':>5}  {'errors':>12}  detail")

    state = {name: ("unknown", {}) for name, _, _, _ in GROUPS}
    started = time.monotonic()
    try:
        while True:
            time.sleep(UPDATE_SECONDS)
            elapsed = time.monotonic() - started
            for name, sample, _, _ in GROUPS:
                previous = state[name][1]
                status, counts = sample()
                state[name] = (status, counts)
                total = sum(counts.values())
                grew = [
                    f"{label} +{count - previous.get(label, 0)}"
                    for label, count in counts.items()
                    if count > previous.get(label, 0)
                ]
                bad = [label for label, count in counts.items() if count]
                if grew:
                    detail = ", ".join(grew[:6]) + (" ..." if len(grew) > 6 else "")
                elif bad:
                    detail = f"{len(bad)} lane(s) with errors, no change"
                else:
                    detail = "-"
                print(f"{elapsed:>5.0f}s  {name:<{width}}  {status:<8}  "
                      f"{len(counts):>5}  {total:>12}  {detail}", flush=True)
            print(f"{'':>5}   {'-' * (width + 40)}", flush=True)
            if MEASURE_SECONDS and elapsed >= MEASURE_SECONDS:
                break
    except KeyboardInterrupt:
        print()
        print("interrupted")

    # --- Per-lane summary ----------------------------------------------------
    for name, _, dev, _ in GROUPS:
        status, counts = state[name]
        drp = {}
        if dev is not None:
            drp = {
                f"L{lane}": count
                for lane, count in enumerate(dev.prbs_error_counts_drp())
            }
        print()
        print(f"=== {name}, checker status: {status} ===")
        print(f"{'lane':>6}  {'errors':>12}  {'errors (drp)':>12}  result")
        for label, count in counts.items():
            verdict = "OK" if count == 0 else "ERRORS"
            print(f"{label:>6}  {count:>12}  {drp.get(label, '-'):>12}  {verdict}")

    clean = all(
        status in ("valid", "clean") and all(c == 0 for c in counts.values())
        for status, counts in state.values()
    )

    # --- Prove the checkers are looking at live data -------------------------
    before = {name: dict(state[name][1]) for name, _, _, _ in GROUPS}
    for _, _, _, injectors in GROUPS:
        for injector in injectors:
            injector.inject_prbs_error()
    time.sleep(0.5)

    print()
    print("=== after error injection ===")
    print(f"{'group':<{width}}  {'lane':>6}  {'before':>12}  "
          f"{'after':>12}  {'delta':>8}")
    detected = {}
    for name, sample, _, injectors in GROUPS:
        _, after = sample()
        if not injectors:
            detected[name] = None
            continue
        grew = False
        for label, count in after.items():
            was = before[name].get(label, 0)
            grew = grew or count > was
            print(f"{name:<{width}}  {label:>6}  {was:>12}  "
                  f"{count:>12}  {count - was:>+8}")
        detected[name] = grew
finally:
    apollo.prbs_select_jrx = apollo_serdes.PRBS_OFF
    apollo.prbs_select_jtx = apollo_serdes.PRBS_OFF
    rx_a.prbs_select = adxcvr.PRBS_OFF
    rx_b.prbs_select = adxcvr.PRBS_OFF
    tx_a.prbs_select = adxcvr.PRBS_OFF
    tx_b.prbs_select = adxcvr.PRBS_OFF

print()
for name, result in detected.items():
    if result is None:
        print(f"{name:<{width}}: injection not applicable "
              "(no force-error on the far-end generator)")
    else:
        print(f"{name:<{width}}: injected error detected: {result}")

unproven = [name for name, result in detected.items() if result is False]

print()
if clean and not unproven:
    print("PASS: zero errors on every lane, and injection was seen where testable")
elif unproven:
    print(f"FAIL: injection not detected on {', '.join(unproven)} -- those "
          "checkers never locked, so their zero counts mean nothing")
else:
    print("FAIL: PRBS errors on at least one lane")

print()
print("The JESD links were taken down by this test; re-initialise them.")
