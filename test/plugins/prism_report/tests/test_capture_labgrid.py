"""Labgrid boot-log capture using a fake client."""
from __future__ import annotations

from unittest import mock

import pytest

from test.plugins.prism_report.capture import (
    LabgridSession, capture_boot_log,
)


class _FakeLG:
    def __init__(self, buffer=b"U-Boot 2024.01\nLinux version 6.1.0\n"):
        self._buffer = buffer
        self.console_acquired = False
        self.released = False

    def acquire(self, place):  # noqa: D401
        self.console_acquired = True
        return self

    def read_console(self):
        return self._buffer

    def run_shell_command(self, cmd):
        return b""

    def release(self):
        self.released = True


def test_returns_console_buffer(monkeypatch):
    fake = _FakeLG()
    sess = LabgridSession(fake)
    out = capture_boot_log(sess, place="pluto-bench-1")
    assert b"U-Boot" in out
    assert fake.console_acquired


def test_returns_none_when_session_is_none():
    assert capture_boot_log(None, place="pluto-bench-1") is None


def test_returns_none_when_acquire_raises(monkeypatch):
    fake = mock.Mock()
    fake.acquire = mock.Mock(side_effect=RuntimeError("locked"))
    sess = LabgridSession(fake)
    assert capture_boot_log(sess, place="pluto-bench-1") is None
