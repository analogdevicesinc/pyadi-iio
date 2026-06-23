# Copyright (C) 2021-2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

from adi.attribute import attribute
from adi.context_manager import context_manager


class yline(object):
    def __init__(self, dev, x, line):
        """Initializer for a Y line of switches."""
        self._line = line
        self._x = x
        self._dev = dev

    def __str__(self):
        """String representation of a Y line of switches."""
        return "[" + ", ".join([str(num) for num in self._line]) + "]"

    def __getitem__(self, y):
        """Read access a Y line using python array indexing."""
        return self._line[y]

    def __setitem__(self, y, value):
        """Write access a Y line using python array indexing."""
        self._dev._switch(self._x, y, value, self._dev._ldsw)
        self._line[y] = value


class adg2128(attribute, context_manager):
    """ADG2128 cross point switch."""

    def __init__(self, uri=""):
        """Initializer for the adg2128 cross point switch device."""
        self._device_name = "adg2128"
        context_manager.__init__(self, uri, self._device_name)

        self._i2c_devs = []
        self._xmax = 0
        self._xline = []
        self._ldsw = True

        self._ctrl = self._ctx.find_device(self._device_name)

        if not self._ctrl:
            raise Exception(self._device_name + " device not found")

    @property
    def immediate(self):
        """Specify whether the writing of a switch is immediate or not.

        When it's not immediate, the new switch configuration is only
        latched into the device (see LDSW in datasheet).
        """
        return self._ldsw

    @immediate.setter
    def immediate(self, value):
        self._ldsw = value

    def add(self, addr):
        """
        Add device by its i2c address.

        Multiple devices may be added provided they all have their Y terminals
        connected (common Y configuration).
        1x adg2128 is represented by a 12 by 8 matrix
        2x adg2128 is represented by a 24 by 8 matrix
        ...

        Arguments:
        addr - device address on i2c bus
        """
        self._i2c_devs.append(addr)
        self._xmax += 12
        for x in range(self._xmax - 12, self._xmax):
            y = yline(self, x, [False for y in range(8)])
            self._xline.append(y)

    def _read(self, addr):
        """Direct Register Access via debugfs."""
        self._set_iio_debug_attr_str("direct_reg_access", addr, self._ctrl)
        return self._get_iio_debug_attr_str("direct_reg_access", self._ctrl)

    def _write(self, addr, val):
        """Direct Register Access via debugfs."""
        self._set_iio_debug_attr_str(
            "direct_reg_access", "0x{:X} 0x{:X}".format(addr, val), self._ctrl
        )

    def _switch(self, x, y, closed, immediate):
        data = closed << 15
        ax_lookup = [0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13]
        ax = ax_lookup[x % 12] << 11
        ay = y << 8
        ldsw = immediate
        addr = self._i2c_devs[x // 12]
        val = data | ax | ay | ldsw
        self._write(addr, val)

    def _read_x(self, x):
        addr = self._i2c_devs[int(x) // 12]
        x_lookup = [
            0b00110100,
            0b00111100,
            0b01110100,
            0b01111100,
            0b00110101,
            0b00111101,
            0b01110101,
            0b01111101,
            0b00110110,
            0b00111110,
            0b01110110,
            0b01111110,
        ]
        val = x_lookup[x % 12] << 8
        self._write(addr, val)
        return self._read(addr)

    def __str__(self):
        """String representation of the cross point switch."""
        return "\n".join([f"x{idx}: {x}" for idx, x in enumerate(self._xline)])

    def __getitem__(self, x):
        """Read access a X line using python array indexing."""
        return self._xline[x]

    def __setitem__(self, x, value):
        """Write access a X line using python array indexing."""
        for y, closed in enumerate(value):
            self._xline[x][y] = closed

    def open_all(self):
        """
        Open all switches.

        For each device, iterate all x-y combinations and
        open all the switches at once.
        """
        ldsw = self._ldsw
        for x in range(self._xmax):
            for y in range(8):
                self._ldsw = False
                if (y == 7) and (x % 12 == 11):
                    self._ldsw = True
                self[x][y] = False
        self._ldsw = ldsw
