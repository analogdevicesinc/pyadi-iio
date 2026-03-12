#!/usr/bin/env python3
# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
Example script for adi_spi_template driver.
Writes value 0x67 to register address 0x0254.
"""

import adi

# Connect to target (adjust IP address as needed)
dev = adi.adi_spi_template(uri="ip:the_ip_of_the_zcu102")

# Write 0x67 to register 0x0254
dev.reg_write(0x0254, 0x67)
print("Wrote 0x67 to register 0x0254")

# Read back to verify
val = dev.reg_read(0x0254)
print(f"Read back: 0x{val:02X}")

if val == 0x67:
    print("SUCCESS: Write verified!")
else:
    print(f"WARNING: Expected 0x67, got 0x{val:02X}")
