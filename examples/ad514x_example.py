# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import argparse

import adi


def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="AD514X Example Script")
    parser.add_argument(
        "--uri",
        type=str,
        default="serial:COM13,230400",
        help="URI for connecting to the AD514X device",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="AD5144",
        help="Device name (AD5141, AD5142, AD5142A, AD5143, AD5144)",
    )
    args = parser.parse_args()

    # Create device instance
    ad514x_dev = adi.ad514x(uri=args.uri, device_name=args.device)

    print(f"Connected to {args.device}")

    # Display channel information
    print(f"Number of channels: {len(ad514x_dev.channel)}")

    # Use channel 0 for examples
    chn = 0
    print(f"Working with Channel {chn}")

    # Example 1: Basic read/write operations
    print("\n1. Basic RDAC Read/Write:")
    ad514x_dev.channel[chn].raw = 100
    print(f"   Reading raw after writing: {ad514x_dev.channel[chn].raw}")

    # Example 2: Copy RDAC to EEPROM
    test_value = 150
    print("\n2. Copy RDAC to EEPROM:")
    print(f"   Write to RDAC: {test_value}")
    ad514x_dev.channel[chn].raw = test_value
    print(f"   RDAC value: {ad514x_dev.channel[chn].raw}")
    print(f"   EEPROM value before copy: {ad514x_dev.channel[chn].eeprom_value}")
    print(f"   Execute copy RDAC to EEPROM...")
    ad514x_dev.channel[chn].copy_rdac_to_eeprom = "enable"
    print(f"   Read EEPROM value: {ad514x_dev.channel[chn].eeprom_value}")

    # Example 3: SW LRDAC (Input Register to RDAC)
    input_value = 200
    print("\n3. SW LRDAC (Load DAC from Input Register):")
    print(f"   Write to input register: {input_value}")
    ad514x_dev.channel[chn].input_reg_val = input_value
    print(f"   Input register value: {ad514x_dev.channel[chn].input_reg_val}")
    print(f"   RDAC (raw) value before LRDAC: {ad514x_dev.channel[chn].raw}")
    print(f"   Execute SW LRDAC...")
    ad514x_dev.channel[chn].sw_lrdac = "enable"
    print(f"   Read RDAC value: {ad514x_dev.channel[chn].raw}")


if __name__ == "__main__":
    main()
