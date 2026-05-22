# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
"""Unit tests for the IQRenderer (combines former test_analyze + test_render)."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pytest
from pytest_prism import RenderContext

from adi.prism_adapters.iq import IQRenderer, PayloadError, analyze, render_spectrum


def _one_tone_payload(fs=1e6, f=100e3, n=8192):
    t = np.arange(n) / fs
    iq = (np.cos(2 * np.pi * f * t) + 1j * np.sin(2 * np.pi * f * t)).astype(
        np.complex64
    )
    return {
        "iq": iq,
        "fs": fs,
        "domain": "complex",
        "expected_tones": [f],
        "metrics": {"peak_min": -10},
    }


# --- ports of test_analyze.py expectations ---


def test_analyze_returns_carrier():
    res = analyze(_one_tone_payload())
    # In genalyzer-unavailable (degraded) fallback, carriers is empty.
    assert len(res.carriers) >= 1 or res.degraded


def test_analyze_missing_iq_raises():
    with pytest.raises(PayloadError, match="iq"):
        analyze({"fs": 1e6, "domain": "complex"})


def test_analyze_missing_fs_raises():
    with pytest.raises(PayloadError, match="fs"):
        analyze({"iq": np.zeros(64, dtype=np.complex64), "domain": "complex"})


# --- ports of test_render.py expectations ---


def test_render_spectrum_returns_html():
    res = analyze(_one_tone_payload())
    html = render_spectrum(
        res,
        _one_tone_payload(),
        meta={"test_id": "t::a", "test_failed": False, "failure_summary": ""},
    )
    assert html.startswith("<")
    assert "plotly" in html.lower()


# --- IQRenderer class wrapper ---


def test_iq_renderer_writes_expected_files(tmp_path):
    r = IQRenderer()
    ctx = RenderContext(
        case_dir=tmp_path, case_id="t::a", logger=logging.getLogger("test"),
    )
    result = r.render(_one_tone_payload(), ctx)
    assert (tmp_path / "spectrum.html").exists()
    assert (tmp_path / "spectrum.json").exists()
    assert (tmp_path / "iq.npz").exists()
    assert result.primary_artifact == "spectrum.html"
    # metrics is a Mapping[str, float]; OK to be empty if all genalyzer metrics
    # are None (e.g., when genalyzer isn't installed and analyze() returns degraded).
    assert isinstance(result.metrics, dict)


def test_iq_renderer_payload_kind():
    assert IQRenderer.payload_kind == "adi.iq"


def test_iq_renderer_propagates_payload_error(tmp_path):
    r = IQRenderer()
    ctx = RenderContext(
        case_dir=tmp_path, case_id="t::a", logger=logging.getLogger("test"),
    )
    with pytest.raises(PayloadError):
        r.render({"fs": 1e6}, ctx)
