# Copyright (C) 2024-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""GTY SerDes PRBS test for the QSFP lanes on Washington (apollo_som_vu11p).

Requires a bitstream built with XCVR_ETH_PRBS=1, which drives the QSFP quad from
util_adxcvr instead of an Ethernet MAC. That is what makes the test possible at
all: the Ethernet MAC IPs expose only DRP and gt_loopback_in, and on GTY the PRBS
pattern is selectable by port, never over DRP. It cannot coexist with CORUNDUM=1,
so a bitstream built for this test has no working Ethernet.

The test runs in internal near-end PMA loopback: each GT loops its own serialised
PRBS back into its receiver, inside the transceiver, so it needs no QSFP loopback
module and no link partner. That covers the PRBS generator and checker, the
serializer, deserializer and CDR at the line rate, but not the package, board
channel or connector -- for those, set LOOPBACK = GtDebugGpio.NORMAL and fit a
QSFP loopback module.

The lane rate is 25.78125 Gb/s, the real CAUI-4 rate, reached from the board's
156.25 MHz reference through the QPLL fractional divider (N = 82.5). It is baked
into the bitstream and the driver never reprograms it: adi,sys-clk-select is
deliberately not XCVR_CPLL, so adxcvr_enforce_settings() returns early. That
matters, because xilinx_xcvr_calc_qpll_config() models QPLL as integer-N only and
would reject this rate.
"""
import time

from adi.adxcvr import adxcvr
from adi.gt_debug_gpio import GtDebugGpio

IP = "ip:10.48.65.198"
PRBS = adxcvr.PRBS_31
NUM_OF_LANES = 4

# Physical address of axi_eth_xcvr_gpio, used to identify its gpiochip by label.
# Must match the offset assigned in projects/apollo_som_vu11p/system_bd.tcl and
# the device tree node.
GPIO_BASE = 0x883B0000
MEASURE_SECONDS = 1 * 60
# Interval between progress lines. Set MEASURE_SECONDS to 0 to run until Ctrl-C.
UPDATE_SECONDS = 5




# Internal loopback modes are NEAR_END_PMA (recommended: covers the SerDes and
# CDR) and NEAR_END_PCS (loops before the serializer, so it only proves the PRBS
# logic itself). FAR_END_* loop received data back out and need a partner.
LOOPBACK = GtDebugGpio.NEAR_END_PMA

rx = adxcvr(IP, "axi-adxcvr-eth-rx")
tx = adxcvr(IP, "axi-adxcvr-eth-tx")

print(f"GT type       : {rx.gt_type_name}")
print(f"lanes (rx/tx) : {rx.num_lanes}/{tx.num_lanes}")
if rx.num_lanes != NUM_OF_LANES:
    print(
        f"  warning: expected {NUM_OF_LANES} lanes, "
        f"bitstream reports {rx.num_lanes}"
    )

gpio = None
if LOOPBACK != GtDebugGpio.NORMAL:
    gpio = GtDebugGpio(rx.fs, GPIO_BASE, NUM_OF_LANES)
    gpio.set_loopback(LOOPBACK)
    # No readback: gpioget would re-request these lines as inputs, which
    # tri-states the axi_gpio outputs and drops the loopback setting.
    print(f"loopback      : {GtDebugGpio.mode_name(LOOPBACK)} "
          f"(0b{LOOPBACK:03b}) on all {NUM_OF_LANES} lanes via {gpio.chip}")


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
print("Ethernet is not present in this bitstream, so nothing needs restoring.")
