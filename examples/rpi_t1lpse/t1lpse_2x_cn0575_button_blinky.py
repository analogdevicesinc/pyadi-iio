# Copyright (C) 2023 Analog Devices Inc.
#
# SPDX short identifier: ADIBSD

import argparse
from time import sleep

import adi

print("adi path: " + str(adi.__file__))

# Optionally pass URIs as command line arguments,
# else use defaults to "ip:192.168.10.2" and "ip:192.168.10.130"
parser = argparse.ArgumentParser(description="CN0575 2x Button Blinky Example Script")
parser.add_argument(
    "--my_cn0575a_u",
    default=["ip:192.168.10.2"],
    help="--my_cn0575a_u (arg) URI of first CN0575 device's context, eg: 'ip:192.168.10.2',\
    'ip:analog.local',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
parser.add_argument(
    "--my_cn0575b_u",
    default=["ip:192.168.10.130"],
    help="--my_cn0575b_u (arg) URI of second CN0575 device's context, eg: 'ip:192.168.10.130',\
    'ip:analog.local',\
    'serial:COM4,115200,8n1n'",
    action="store",
    nargs="*",
)
args = parser.parse_args()
my_cn0575a_uri = args.my_cn0575a_u[0]
my_cn0575b_uri = args.my_cn0575b_u[0]

print("my_cn0575a uri: " + str(my_cn0575a_uri))
print("my_cn0575b uri: " + str(my_cn0575b_uri))

my_cn0575a = adi.cn0575(uri=my_cn0575a_uri)
my_cn0575b = adi.cn0575(uri=my_cn0575b_uri)

while True:
    btn_a = my_cn0575b.button
    btn_b = my_cn0575a.button

    print(f"Button A: {btn_a}, Button B: {btn_b}")

    my_cn0575a.led = btn_a
    my_cn0575b.led = btn_b

    sleep(0.1)
