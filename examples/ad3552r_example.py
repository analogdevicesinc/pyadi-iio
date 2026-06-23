# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Set up AD3552R
dev = adi.ad3552r("ip:analog", "ad3552r")

print("raw output cleanup ...")
dev.voltage0.raw = 0
dev.voltage1.raw = 0
print("current ch 0: " + str(dev.voltage0.raw))
print("current ch 1: " + str(dev.voltage1.raw))

for ch_num in (0, 1):
    ad3552r_chan = dev.channel[ch_num]
    print("channel: " + str(ch_num))
    print("writing raw: 100")
    ad3552r_chan.raw = 100
    print("reading raw:", end=" ")
    print(ad3552r_chan.raw)
    print("reading offset:", end=" ")
    print(ad3552r_chan.offset)
    print("reading scale:", end=" ")
    print(ad3552r_chan.scale)

print("setting ch 0 and 1 respectively as 10 and 30 ...")
dev.voltage0.raw = 10
dev.voltage1.raw = 30
print("current ch 0 raw: " + str(dev.voltage0.raw))
print("current ch 1 raw: " + str(dev.voltage1.raw))
