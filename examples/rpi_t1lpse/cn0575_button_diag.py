# Copyright (C) 2023 Analog Devices Inc.
#
# SPDX short identifier: ADIBSD

"""Diagnostic: poll both CN0575 buttons continuously.

Read-only on the buttons (no LED writes at all, so LED cross-mapping
cannot mask anything). Reads each button two ways and prints both:
  1) via the adi public API  (cn0575.button -> gpios.gpio_ext_btn descriptor)
  2) via direct libiio channel access (bypasses the descriptor entirely)

Run it, then press button A, release, press button B, release.
Watch which columns ever change from 0 to 1.
"""

import argparse
from time import sleep

import adi

print("adi path: " + str(adi.__file__))

parser = argparse.ArgumentParser(description="CN0575 button polling diagnostic")
parser.add_argument("--my_cn0575a_u", default="ip:192.168.10.2")
parser.add_argument("--my_cn0575b_u", default="ip:192.168.10.130")
args = parser.parse_args()

a = adi.cn0575(uri=args.my_cn0575a_u)
b = adi.cn0575(uri=args.my_cn0575b_u)

# Grab direct channel handles that bypass the shared class descriptor.
a_btn_chan = a.gpios._ctrl.find_channel("voltage0", False)
b_btn_chan = b.gpios._ctrl.find_channel("voltage0", False)

print("Press button A, then button B. Ctrl-C to stop.")
print(f"{'A.button':>10} {'A.direct':>10} {'B.button':>10} {'B.direct':>10}")

while True:
    a_api = a.button
    b_api = b.button
    a_dir = a_btn_chan.attrs["raw"].value
    b_dir = b_btn_chan.attrs["raw"].value
    print(f"{a_api:>10} {a_dir:>10} {b_api:>10} {b_dir:>10}")
    sleep(0.1)
