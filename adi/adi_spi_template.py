# Copyright (C) 2025-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class adi_spi_template(attribute, context_manager):
    """ADI SPI Template - minimal register read/write driver

    This Python driver works with the Linux kernel driver:
    drivers/misc/adi_spi_template.c
    """

    _device_name = "adi_dev"  # matches DT node name in adi_dev@0

    def __init__(self, uri="", device_name="adi_dev"):
        """Constructor for adi_spi_template class.

        Args:
            uri: URI of the IIO context (e.g., "ip:192.168.1.100" or "local:")
            device_name: Name of the IIO device (default: "adi_dev" from DT node)
        """
        context_manager.__init__(self, uri, self._device_name)

        self._ctrl = None

        # Find the device - try both provided name and default
        search_names = [device_name, self._device_name, "adi-spi-template"]
        for device in self._ctx.devices:
            if device.name in search_names:
                self._ctrl = device
                break

        if not self._ctrl:
            # List available devices for debugging
            available = [d.name for d in self._ctx.devices]
            raise Exception(
                f"Device '{device_name or self._device_name}' not found. "
                f"Available devices: {available}"
            )

    def reg_read(self, reg):
        """Read a register value.

        Args:
            reg: Register address (int or hex string like "0x1234")

        Returns:
            Register value as integer
        """
        if isinstance(reg, int):
            reg = hex(reg)
        self._set_iio_debug_attr_str("direct_reg_access", reg, self._ctrl)
        val = self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)
        return int(val, 0)

    def reg_write(self, reg, value):
        """Write a register value.

        Args:
            reg: Register address (int or hex string)
            value: Value to write (int or hex string)
        """
        if isinstance(reg, int):
            reg = hex(reg)
        if isinstance(value, int):
            value = hex(value)
        self._set_iio_debug_attr_str("direct_reg_access", f"{reg} {value}", self._ctrl)

    def reg_dump(self, start=0x00, end=0x10):
        """Dump a range of registers.

        Args:
            start: Start register address
            end: End register address (inclusive)

        Returns:
            Dictionary of {address: value}
        """
        regs = {}
        for addr in range(start, end + 1):
            try:
                regs[addr] = self.reg_read(addr)
            except Exception as e:
                regs[addr] = f"Error: {e}"
        return regs

    def reg_dump_print(self, start=0x00, end=0x10):
        """Dump and print a range of registers."""
        regs = self.reg_dump(start, end)
        print(f"Register dump 0x{start:04X} - 0x{end:04X}:")
        print("-" * 30)
        for addr, val in regs.items():
            if isinstance(val, int):
                print(f"0x{addr:04X}: 0x{val:02X} ({val:3d})")
            else:
                print(f"0x{addr:04X}: {val}")


# Example usage
if __name__ == "__main__":
    # Connect to local IIO context
    # dev = adi_spi_template(uri="local:")

    # Or connect to remote target
    # dev = adi_spi_template(uri="ip:192.168.1.100")

    # Read register
    # val = dev.reg_read(0x00)
    # print(f"Register 0x00 = 0x{val:02X}")

    # Write register
    # dev.reg_write(0x02, 0x55)

    # Dump registers
    # dev.reg_dump_print(0x00, 0x0F)

    print("adi_spi_template driver loaded")
    print("Usage:")
    print("  dev = adi_spi_template(uri='ip:192.168.1.100')")
    print("  val = dev.reg_read(0x00)")
    print("  dev.reg_write(0x02, 0x55)")
    print("  dev.reg_dump_print(0x00, 0x0F)")
