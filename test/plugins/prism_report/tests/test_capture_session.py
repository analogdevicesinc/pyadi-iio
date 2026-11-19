"""Session orchestrators wire iio_info + dmesg + labgrid together."""
from __future__ import annotations

from unittest import mock

import pytest

from test.plugins.prism_report.config import Config
from test.plugins.prism_report import capture as cap


def _cfg(**overrides):
    base = dict(
        enabled=True, out_dir=None, upload_url=None, upload_email=None,
        upload_password=None, upload_project=None, run_name="r",
        user_tags={}, labgrid_place=None, no_labgrid=True,
        dmesg_via="none", dmesg_ssh_user="root", dmesg_ssh_key=None,
        fail_on_upload_error=False,
    )
    base.update(overrides)
    return Config(**base)


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
    pre = cap.capture_session_pre(
        _cfg(dmesg_via="ssh"), iio_uri="ip:1.2.3.4"
    )
    assert pre.dmesg == b"[ 1.0] Linux\n"
    assert pre.dmesg_capture_method == "ssh"


def test_post_computes_diff_when_pre_and_post_succeed(monkeypatch):
    monkeypatch.setattr(cap, "capture_dmesg",
                        lambda **kw: b"[ 1.0] x\n[ 2.0] y\n")
    pre_state = cap.SessionPre(
        iio_info=b"i", dmesg=b"[ 1.0] x\n", boot_log=None,
        labgrid_session=None, dmesg_capture_method="ssh",
    )
    post = cap.capture_session_post(
        _cfg(dmesg_via="ssh"), iio_uri="ip:1.2.3.4", pre=pre_state,
    )
    assert post.dmesg_post == b"[ 1.0] x\n[ 2.0] y\n"
    assert post.dmesg_diff == b"[ 2.0] y\n"


def test_post_skips_diff_when_pre_dmesg_was_none(monkeypatch):
    monkeypatch.setattr(cap, "capture_dmesg", lambda **kw: b"[ 2.0] y\n")
    pre_state = cap.SessionPre(
        iio_info=None, dmesg=None, boot_log=None,
        labgrid_session=None, dmesg_capture_method="skipped",
    )
    post = cap.capture_session_post(
        _cfg(dmesg_via="ssh"), iio_uri="ip:1.2.3.4", pre=pre_state,
    )
    assert post.dmesg_post == b"[ 2.0] y\n"
    assert post.dmesg_diff is None
