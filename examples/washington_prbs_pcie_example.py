# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""GTY SerDes PRBS test for the PCIe lanes on Washington (apollo_som_vu11p).

Requires a bitstream built with XCVR_PRBS=1, which enables the PCIe core's
transceiver-debug ports and attaches them to two axi_adxcvr instances through
util_xcvr_prbs.

The test runs in internal near-end PMA loopback: each GT loops its own
serialised PRBS back into its receiver, inside the transceiver. That covers the
PRBS generator and checker, serializer, deserializer and CDR at the current
line rate, and needs no link partner and no loopback plug. It does not cover
the package, board channel or connector -- for that, set
LOOPBACK = GtDebugGpio.NORMAL and provide an external loopback or a partner.

Selecting a PRBS pattern replaces the PCS data on the lane, so the PCIe link
goes down for the duration of the test and the host needs a rescan (or a
reboot) afterwards. Run this over the network control path, never over PCIe.

Loopback and TXINHIBIT are driven through the axi_pcie_xcvr_gpio gpiochip, so the
target needs that device tree node (gpio-xilinx) and libgpiod installed.

TX_INHIBIT asserts TXINHIBIT on every lane, which blocks transmission of TXDATA
and forces GTYTXP high and GTYTXN low. That keeps the PRBS pattern off the serial
pins while it is looped back internally, which matters when a host is still
connected -- but because it blocks the transmit data rather than only muting the
output stage, it may also blank what near-end PMA loopback feeds back to the
receiver. It therefore defaults to off. If you enable it and the error-injection
check below stops firing, the loopback path is being blanked and it must stay
off; only the TX pins, not the PRBS test, benefit from it.

The PCIe LTSSM owns the GT line rate and this design does not expose
gt_txrate/gt_rxrate, so PRBS runs at whatever rate the core last settled on --
2.5 GT/s (Gen1) when the link never trained. This is a connectivity and gross
fault test, not a Gen3 margin measurement.
"""

import time

from adi.adxcvr import adxcvr
from adi.gt_debug_gpio import GtDebugGpio

IP = "ip:10.48.65.198"
PRBS = adxcvr.PRBS_31
NUM_OF_LANES = 8
MEASURE_SECONDS = 1 * 60
# Interval between progress lines. Set MEASURE_SECONDS to 0 to run until Ctrl-C.
UPDATE_SECONDS = 5

# Physical address of axi_pcie_xcvr_gpio, used to identify its gpiochip by
# label. Must match the offset assigned in
# projects/apollo_som_vu11p/system_bd.tcl and the device tree node.
GPIO_BASE = 0x88380000


# Internal loopback modes are NEAR_END_PMA (recommended: covers the SerDes and
# CDR) and NEAR_END_PCS (loops before the serializer, so it only proves the PRBS
# logic itself). FAR_END_* loop received data back out and need a partner.
LOOPBACK = GtDebugGpio.NEAR_END_PMA
TX_INHIBIT = True

rx = adxcvr(IP, "axi-adxcvr-pcie-rx")
tx = adxcvr(IP, "axi-adxcvr-pcie-tx")

print(f"GT type       : {rx.gt_type_name}")
print(f"lanes (rx/tx) : {rx.num_lanes}/{tx.num_lanes}")
if rx.num_lanes != NUM_OF_LANES:
    print(
        f"  warning: expected {NUM_OF_LANES} lanes, "
        f"bitstream reports {rx.num_lanes}"
    )

gpio = None
if LOOPBACK != GtDebugGpio.NORMAL or TX_INHIBIT:
    gpio = GtDebugGpio(rx.fs, GPIO_BASE, NUM_OF_LANES)
    gpio.set_loopback(LOOPBACK)
    gpio.set_txinhibit(TX_INHIBIT)
    # No readback: gpioget would re-request these lines as inputs, which
    # tri-states the axi_gpio outputs and drops the loopback setting.
    print(f"loopback      : {GtDebugGpio.mode_name(LOOPBACK)} "
          f"(0b{LOOPBACK:03b}) on all {NUM_OF_LANES} lanes via {gpio.chip}")
    print(f"tx inhibit    : {TX_INHIBIT}")

# --- Enable PRBS on both ends of the loop -----------------------------------
# The TX generator must be running before the RX checker can lock.
tx.prbs_select = PRBS
rx.prbs_select = PRBS

time.sleep(1)
rx.reset_prbs_counters()

# --- Monitor ----------------------------------------------------------------
lane_header = "".join(f"{'L' + str(n):>9}" for n in range(NUM_OF_LANES))
duration = f"{MEASURE_SECONDS}s total" if MEASURE_SECONDS else "until Ctrl-C"
print()
print(f"=== PRBS-{PRBS}, sampling every {UPDATE_SECONDS}s, {duration} ===")
print(f"{'t':>7}  {'status':<8}{lane_header}")

status = "unknown"
errors = [0] * NUM_OF_LANES
started = time.monotonic()

try:
    while True:
        time.sleep(UPDATE_SECONDS)
        elapsed = time.monotonic() - started
        previous = errors
        status = rx.prbs_status
        errors = rx.prbs_error_counters

        counts = "".join(f"{count:>9}" for count in errors)
        print(f"{elapsed:>6.0f}s  {status:<8}{counts}")

        grew = [
            f"L{lane} +{errors[lane] - previous[lane]}"
            for lane in range(min(len(errors), len(previous)))
            if errors[lane] > previous[lane]
        ]
        if grew:
            print(f"{'':>7}  new errors: {', '.join(grew)}")

        if MEASURE_SECONDS and elapsed >= MEASURE_SECONDS:
            break
except KeyboardInterrupt:
    print()
    print("interrupted -- restoring the lanes")

# --- Summary ----------------------------------------------------------------
errors_drp = rx.prbs_error_counts_drp()

print()
print(f"=== final, checker status: {status} ===")
print(f"{'lane':>4}  {'errors':>12}  {'errors (drp)':>12}  result")
for lane in range(len(errors)):
    drp = errors_drp[lane] if lane < len(errors_drp) else "-"
    verdict = "OK" if errors[lane] == 0 else "ERRORS"
    print(f"{lane:>4}  {errors[lane]:>12}  {drp:>12}  {verdict}")

clean = status == "valid" and all(count == 0 for count in errors)

# --- Prove the checker is actually looking at the data ----------------------
# A forced TX error must show up in the counters; if it does not, the lane was
# never really locked and the zero counts above mean nothing.
try:
    tx.inject_prbs_error()
    time.sleep(0.5)
    injected = rx.prbs_error_counters
    status_injected = rx.prbs_status
    lanes = range(min(len(injected), len(errors)))
    detected = any(injected[lane] > errors[lane] for lane in lanes)

    print()
    print(f"=== after error injection, checker status: {status_injected} ===")
    print(f"{'lane':>4}  {'before':>12}  {'after':>12}  {'delta':>8}")
    for lane in lanes:
        delta = injected[lane] - errors[lane]
        print(f"{lane:>4}  {errors[lane]:>12}  {injected[lane]:>12}  {delta:>+8}")
    print()
    print(f"injected error detected: {detected}")
finally:
    rx.prbs_select = adxcvr.PRBS_OFF
    tx.prbs_select = adxcvr.PRBS_OFF
    if gpio is not None:
        gpio.set_txinhibit(False)
        gpio.set_loopback(GtDebugGpio.NORMAL)

print()
if clean and detected:
    print("PASS: all lanes locked with zero errors, and error injection was seen")
elif not detected:
    print(
        "FAIL: error injection was not detected -- the checker never locked, "
        "so the error counts above are not meaningful"
    )
else:
    print("FAIL: PRBS errors on at least one lane")

print()
print("The PCIe link was taken down by this test; rescan or reboot the host.")
