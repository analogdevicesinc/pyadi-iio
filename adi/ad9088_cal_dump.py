#!/usr/bin/env python3
# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
# SPDX-License-Identifier: GPL-2.0
"""
AD9088 Calibration Data Dump Tool

Copyright 2025 Analog Devices Inc.

Usage: python3 ad9088_cal_dump.py <calibration_file> [SSH OPTIONS]

This tool reads an AD9088 calibration data file and displays:
- Header information (magic, version, chip ID, configuration)
- Section offsets and sizes
- CRC validation
- Calibration data summary

SSH OPTIONS (optional):
  --ssh-pull <ip> <username> <password> <remote_path> [local_path]
    Download calibration file from remote target via SSH
  --ssh-push <ip> <username> <password> <local_path> <remote_path>
    Upload calibration file to remote target via SSH
"""

import argparse
import os
import struct
import sys
import zlib
from pathlib import Path

try:
    import adi.sshfs as sshfs
except ImportError:
    sshfs = None

# Magic number for AD9088 calibration files
AD9088_CAL_MAGIC = 0x41443930  # "AD90"
AD9088_CAL_VERSION = 1

# Chip IDs
CHIPID_AD9084 = 0x9084
CHIPID_AD9088 = 0x9088

# Number of devices
ADI_APOLLO_NUM_ADC_CAL_MODES = 2
ADI_APOLLO_NUM_JRX_SERDES_12PACKS = 4
ADI_APOLLO_NUM_JTX_SERDES_12PACKS = 4


# Calibration file header structure
class AD9088CalHeader:
    """Calibration file header structure"""

    def __init__(self, data):
        """Parse header from binary data"""
        # Parse in sections to handle padding correctly
        offset = 0

        # First 12 bytes: magic, version, chip_id
        self.magic, self.version, self.chip_id = struct.unpack(
            "<III", data[offset : offset + 12]
        )
        offset += 12

        # Next 5 bytes: configuration flags
        (
            self.is_8t8r,
            self.num_adcs,
            self.num_dacs,
            self.num_serdes_rx,
            self.num_serdes_tx,
        ) = struct.unpack("<BBBBB", data[offset : offset + 5])
        offset += 5

        # 3 bytes reserved padding
        offset += 3

        # Offsets (16 bytes)
        (
            self.adc_cal_offset,
            self.dac_cal_offset,
            self.serdes_rx_cal_offset,
            self.serdes_tx_cal_offset,
        ) = struct.unpack("<IIII", data[offset : offset + 16])
        offset += 16

        # Sizes (16 bytes)
        (
            self.adc_cal_size,
            self.dac_cal_size,
            self.serdes_rx_cal_size,
            self.serdes_tx_cal_size,
        ) = struct.unpack("<IIII", data[offset : offset + 16])
        offset += 16

        # Total size
        self.total_size = struct.unpack("<I", data[offset : offset + 4])[0]
        offset += 4

        # 8 bytes reserved (2 uint32s)
        # offset += 8

        self.SIZE = offset


def chip_id_to_string(chip_id):
    """Convert chip ID to string representation"""
    chip_names = {
        CHIPID_AD9084: "AD9084",
        CHIPID_AD9088: "AD9088",
    }
    return chip_names.get(chip_id, "Unknown")


def print_header(hdr):
    """Print header information"""
    print("=== AD9088 Calibration Data Header ===\n")

    # Magic number with ASCII representation
    magic_bytes = struct.pack("<I", hdr.magic)
    magic_chars = "".join(chr(b) if 32 <= b < 127 else "?" for b in magic_bytes)
    magic_status = "[OK]" if hdr.magic == AD9088_CAL_MAGIC else "[INVALID]"
    print(f"Magic Number:        0x{hdr.magic:08X} ('{magic_chars}') {magic_status}")

    version_status = "[OK]" if hdr.version == AD9088_CAL_VERSION else "[UNSUPPORTED]"
    print(f"Version:             {hdr.version} {version_status}")

    chip_name = chip_id_to_string(hdr.chip_id)
    print(f"Chip ID:             0x{hdr.chip_id:04X} ({chip_name})")

    config = "8T8R (8 TX, 8 RX)" if hdr.is_8t8r else "4T4R (4 TX, 4 RX)"
    print(f"Configuration:       {config}")

    print(f"Number of ADCs:      {hdr.num_adcs}")
    print(f"Number of DACs:      {hdr.num_dacs}")
    print(f"Number of SERDES RX: {hdr.num_serdes_rx}")
    print(f"Number of SERDES TX: {hdr.num_serdes_tx}")

    print("\n=== Calibration Sections ===\n")

    print("ADC Calibration:")
    print(f"  Offset: 0x{hdr.adc_cal_offset:08X} ({hdr.adc_cal_offset} bytes)")
    print(f"  Size:   0x{hdr.adc_cal_size:08X} ({hdr.adc_cal_size} bytes)")
    if hdr.num_adcs > 0 and hdr.adc_cal_size > 0:
        per_mode = hdr.adc_cal_size // ADI_APOLLO_NUM_ADC_CAL_MODES
        per_adc = per_mode // hdr.num_adcs
        print(f"  Per Mode: {per_mode} bytes")
        print(f"  Per ADC:  {per_adc} bytes")

    print("\nDAC Calibration:")
    print(f"  Offset: 0x{hdr.dac_cal_offset:08X} ({hdr.dac_cal_offset} bytes)")
    print(f"  Size:   0x{hdr.dac_cal_size:08X} ({hdr.dac_cal_size} bytes)")
    if hdr.num_dacs > 0 and hdr.dac_cal_size > 0:
        per_dac = hdr.dac_cal_size // hdr.num_dacs
        print(f"  Per DAC:  {per_dac} bytes")

    print("\nSERDES RX Calibration:")
    print(
        f"  Offset: 0x{hdr.serdes_rx_cal_offset:08X} ({hdr.serdes_rx_cal_offset} bytes)"
    )
    print(f"  Size:   0x{hdr.serdes_rx_cal_size:08X} ({hdr.serdes_rx_cal_size} bytes)")
    if hdr.num_serdes_rx > 0 and hdr.serdes_rx_cal_size > 0:
        per_serdes = hdr.serdes_rx_cal_size // hdr.num_serdes_rx
        print(f"  Per Pack: {per_serdes} bytes")

    print("\nSERDES TX Calibration:")
    print(
        f"  Offset: 0x{hdr.serdes_tx_cal_offset:08X} ({hdr.serdes_tx_cal_offset} bytes)"
    )
    print(f"  Size:   0x{hdr.serdes_tx_cal_size:08X} ({hdr.serdes_tx_cal_size} bytes)")
    if hdr.num_serdes_tx > 0 and hdr.serdes_tx_cal_size > 0:
        per_serdes = hdr.serdes_tx_cal_size // hdr.num_serdes_tx
        print(f"  Per Pack: {per_serdes} bytes")

    print(f"\nTotal Size:          0x{hdr.total_size:08X} ({hdr.total_size} bytes)")


def print_section_summary(section_name, data, offset, size, num_items, item_name):
    """Print calibration section summary"""
    if size == 0 or num_items == 0:
        print(f"\n=== {section_name}: Empty ===")
        return

    per_item = size // num_items

    print(f"\n=== {section_name} ===")
    print(f"Total size: {size} bytes ({num_items} items × {per_item} bytes)\n")

    # Check for all zeros or all 0xFF (likely uninitialized)
    all_zero = all(b == 0x00 for b in data[:size])
    all_ff = all(b == 0xFF for b in data[:size])

    if all_zero:
        print("WARNING: All data is zero (possibly uninitialized)")
    elif all_ff:
        print("WARNING: All data is 0xFF (possibly uninitialized)")

    # Print first 16 bytes of each item
    for i in range(num_items):
        item_offset = i * per_item
        print(f"{item_name} {i} (offset 0x{offset + item_offset:08X}):")

        bytes_to_show = min(per_item, 16)
        hex_bytes = data[item_offset : item_offset + bytes_to_show]
        hex_str = " ".join(f"{b:02X}" for b in hex_bytes)
        print(f"  {hex_str} ")

        if bytes_to_show < per_item:
            remaining = per_item - bytes_to_show
            print(f"  ... ({remaining} more bytes)")


def validate_and_dump(filename):
    """Validate and dump calibration file"""
    try:
        # Open and read file
        with open(filename, "rb") as fp:
            data = fp.read()

        file_size = len(data)
        # Use just the filename, not the full path
        display_name = Path(filename).name
        print(f"File: {display_name}")
        print(f"Size: {file_size} bytes\n")

        # Check minimum size (header is at least 52 bytes)
        if file_size < 52 + 4:
            print(f"Error: File too small ({file_size} bytes)", file=sys.stderr)
            return 1

        validate_data(data, print_data=True)

    except FileNotFoundError:
        print(f"Error: Cannot open file '{filename}'", file=sys.stderr)
        return 1


def validate_data(data, print_data=False):

    try:

        file_size = len(data)

        # Parse header
        hdr = AD9088CalHeader(data)

        # Validate magic number
        if hdr.magic != AD9088_CAL_MAGIC:
            print(
                f"Error: Invalid magic number 0x{hdr.magic:08X} (expected 0x{AD9088_CAL_MAGIC:08X})",
                file=sys.stderr,
            )
            if print_data:
                print_header(hdr)
            return 1

        # Validate version
        if hdr.version != AD9088_CAL_VERSION:
            print(
                f"Warning: Unsupported version {hdr.version} (expected {AD9088_CAL_VERSION})",
                file=sys.stderr,
            )

        # Validate total size
        if hdr.total_size != file_size:
            print(
                f"Warning: Size mismatch - header says {hdr.total_size}, file is {file_size}",
                file=sys.stderr,
            )

        # Extract and verify CRC
        crc_stored = struct.unpack("<I", data[-4:])[0]
        crc_calc = zlib.crc32(data[:-4]) & 0xFFFFFFFF

        if print_data:
            print("=== CRC Validation ===\n")
            print(f"Stored CRC:     0x{crc_stored:08X}")
            print(f"Calculated CRC: 0x{crc_calc:08X}")
            print(
                f"Status:         {'[OK]' if crc_stored == crc_calc else '[FAILED]'}\n"
            )

        ret = 0
        if crc_stored != crc_calc:
            print("Error: CRC mismatch!", file=sys.stderr)
            ret = 1

        # Print header information
        if print_data:
            print_header(hdr)

        # Print section summaries if CRC is valid
        if crc_stored == crc_calc and ret == 0:
            # ADC calibration
            if hdr.adc_cal_size > 0 and hdr.adc_cal_offset < file_size:
                num_items = hdr.num_adcs * ADI_APOLLO_NUM_ADC_CAL_MODES
                if print_data:
                    print_section_summary(
                        "ADC Calibration Data",
                        data[hdr.adc_cal_offset :],
                        hdr.adc_cal_offset,
                        hdr.adc_cal_size,
                        num_items,
                        "ADC Chan/Mode",
                    )

            # DAC calibration
            if hdr.dac_cal_size > 0 and hdr.dac_cal_offset < file_size:
                if print_data:
                    print_section_summary(
                        "DAC Calibration Data",
                        data[hdr.dac_cal_offset :],
                        hdr.dac_cal_offset,
                        hdr.dac_cal_size,
                        hdr.num_dacs,
                        "DAC",
                    )

            # SERDES RX calibration
            if hdr.serdes_rx_cal_size > 0 and hdr.serdes_rx_cal_offset < file_size:
                if print_data:
                    print_section_summary(
                        "SERDES RX Calibration Data",
                        data[hdr.serdes_rx_cal_offset :],
                        hdr.serdes_rx_cal_offset,
                        hdr.serdes_rx_cal_size,
                        hdr.num_serdes_rx,
                        "SERDES RX Pack",
                    )

            # SERDES TX calibration
            if hdr.serdes_tx_cal_size > 0 and hdr.serdes_tx_cal_offset < file_size:
                if print_data:
                    print_section_summary(
                        "SERDES TX Calibration Data",
                        data[hdr.serdes_tx_cal_offset :],
                        hdr.serdes_tx_cal_offset,
                        hdr.serdes_tx_cal_size,
                        hdr.num_serdes_tx,
                        "SERDES TX Pack",
                    )

        return ret

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def ssh_pull(ip, username, password, remote_path, local_path=None):
    """Download calibration file from remote target via SSH"""
    if sshfs is None:
        print("Error: paramiko module is required for SSH support", file=sys.stderr)
        return 1

    if local_path is None:
        local_path = Path(remote_path).name

    try:
        print(f"Connecting to {ip}...")
        ssh = sshfs.sshfs(ip, username, password)

        if not remote_path:
            # Find calibration_data file in /sys/bus/iio/devices/
            cal_file = None
            for dev in ssh.listdir("/sys/bus/iio/devices/"):
                attr_path = f"/sys/bus/iio/devices/{dev}/calibration_data"
                if ssh.isfile(attr_path):
                    cal_file = attr_path
                    break
            if cal_file is None:
                print(
                    "Error: calibration_data file not found in /sys/bus/iio/devices/",
                    file=sys.stderr,
                )
                return 1
            remote_path = cal_file
            print(f"Found calibration file: {remote_path}")

        print(f"Pulling {remote_path} to {local_path}...")

        # Read file from remote via SSH
        _, stdout, stderr = ssh.ssh.exec_command(f"cat {remote_path}")
        data = stdout.read()

        if not data:
            stderr_msg = stderr.read().decode().strip()
            print(f"Error: Failed to read remote file: {stderr_msg}", file=sys.stderr)
            return 1

        # Write to local file
        with open(local_path, "wb") as fp:
            fp.write(data)

        print(f"Successfully downloaded {len(data)} bytes to {local_path}")

        # Validate the downloaded file
        print("\nValidating downloaded file...")
        return validate_and_dump(local_path)

    except Exception as e:
        print(f"Error: SSH pull failed - {e}", file=sys.stderr)
        return 1


def ssh_push(ip, username, password, local_path, remote_path):
    """Upload calibration file to remote target via SSH"""
    if sshfs is None:
        print("Error: paramiko module is required for SSH support", file=sys.stderr)
        return 1

    try:
        # Read local file
        if not os.path.isfile(local_path):
            print(f"Error: Local file '{local_path}' not found", file=sys.stderr)
            return 1

        with open(local_path, "rb") as fp:
            data = fp.read()

        # Validate before uploading
        print(f"Validating local file {local_path}...")
        ret = validate_data(data, print_data=False)
        if ret != 0:
            print("Error: Local file validation failed", file=sys.stderr)
            return 1

        print(f"Connecting to {ip}...")
        ssh = sshfs.sshfs(ip, username, password)

        print(f"Pushing {local_path} ({len(data)} bytes) to {remote_path}...")

        # Upload file via SFTP
        sftp = ssh.ssh.open_sftp()
        with sftp.file(remote_path, "wb") as fp:
            fp.write(data)
        sftp.close()

        print(f"Successfully uploaded {len(data)} bytes to {remote_path}")
        return 0

    except Exception as e:
        print(f"Error: SSH push failed - {e}", file=sys.stderr)
        return 1


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="AD9088 Calibration Data Dump Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dump local calibration file
  %(prog)s /lib/firmware/ad9088_cal.bin

  # Download and dump from remote target and find calibration_data attribute
  %(prog)s --ssh-pull 192.168.1.100 root password

  # Download and dump from remote target with custom local filename
  %(prog)s --ssh-pull 192.168.1.100 root password my_cal.bin

  # Download and dump from remote target with specified remote path
  %(prog)s --ssh-pull 192.168.1.100 root password my_cal.bin /lib/firmware/ad9088_cal.bin

  # Upload local file to remote target
  %(prog)s --ssh-push 192.168.1.100 root password my_cal.bin /lib/firmware/ad9088_cal.bin
        """,
    )

    # SSH pull option
    parser.add_argument(
        "--ssh-pull",
        nargs="+",
        help="Download calibration file from remote target via SSH: ip username password [local_path] [remote_path]",
    )

    # SSH push option
    parser.add_argument(
        "--ssh-push",
        nargs="+",
        help="Upload calibration file to remote target via SSH: ip username password local_path remote_path",
    )

    # Default command - dump local file
    parser.add_argument(
        "file", nargs="?", default=None, help="Local calibration file to dump",
    )

    # Parse arguments
    args = parser.parse_args()

    # Handle --ssh-pull
    if args.ssh_pull:
        if len(args.ssh_pull) < 4:
            print(
                "Error: --ssh-pull requires: ip username password remote_path [local_path]",
                file=sys.stderr,
            )
            return 1
        ip = args.ssh_pull[0]
        username = args.ssh_pull[1]
        password = args.ssh_pull[2]
        local_path = (
            args.ssh_pull[3] if len(args.ssh_pull) > 3 else "calibration_data.bin"
        )
        remote_path = args.ssh_pull[4] if len(args.ssh_pull) > 4 else None
        return ssh_pull(ip, username, password, remote_path, local_path)

    # Handle --ssh-push
    if args.ssh_push:
        if len(args.ssh_push) != 5:
            print(
                "Error: --ssh-push requires: ip username password local_path remote_path",
                file=sys.stderr,
            )
            return 1
        ip = args.ssh_push[0]
        username = args.ssh_push[1]
        password = args.ssh_push[2]
        local_path = args.ssh_push[3]
        remote_path = args.ssh_push[4]
        return ssh_push(ip, username, password, local_path, remote_path)

    # Handle default command - dump local file
    if args.file:
        return validate_and_dump(args.file)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
