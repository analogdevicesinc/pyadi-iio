# Copyright (C) 2023 Analog Devices Inc.
#
# SPDX short identifier: ADIBSD

"""Diagnostic: exercise ONE CN0575 in isolation, both directions.

- Reads the button via direct libiio (bypasses pyadi descriptors).
- Every ~1s, toggles the LED so you can watch it physically blink.

Use this on the suspect board (e.g. ip:10.87.54.201) with nothing else
connected. If the LED blinks but the button never reads 1 while pressed,
the button INPUT path on that board is the problem (hardware / wiring /
device-tree), not pyadi.
"""

import argparse
from time import sleep

import adi

print("adi path: " + str(adi.__file__))

parser = argparse.ArgumentParser(description="Single CN0575 diagnostic")
parser.add_argument("--uri", default="ip:192.168.10.2")
args = parser.parse_args()

dev = adi.cn0575(uri=args.uri)
btn_chan = dev.gpios._ctrl.find_channel("voltage0", False)  # input, direct

print(f"Testing {args.uri}. Press the button; watch the LED toggle. Ctrl-C to stop.")
print(f"{'btn.api':>9} {'btn.direct':>11} {'led.set':>9}")

led = 0
i = 0
while True:
    if i % 10 == 0:  # toggle LED once per second
        led ^= 1
        dev.led = led
    btn_api = dev.button
    btn_dir = btn_chan.attrs["raw"].value
    print(f"{btn_api:>9} {btn_dir:>11} {led:>9}")
    i += 1
    sleep(0.1)
