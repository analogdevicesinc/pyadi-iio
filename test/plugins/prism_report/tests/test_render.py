"""Render-module tests: figure shape, golden snapshot, failure annotation."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

from test.plugins.prism_report.analyze import AnalysisResult, Component
from test.plugins.prism_report.render import (
    render_spectrum,
    render_spectrum_figure_json,
)

GOLDEN_DIR = Path(__file__).parent / "golden"


def _result_one_tone():
    freq = np.linspace(-1e6, 1e6, 1024)
    dbfs = -90 + 0 * freq
    return AnalysisResult(
        spectrum_freq_hz=freq,
        spectrum_dbfs=dbfs,
        carriers=[Component("carrier", 200_000, -1.0, None, None)],
        harmonics=[
            Component("HD2", 400_000, -55.0, -54.0, 2),
            Component("HD3", 600_000, -65.0, -64.0, 3),
        ],
        sfdr_dbc=53.0, snr_db=58.0, sinad_db=56.0, thd_dbc=-58.0,
        nsd_dbfs_per_hz=-110.0,
    )


def _payload_one_tone():
    return {"classname": "adi.Pluto", "params": {"sample_rate": 4000000}}


def test_html_contains_plotly_div_and_metrics():
    html = render_spectrum(
        _result_one_tone(), _payload_one_tone(),
        meta={"test_id": "test_pluto::test_sfdr[0]", "test_failed": False},
    )
    assert "plotly" in html.lower()
    assert "SFDR" in html and "53" in html
    assert "test_pluto::test_sfdr[0]" in html


def test_html_marks_carrier_and_harmonics():
    html = render_spectrum(
        _result_one_tone(), _payload_one_tone(),
        meta={"test_id": "x", "test_failed": False},
    )
    # Each annotation kind should appear at least once in label text.
    assert "f0" in html.lower() or "carrier" in html.lower()
    assert re.search(r"HD2|HD3", html) is not None


def test_failed_test_renders_failed_badge():
    html = render_spectrum(
        _result_one_tone(), _payload_one_tone(),
        meta={"test_id": "x", "test_failed": True,
              "failure_summary": "AssertionError: 33 < 40"},
    )
    assert "FAILED" in html
    assert "AssertionError" in html


def test_golden_snapshot_byte_stable(request):
    """Update with `pytest --update-golden` (custom flag) when intentional."""
    html = render_spectrum(
        _result_one_tone(), _payload_one_tone(),
        meta={"test_id": "test_pluto::test_sfdr[0]", "test_failed": False,
              "fixed_clock": "2026-01-01T00:00:00Z"},
    )
    target = GOLDEN_DIR / "spectrum_one_tone.html"
    if request.config.getoption("--update-golden", default=False):
        GOLDEN_DIR.mkdir(exist_ok=True)
        target.write_text(html)
        pytest.skip("golden updated")
    if not target.exists():
        pytest.skip(f"golden missing — run with --update-golden once: {target}")
    expected = target.read_text()
    assert html == expected


def test_figure_json_is_parseable_plotly_spec():
    """The JSON variant must be a valid Plotly figure spec with carrier + HD
    annotations encoded in `layout.shapes`/`layout.annotations`.
    """
    raw = render_spectrum_figure_json(
        _result_one_tone(), _payload_one_tone(),
        meta={"test_id": "x", "test_failed": False},
    )
    fig = json.loads(raw)
    assert "data" in fig and isinstance(fig["data"], list) and fig["data"]
    assert fig["data"][0]["mode"] == "lines"
    layout = fig.get("layout", {})
    # Carrier + 2 harmonics + NSD hline = at least 4 shapes (vlines/hlines)
    shapes = layout.get("shapes", [])
    assert len(shapes) >= 4, shapes
    # Annotations include the per-component labels and the metrics card
    ann_text = " ".join(a.get("text", "") for a in layout.get("annotations", []))
    assert "HD2" in ann_text and "HD3" in ann_text
    assert "SFDR" in ann_text
