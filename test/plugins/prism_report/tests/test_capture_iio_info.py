"""capture_iio_info: subprocess success, library fallback, both-fail None."""
from __future__ import annotations

import subprocess
from unittest import mock

import pytest

from test.plugins.prism_report.capture import capture_iio_info


def test_subprocess_path_returns_bytes(monkeypatch):
    fake = mock.Mock(returncode=0, stdout=b"IIO context\n", stderr=b"")
    monkeypatch.setattr(subprocess, "run", mock.Mock(return_value=fake))
    out = capture_iio_info("ip:192.168.2.1")
    assert out == b"IIO context\n"


def test_falls_back_to_library_when_binary_missing(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        mock.Mock(side_effect=FileNotFoundError))
    fake_ctx = mock.MagicMock()
    fake_ctx.devices = []
    fake_ctx.attrs = {"name": "fake"}
    fake_ctx.description = "fake context"
    monkeypatch.setattr(
        "test.plugins.prism_report.capture._open_iio_context",
        lambda uri: fake_ctx,
    )
    out = capture_iio_info("ip:192.168.2.1")
    assert out is not None
    assert b"fake" in out


def test_returns_none_when_both_paths_fail(monkeypatch):
    monkeypatch.setattr(subprocess, "run",
                        mock.Mock(side_effect=FileNotFoundError))
    monkeypatch.setattr(
        "test.plugins.prism_report.capture._open_iio_context",
        mock.Mock(side_effect=Exception("no libiio")),
    )
    assert capture_iio_info("ip:127.0.0.1") is None
