# Copyright (C) 2023 Analog Devices Inc.
#
# SPDX short identifier: ADIBSD

"""Diagnostic: dump the GPIO channel map of two CN0575 contexts.

Read-only. Does NOT write to any GPIO/LED. It only enumerates channels.

Why: the class-level descriptors in one_bit_adc_dac bake in each channel's
id/output. Whichever board is constructed last overwrites those class
attributes for ALL instances. If the two boards enumerate channels
identically, this is harmless (works). If they differ, one board routes
through the other's channel id and stops responding. This dump reveals
which case you are in.
"""

import argparse

import adi

print("adi path: " + str(adi.__file__))

parser = argparse.ArgumentParser(description="CN0575 channel-map diagnostic")
parser.add_argument("--my_cn0575a_u", default="ip:192.168.10.2")
parser.add_argument("--my_cn0575b_u", default="ip:192.168.10.130")
args = parser.parse_args()


def dump(label, uri):
    gpios = adi.one_bit_adc_dac(uri)
    ctrl = gpios._ctrl
    print(f"\n=== {label} ({uri}) ===")
    print(f"ctrl device name: {ctrl.name}")
    for chan in ctrl.channels:
        lbl = chan.attrs["label"].value if "label" in chan.attrs else "<no label>"
        print(f"  id={chan.id!r:12} output={chan.output!s:5} label={lbl!r}")


dump("Board A", args.my_cn0575a_u)
dump("Board B", args.my_cn0575b_u)
