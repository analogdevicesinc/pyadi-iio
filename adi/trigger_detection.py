# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

from adi.sshfs import sshfs


class trigger_detection:
    """TRIGGER_DETECTION AXI peripheral. No IIO endpoint, registers
    accessed via `busybox devmem` over SSH."""

    BASE_CHANNEL_0 = 0x44AC0000  # in front of axi_adc1_hmcad15xx
    BASE_CHANNEL_1 = 0x44AB0000  # in front of axi_adc2_hmcad15xx

    FRAME_SIZE_SAMPLES = 16

    _LOWER_THRESHOLD     = 0x00
    _UPPER_THRESHOLD     = 0x04
    _TRIGGER_LEVEL       = 0x08
    _NUM_FRAMES_PER_TRIG = 0x0C
    _NUM_CONTEXT_FRAMES  = 0x10
    _TRIGGER_MODE        = 0x14
    _SINGLE_TRIGGER      = 0x18
    _TRIGGER_ENABLE      = 0x1C
    _FORCE_TRIGGER       = 0x20
    _TRIGGER_RESET       = 0x24
    _TRIGGER_STATUS      = 0x28
    _TRIGGER_ARM         = 0x2C

    MODE_OUT_OF_BOUNDS = 0
    MODE_RISING        = 1
    MODE_FALLING       = 2
    MODE_FORCE         = 3

    def __init__(self, uri, base_address, username="root", password="analog"):
        self._base = base_address
        self._fs = sshfs(uri, username, password)

    def reg_read(self, offset):
        addr = self._base + offset
        out, err = self._fs._run(f"busybox devmem 0x{addr:08X}")
        if err:
            raise RuntimeError(f"devmem read 0x{addr:08X}: {err}")
        return int(out, 16)

    def reg_write(self, offset, value):
        addr = self._base + offset
        out, err = self._fs._run(
            f"busybox devmem 0x{addr:08X} 32 0x{value & 0xFFFFFFFF:08X}"
        )
        if err:
            raise RuntimeError(f"devmem write 0x{addr:08X}: {err}")

    @property
    def lower_threshold(self):
        return self.reg_read(self._LOWER_THRESHOLD) & 0xFF

    @lower_threshold.setter
    def lower_threshold(self, v):
        self.reg_write(self._LOWER_THRESHOLD, v & 0xFF)

    @property
    def upper_threshold(self):
        return self.reg_read(self._UPPER_THRESHOLD) & 0xFF

    @upper_threshold.setter
    def upper_threshold(self, v):
        self.reg_write(self._UPPER_THRESHOLD, v & 0xFF)

    @property
    def trigger_level(self):
        return self.reg_read(self._TRIGGER_LEVEL) & 0xFF

    @trigger_level.setter
    def trigger_level(self, v):
        self.reg_write(self._TRIGGER_LEVEL, v & 0xFF)

    @property
    def num_frames_per_trigger(self):
        return self.reg_read(self._NUM_FRAMES_PER_TRIG) & 0xFFFF

    @num_frames_per_trigger.setter
    def num_frames_per_trigger(self, v):
        self.reg_write(self._NUM_FRAMES_PER_TRIG, v & 0xFFFF)

    @property
    def num_context_frames(self):
        return self.reg_read(self._NUM_CONTEXT_FRAMES) & 0x3FF

    @num_context_frames.setter
    def num_context_frames(self, v):
        self.reg_write(self._NUM_CONTEXT_FRAMES, v & 0x3FF)

    @property
    def trigger_mode(self):
        return self.reg_read(self._TRIGGER_MODE) & 0x7

    @trigger_mode.setter
    def trigger_mode(self, v):
        self.reg_write(self._TRIGGER_MODE, v & 0x7)

    @property
    def single_trigger(self):
        return bool(self.reg_read(self._SINGLE_TRIGGER) & 0x1)

    @single_trigger.setter
    def single_trigger(self, v):
        self.reg_write(self._SINGLE_TRIGGER, 1 if v else 0)

    @property
    def trigger_enable(self):
        return bool(self.reg_read(self._TRIGGER_ENABLE) & 0x1)

    @trigger_enable.setter
    def trigger_enable(self, v):
        if not v:
            self.disarm()
        self.reg_write(self._TRIGGER_ENABLE, 1 if v else 0)

    @property
    def force_trigger(self):
        return bool(self.reg_read(self._FORCE_TRIGGER) & 0x1)

    @force_trigger.setter
    def force_trigger(self, v):
        self.reg_write(self._FORCE_TRIGGER, 1 if v else 0)

    @property
    def triggered(self):
        return bool(self.reg_read(self._TRIGGER_STATUS) & 0x1)

    @property
    def trigger_arm(self):
        return bool(self.reg_read(self._TRIGGER_ARM) & 0x1)

    @trigger_arm.setter
    def trigger_arm(self, v):
        self.reg_write(self._TRIGGER_ARM, 1 if v else 0)

    def reset(self):
        self.reg_write(self._TRIGGER_RESET, 1)
        self.reg_write(self._TRIGGER_RESET, 0)

    def arm(self):
        """Start trigger comparison. Auto-disarms on trigger event.
        Caller must have already set trigger_enable=True and created the iio buffer."""
        self.trigger_arm = True

    def disarm(self):
        """Cancel arm before a trigger event."""
        self.trigger_arm = False

    def wait_for_trigger(self, poll_interval=0.05, timeout=None):
        """Poll trigger_arm until it self-clears (event fired). Ctrl-C-able.
        Returns True on trigger, False on timeout."""
        deadline = None if timeout is None else time.monotonic() + timeout
        while self.trigger_arm:
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(poll_interval)
        return True

    def compute_rx_buffer_size(self):
        return (self.num_context_frames + self.num_frames_per_trigger) * self.FRAME_SIZE_SAMPLES
