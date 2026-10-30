"""End-to-end test: a fake test populates pytest.data_log; plugin produces an
out-dir with the right shape."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_local_export_e2e(pytester, tmp_path: Path, monkeypatch):
    out = tmp_path / "report"
    monkeypatch.setenv("PRISM_NO_LABGRID", "1")
    pytester.makepyfile(
        f"""
        import numpy as np, pytest

        def test_dummy_spectrum():
            n = 1024
            fs = 4_000_000
            f0 = 400_000
            t = np.arange(n) / fs
            iq = np.exp(2j * np.pi * f0 * t).astype(np.complex64) * (2**14)
            pytest.data_log = {{
                "iq": iq, "fs": fs, "domain": "complex",
                "expected_tones": [f0],
                "metrics": {{"sfdr_dbc": 50.0, "sfdr_min": 40}},
                "params": {{"sample_rate": fs}},
                "classname": "adi.Pluto",
            }}
            assert True
        """
    )
    result = pytester.runpytest(
        "--prism-report",
        f"--prism-out={out}",
        "--prism-dmesg-via=none",
        "-q",
    )
    result.assert_outcomes(passed=1)
    assert (out / "manifest.json").exists()
    manifest = json.loads((out / "manifest.json").read_text())
    assert any(c["case_nodeid"].endswith("test_dummy_spectrum")
               for c in manifest["cases"])
    case_dir = out / "cases"
    spectrum_paths = list(case_dir.rglob("spectrum.html"))
    assert len(spectrum_paths) == 1
    assert b"plotly" in spectrum_paths[0].read_bytes().lower()
