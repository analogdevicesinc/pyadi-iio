#!/usr/bin/env python3
# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""
Example script for adi_spi_template driver.
Usage: python3 adi_spi_template_example.py <address> <data>
  address: 15-bit register address (e.g., 0x0254)
  data:    8-bit value to write (e.g., 0x67)
"""

import sys

import adi

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <address> <data>")
    print(f"  address: 15-bit register address (0x0000 - 0x7FFF)")
    print(f"  data:    8-bit value (0x00 - 0xFF)")
    print(f"Example: {sys.argv[0]} 0x0254 0x67")
    sys.exit(1)

addr = int(sys.argv[1], 0)
data = int(sys.argv[2], 0)

if addr > 0x7FFF:
    print(f"Error: address 0x{addr:04X} exceeds 15-bit range (max 0x7FFF)")
    sys.exit(1)

if data > 0xFF:
    print(f"Error: data 0x{data:X} exceeds 8-bit range (max 0xFF)")
    sys.exit(1)

dev = adi.adi_spi_template(uri="ip:10.48.65.246")

dev.reg_write(addr, data)
print(f"Wrote 0x{data:02X} to register 0x{addr:04X}")

val = dev.reg_read(addr)
print(f"Read back: 0x{val:02X}")
