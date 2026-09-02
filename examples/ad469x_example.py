# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# ad4695.c family example (ad4695/96/97/98): has offset, calibscale, calibbias
dev = adi.ad469x(uri="ip:analog", device_name="ad4696")

# ad4691.c family example (ad4691/92/93/94): has oversampling_ratio, sampling_frequency
# dev = adi.ad469x(uri="ip:analog", device_name="ad4692")

ad_channel = 0

# Buffered read
dev.rx_enabled_channels = [ad_channel]
dev.rx_buffer_size = 100
dev.rx_output_type = "SI"

data = dev.rx()
print(f"Voltage ch{ad_channel}: {data}")

# Per-channel attributes common to all parts
ch = dev.channel[ad_channel]
print(f"  raw:   {ch.raw}")
print(f"  scale: {ch.scale}")

# ad4695.c family specific attributes
if hasattr(ch, "offset"):
    print(f"  offset: {ch.offset}")
if hasattr(ch, "calibscale"):
    print(f"  calibscale: {ch.calibscale}")
if hasattr(ch, "calibbias"):
    print(f"  calibbias: {ch.calibbias}")

# ad4691.c family specific attributes
if hasattr(ch, "sampling_frequency"):
    print(f"  sampling_frequency: {ch.sampling_frequency} Hz")
    ch.sampling_frequency = 500000
    print(f"  sampling_frequency set to: {ch.sampling_frequency} Hz")
if hasattr(ch, "oversampling_ratio"):
    print(f"  oversampling_ratio: {ch.oversampling_ratio}")
