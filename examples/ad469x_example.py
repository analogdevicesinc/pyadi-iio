# Copyright (C) 2022-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import adi

# Works with both the ad4695.c family (ad4695/96/97/98) and the
# ad4691.c family (ad4691/92/93/94). Pass device_name to select a
# specific part; defaults to "ad4696" when omitted.

# ad4695.c family example (has offset, calibscale, calibbias)
dev = adi.ad469x(uri="ip:analog", device_name="ad4696")

# ad4691.c family example (no offset; has oversampling_ratio)
# dev = adi.ad469x(uri="ip:analog", device_name="ad4692")

ad_channel = 0

# Buffered read
dev.rx_enabled_channels = [ad_channel]
dev.rx_buffer_size = 100
dev.rx_output_type = "SI"

data = dev.rx()
print(f"Voltage ch{ad_channel}: {data}")

# Per-channel attributes (common to all parts)
ch = dev.channel[ad_channel]
print(f"  raw:   {ch.raw}")
print(f"  scale: {ch.scale}")

# offset: present on ad4695.c family, returns '0' on ad4691.c family
print(f"  offset: {ch.offset}")

# oversampling_ratio: present when the operating mode supports it,
# None otherwise
if ch.oversampling_ratio is not None:
    print(f"  oversampling_ratio: {ch.oversampling_ratio}")

# sampling_frequency: present when the operating mode supports it,
# None otherwise
if ch.sampling_frequency is not None:
    print(f"  sampling_frequency: {ch.sampling_frequency} Hz")
    ch.sampling_frequency = 500000
    print(f"  sampling_frequency set to: {ch.sampling_frequency} Hz")

# calibscale / calibbias: ad4695.c family only, None on ad4691.c family
if ch.calibscale is not None:
    print(f"  calibscale: {ch.calibscale}")
if ch.calibbias is not None:
    print(f"  calibbias: {ch.calibbias}")
