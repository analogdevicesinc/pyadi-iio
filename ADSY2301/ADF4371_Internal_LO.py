# ==========================================================================
# ADSY2301 — On-Board LO PLL Configuration (ADF4371)
# --------------------------------------------------------------------------
# Configures the ADF4371 frequency synthesizer on the ADSY2301 board to
# generate the local oscillator signal used by the ADXUD1AEBZ
# up/down-converter.
#
# Adjust `rf16_frequency` below to set the desired LO frequency.
#   - rf16_enable = True  → RF1 output (8 GHz to 16 GHz)
#   - rf16_enable = False → RF2 output (16 GHz to 32 GHz)
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import adi

url = "ip:192.168.1.1"  # IP address of the ADRV9009-ZU11EG SoM

# Setup ADF4371 PLL for local oscillator generation
ADF4371 = adi.adf4371(uri=url, device_name="adf4371-0")
ADF4371.rf16_enable = True             # True: RF1 (8-16 GHz), False: RF2 (16-32 GHz)
ADF4371.rf16_frequency = int(14.49e9)  # LO frequency in Hz