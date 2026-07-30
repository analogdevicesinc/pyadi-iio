# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse

import adi

parser = argparse.ArgumentParser(description="LTC2984 / ADT7604 Example Script")
parser.add_argument(
    "-u",
    default=["ip:analog.local"],
    help="-u (arg) URI of target device's context, eg: 'ip:analog.local',\
    'ip:192.168.2.1',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
parser.add_argument(
    "-d",
    "--device",
    default="ltc2984",
    choices=["ltc2984", "adt7604", "ltc2983"],
    help="Device to instantiate (default: ltc2984)",
)
args = parser.parse_args()
my_uri = args.u[0]

print("uri: " + str(my_uri))
print("device: " + args.device)

# Instantiate the correct device class
device_map = {
    "ltc2984": adi.ltc2984,
    "adt7604": adi.adt7604,
    "ltc2983": adi.ltc2983,
}
my_dev = device_map[args.device](uri=my_uri)

# The LTC2983 family exposes temperature channels (temp0, temp1, ...)
# via the IIO subsystem. Each channel is an ltc2983._channel instance
# with raw, scale, and value attributes. Channels are accessible by
# name: my_dev.channel["temp0"], my_dev.channel["temp1"], etc.

print(f"\nFound {len(my_dev.channel)} channels:")

print("\n--- Temperature Channels ---")
for ch_name, ch in my_dev.channel.items():
    print(f"\n  {ch_name}")
    print(f"    raw:   {ch.raw}")
    print(f"    scale: {ch.scale}")
    print(f"    value: {ch.value:.3f} milli-degrees C")

# del my_dev
