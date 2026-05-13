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

    _LOWER_THRESHOLD    = 0x00
    _UPPER_THRESHOLD    = 0x04
    _TRIGGER_LEVEL      = 0x08  # reserved
    _NUM_TRIGGER_FRAMES = 0x0C
    _NUM_CONTEXT_FRAMES = 0x10
    _TRIGGER_MODE       = 0x14
    _SINGLE_TRIGGER     = 0x18
    _TRIGGER_ENABLE     = 0x1C
    _FORCE_TRIGGER      = 0x20  # SC
    _TRIGGER_RESET      = 0x24  # SC
    _TRIGGER_STATUS     = 0x28  # W1C
    _ARM_TRIGGER        = 0x2C  # SC
    _TRIGGER_POS        = 0x30  # RO
    _FSM_STATUS         = 0x34  # RO

    # Trigger modes
    MODE_THRESHOLD = 0
    MODE_RISING    = 1
    MODE_FALLING   = 2

    # FSM states (read via fsm_status)
    STATE_BYPASS           = 0
    STATE_IDLE             = 1
    STATE_ARMED            = 2
    STATE_TRIGGERED        = 3
    STATE_CAPTURE_COMPLETE = 4

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
    def num_trigger_frames(self):
        return self.reg_read(self._NUM_TRIGGER_FRAMES) & 0xFFFF

    @num_trigger_frames.setter
    def num_trigger_frames(self, v):
        self.reg_write(self._NUM_TRIGGER_FRAMES, v & 0xFFFF)

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
        self.reg_write(self._TRIGGER_ENABLE, 1 if v else 0)

    @property
    def triggered(self):
        """Sticky trigger_detected bit (W1C). Use clear_trigger_detected() to clear."""
        return bool(self.reg_read(self._TRIGGER_STATUS) & 0x1)

    @property
    def trigger_pos(self):
        """(frame_idx, sample_offset) of the most recent trigger event."""
        v = self.reg_read(self._TRIGGER_POS)
        return v & 0x7FF, (v >> 16) & 0xF

    @property
    def fsm_status(self):
        return self.reg_read(self._FSM_STATUS) & 0x7

    @property
    def armed(self):
        return self.fsm_status == self.STATE_ARMED

    def clear_trigger_detected(self):
        """Write 1 to clear the sticky trigger_detected bit."""
        self.reg_write(self._TRIGGER_STATUS, 1)

    def force_trigger(self):
        """Pulse force_trigger. Only effective when FSM is in ARMED."""
        self.reg_write(self._FORCE_TRIGGER, 1)

    def reset(self):
        """Pulse trigger_reset. FSM -> BYPASS (re-IDLEs if trigger_enable still 1)."""
        self.reg_write(self._TRIGGER_RESET, 1)

    def arm(self):
        """Pulse arm_trigger. FSM transitions IDLE -> ARMED.
        Caller must have set trigger_enable=True and created the iio buffer."""
        self.reg_write(self._ARM_TRIGGER, 1)

    def disarm(self):
        """Reset FSM (-> BYPASS); auto-IDLEs if trigger_enable still 1."""
        self.reset()

    def wait_for_trigger(self, poll_interval=0.05, timeout=None):
        """Poll trigger_detected until set. Ctrl-C-able between polls.
        Returns True on trigger, False on timeout (timeout=None waits forever)."""
        deadline = None if timeout is None else time.monotonic() + timeout
        while not self.triggered:
            if deadline is not None and time.monotonic() >= deadline:
                return False
            time.sleep(poll_interval)
        return True

    def compute_rx_buffer_size(self):
        return (self.num_context_frames + self.num_trigger_frames) * self.FRAME_SIZE_SAMPLES
