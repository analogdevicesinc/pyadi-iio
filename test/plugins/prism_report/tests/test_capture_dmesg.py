"""dmesg capture: SSH path, console fallback, diff stability."""
from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from test.plugins.prism_report.capture import (
    capture_dmesg, compute_dmesg_diff,
)


def test_ssh_path_when_uri_is_ip(monkeypatch):
    fake = mock.Mock(returncode=0, stdout=b"[ 1.0] Linux\n", stderr=b"")
    runner = mock.Mock(return_value=fake)
    monkeypatch.setattr(subprocess, "run", runner)
    out = capture_dmesg(
        iio_uri="ip:192.168.2.1", via="auto",
        ssh_user="root", ssh_key=None,
        labgrid_session=None,
    )
    assert out == b"[ 1.0] Linux\n"
    args, _ = runner.call_args
    assert "ssh" in args[0][0]
    assert "192.168.2.1" in " ".join(args[0])


def test_ssh_failure_falls_back_to_console(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run",
        mock.Mock(return_value=mock.Mock(returncode=255, stdout=b"", stderr=b"oops")),
    )
    fake_session = mock.Mock()
    fake_session.run_shell_command = mock.Mock(return_value=b"[ 1.0] dmesg-via-console\n")
    out = capture_dmesg(
        iio_uri="ip:192.168.2.1", via="auto",
        ssh_user="root", ssh_key=None,
        labgrid_session=fake_session,
    )
    assert out == b"[ 1.0] dmesg-via-console\n"


def test_via_none_returns_none():
    assert capture_dmesg(
        iio_uri="ip:1.2.3.4", via="none",
        ssh_user="root", ssh_key=None, labgrid_session=None,
    ) is None


def test_non_ip_uri_skips_ssh(monkeypatch):
    runner = mock.Mock()
    monkeypatch.setattr(subprocess, "run", runner)
    fake_session = mock.Mock()
    fake_session.run_shell_command = mock.Mock(return_value=b"x")
    out = capture_dmesg(
        iio_uri="usb:1.2.3", via="auto",
        ssh_user="root", ssh_key=None,
        labgrid_session=fake_session,
    )
    assert out == b"x"
    runner.assert_not_called()


def test_diff_ignores_timestamp_prefix():
    pre = b"[    1.001] line A\n[    2.002] line B\n"
    post = b"[    1.500] line A\n[    2.501] line B\n[    3.000] line C\n"
    out = compute_dmesg_diff(pre, post)
    assert out == b"[    3.000] line C\n"


def test_diff_empty_when_no_change():
    pre = b"[    1.0] x\n"
    post = b"[    9.9] x\n"
    assert compute_dmesg_diff(pre, post) == b""
