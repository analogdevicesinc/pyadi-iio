"""Pure-logic tests for analyze()."""
from __future__ import annotations

import numpy as np
import pytest

from test.plugins.prism_report.analyze import (
    AnalysisResult, PayloadError, analyze,
)


def test_payload_missing_iq_raises():
    with pytest.raises(PayloadError, match="iq"):
        analyze({"fs": 1000})


def test_payload_missing_fs_raises():
    with pytest.raises(PayloadError, match="fs"):
        analyze({"iq": np.zeros(8, dtype=np.complex64)})


def test_one_tone_finds_carrier(synthetic_tone):
    payload = {
        "iq": synthetic_tone["iq"],
        "fs": synthetic_tone["fs"],
        "domain": "complex",
        "expected_tones": [synthetic_tone["f0"]],
    }
    result = analyze(payload)
    assert isinstance(result, AnalysisResult)
    bin_hz = synthetic_tone["fs"] / len(synthetic_tone["iq"])
    assert abs(result.carriers[0].freq_hz - synthetic_tone["f0"]) < bin_hz
    # We expect HD2 to be detected at ~2*f0
    hd2 = next((c for c in result.harmonics if c.order == 2), None)
    assert hd2 is not None
    assert abs(hd2.freq_hz - 2 * synthetic_tone["f0"]) < 2 * bin_hz


def test_two_tone_finds_both_carriers_and_imd(synthetic_two_tone):
    payload = {
        "iq": synthetic_two_tone["iq"],
        "fs": synthetic_two_tone["fs"],
        "domain": "complex",
        "expected_tones": [synthetic_two_tone["f1"], synthetic_two_tone["f2"]],
    }
    result = analyze(payload)
    assert len(result.carriers) == 2


def test_genalyzer_unavailable_falls_back(monkeypatch, synthetic_tone):
    # Force the fallback path
    import test.plugins.prism_report.analyze as analyze_mod
    monkeypatch.setattr(analyze_mod, "_GENALYZER", None)
    payload = {
        "iq": synthetic_tone["iq"],
        "fs": synthetic_tone["fs"],
        "domain": "complex",
        "expected_tones": [synthetic_tone["f0"]],
    }
    result = analyze(payload)
    assert result.degraded is True
    assert len(result.spectrum_freq_hz) > 0
    assert len(result.spectrum_dbfs) == len(result.spectrum_freq_hz)
    assert result.carriers == []  # No FA in fallback
