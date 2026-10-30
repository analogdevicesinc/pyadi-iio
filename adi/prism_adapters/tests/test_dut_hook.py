# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
"""Unit tests for ADIDUTHook + the underlying capture functions.

Merged from the old plugin's test_capture_dmesg.py, test_capture_iio_info.py,
test_capture_labgrid.py, test_capture_session.py.
"""

from __future__ import annotations

import logging as _logging
import subprocess
from unittest import mock

import pytest
from pytest_prism import SessionContext
from pytest_prism.config import Config

from adi.prism_adapters import capture as cap
from adi.prism_adapters.capture import (
    ADIDUTHook,
    LabgridSession,
    SessionPre,
    capture_boot_log,
    capture_dmesg,
    capture_iio_info,
    compute_dmesg_diff,
)

# ============================================================
# Helpers shared across sections
# ============================================================


def _cfg(**overrides):
    base = dict(
        enabled=True,
        out_dir=None,
        upload_url=None,
        upload_email=None,
        upload_password=None,
        upload_project=None,
        run_name="r",
        user_tags={},
        labgrid_place=None,
        no_labgrid=True,
        dmesg_via="none",
        dmesg_ssh_user="root",
        dmesg_ssh_key=None,
        fail_on_upload_error=False,
    )
    base.update(overrides)
    return Config(**base)


# ============================================================
# test_capture_dmesg — dmesg capture: SSH path, console fallback, diff stability
# ============================================================


def test_ssh_path_when_uri_is_ip(monkeypatch):
    fake = mock.Mock(returncode=0, stdout=b"[ 1.0] Linux\n", stderr=b"")
    runner = mock.Mock(return_value=fake)
    monkeypatch.setattr(subprocess, "run", runner)
    out = capture_dmesg(
        iio_uri="ip:192.168.2.1",
        via="auto",
        ssh_user="root",
        ssh_key=None,
        labgrid_session=None,
    )
    assert out == b"[ 1.0] Linux\n"
    args, _ = runner.call_args
    assert "ssh" in args[0][0]
    assert "192.168.2.1" in " ".join(args[0])


def test_ssh_failure_falls_back_to_console(monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "run",
        mock.Mock(return_value=mock.Mock(returncode=255, stdout=b"", stderr=b"oops")),
    )
    fake_session = mock.Mock()
    fake_session.run_shell_command = mock.Mock(
        return_value=b"[ 1.0] dmesg-via-console\n"
    )
    out = capture_dmesg(
        iio_uri="ip:192.168.2.1",
        via="auto",
        ssh_user="root",
        ssh_key=None,
        labgrid_session=fake_session,
    )
    assert out == b"[ 1.0] dmesg-via-console\n"


def test_via_none_returns_none():
    assert (
        capture_dmesg(
            iio_uri="ip:1.2.3.4",
            via="none",
            ssh_user="root",
            ssh_key=None,
            labgrid_session=None,
        )
        is None
    )


def test_non_ip_uri_skips_ssh(monkeypatch):
    runner = mock.Mock()
    monkeypatch.setattr(subprocess, "run", runner)
    fake_session = mock.Mock()
    fake_session.run_shell_command = mock.Mock(return_value=b"x")
    out = capture_dmesg(
        iio_uri="usb:1.2.3",
        via="auto",
        ssh_user="root",
        ssh_key=None,
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


# ============================================================
# test_capture_iio_info — subprocess success, library fallback, both-fail None
# ============================================================


def test_subprocess_path_returns_bytes(monkeypatch):
    fake = mock.Mock(returncode=0, stdout=b"IIO context\n", stderr=b"")
    monkeypatch.setattr(subprocess, "run", mock.Mock(return_value=fake))
    out = capture_iio_info("ip:192.168.2.1")
    assert out == b"IIO context\n"


def test_falls_back_to_library_when_binary_missing(monkeypatch):
    monkeypatch.setattr(subprocess, "run", mock.Mock(side_effect=FileNotFoundError))
    fake_ctx = mock.MagicMock()
    fake_ctx.devices = []
    fake_ctx.attrs = {"name": "fake"}
    fake_ctx.description = "fake context"
    monkeypatch.setattr(
        "adi.prism_adapters.capture._open_iio_context", lambda uri: fake_ctx,
    )
    out = capture_iio_info("ip:192.168.2.1")
    assert out is not None
    assert b"fake" in out


def test_returns_none_when_both_paths_fail(monkeypatch):
    monkeypatch.setattr(subprocess, "run", mock.Mock(side_effect=FileNotFoundError))
    monkeypatch.setattr(
        "adi.prism_adapters.capture._open_iio_context",
        mock.Mock(side_effect=Exception("no libiio")),
    )
    assert capture_iio_info("ip:127.0.0.1") is None


# ============================================================
# test_capture_labgrid — Labgrid boot-log capture using a fake client
# ============================================================


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


# ============================================================
# test_capture_session — Session orchestrators wire iio_info + dmesg + labgrid
# ============================================================


def test_pre_collects_iio_info_only_when_dmesg_disabled(monkeypatch):
    monkeypatch.setattr(cap, "capture_iio_info", lambda uri: b"info-bytes")
    monkeypatch.setattr(cap, "open_labgrid_session", lambda **kw: None)
    pre = cap.capture_session_pre(_cfg(), iio_uri="ip:1.2.3.4")
    assert pre.iio_info == b"info-bytes"
    assert pre.dmesg is None
    assert pre.boot_log is None
    assert pre.labgrid_session is None
    assert pre.dmesg_capture_method == "skipped"


def test_pre_includes_dmesg_when_via_ssh(monkeypatch):
    monkeypatch.setattr(cap, "capture_iio_info", lambda uri: b"info")
    monkeypatch.setattr(cap, "open_labgrid_session", lambda **kw: None)
    monkeypatch.setattr(cap, "capture_dmesg", lambda **kw: b"[ 1.0] Linux\n")
    pre = cap.capture_session_pre(_cfg(dmesg_via="ssh"), iio_uri="ip:1.2.3.4")
    assert pre.dmesg == b"[ 1.0] Linux\n"
    assert pre.dmesg_capture_method == "ssh"


def test_post_computes_diff_when_pre_and_post_succeed(monkeypatch):
    monkeypatch.setattr(cap, "capture_dmesg", lambda **kw: b"[ 1.0] x\n[ 2.0] y\n")
    pre_state = SessionPre(
        iio_info=b"i",
        dmesg=b"[ 1.0] x\n",
        boot_log=None,
        labgrid_session=None,
        dmesg_capture_method="ssh",
    )
    post = cap.capture_session_post(
        _cfg(dmesg_via="ssh"), iio_uri="ip:1.2.3.4", pre=pre_state,
    )
    assert post.dmesg_post == b"[ 1.0] x\n[ 2.0] y\n"
    assert post.dmesg_diff == b"[ 2.0] y\n"


def test_post_skips_diff_when_pre_dmesg_was_none(monkeypatch):
    monkeypatch.setattr(cap, "capture_dmesg", lambda **kw: b"[ 2.0] y\n")
    pre_state = SessionPre(
        iio_info=None,
        dmesg=None,
        boot_log=None,
        labgrid_session=None,
        dmesg_capture_method="skipped",
    )
    post = cap.capture_session_post(
        _cfg(dmesg_via="ssh"), iio_uri="ip:1.2.3.4", pre=pre_state,
    )
    assert post.dmesg_post == b"[ 2.0] y\n"
    assert post.dmesg_diff is None


# ============================================================
# ADIDUTHook class wrapper tests (new)
# ============================================================


def _hook_ctx(tmp_path):
    cfg = Config.from_argv(["--prism-report", "--prism-no-labgrid"])
    return SessionContext(
        run_dir=tmp_path,
        hook_dir=tmp_path / "hook",
        config=cfg,
        logger=_logging.getLogger("test"),
    )


def test_adi_dut_hook_session_pre_no_iio(tmp_path):
    ctx = _hook_ctx(tmp_path)
    ctx.hook_dir.mkdir(parents=True, exist_ok=True)
    h = ADIDUTHook()
    meta = h.session_pre(ctx)
    # Without PYADI_IIO_URI set, iio_uri is empty and no iio_info is written
    assert meta["iio_uri"] == ""
    assert not (ctx.hook_dir / "iio_info.txt").exists()


def test_adi_dut_hook_session_post_runs_without_pre(tmp_path):
    """If session_pre wasn't called (e.g., crash before), session_post still works."""
    ctx = _hook_ctx(tmp_path)
    ctx.hook_dir.mkdir(parents=True, exist_ok=True)
    h = ADIDUTHook()
    meta = h.session_post(ctx)
    assert "dmesg_post_captured" in meta


def test_adi_dut_hook_session_pre_records_iio_uri_when_set(tmp_path, monkeypatch):
    monkeypatch.setenv("PYADI_IIO_URI", "ip:127.0.0.1:9999")  # unreachable
    ctx = _hook_ctx(tmp_path)
    ctx.hook_dir.mkdir(parents=True, exist_ok=True)
    h = ADIDUTHook()
    meta = h.session_pre(ctx)
    assert meta["iio_uri"] == "ip:127.0.0.1:9999"
