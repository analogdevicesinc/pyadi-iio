# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD
"""IQ analyzer + spectrum renderer for the pytest-prism plugin.

Bundles the genalyzer Fourier-Analysis call and the Plotly figure builder
behind a single `IQRenderer` class registered as the `"adi.iq"` payload kind.

Payload contract (matches the legacy pytest.data_log shape):
    {
      "iq": np.ndarray,           # complex or real samples
      "fs": float,                # sample rate Hz
      "domain": "complex" | "real",
      "expected_tones": [float],  # Hz
      "metrics": {...},           # passed through to metrics.json
      "params": {...},            # optional, passed through
    }
"""
from __future__ import annotations

import io
import json as _json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
from pytest_prism import RenderContext, RenderResult

# ---------- BEGIN: contents from analyze.py ----------

try:
    import genalyzer

    _GENALYZER: Any = genalyzer
except ImportError:
    _GENALYZER = None


class PayloadError(ValueError):
    """Payload from `pytest.data_log` is missing required keys."""


@dataclass(frozen=True)
class Component:
    label: str  # "carrier", "HD2", "IMD3 (2f1-f2)", "image", "DC"
    freq_hz: float
    power_dbfs: float
    power_dbc: float | None  # None for carrier; dBc relative to fundamental
    order: int | None  # harmonic order; None for non-harmonics


@dataclass(frozen=True)
class AnalysisResult:
    spectrum_freq_hz: np.ndarray
    spectrum_dbfs: np.ndarray
    carriers: list[Component] = field(default_factory=list)
    harmonics: list[Component] = field(default_factory=list)
    imd: list[Component] = field(default_factory=list)
    image: Component | None = None
    dc: Component | None = None
    sfdr_dbc: float | None = None
    snr_db: float | None = None
    sinad_db: float | None = None
    thd_dbc: float | None = None
    nsd_dbfs_per_hz: float | None = None
    degraded: bool = False
    notes: str = ""


def _require(payload: dict, key: str) -> Any:
    if key not in payload or payload[key] is None:
        raise PayloadError(f"prism_report payload missing required key: {key!r}")
    return payload[key]


def _numpy_spectrum_complex(iq: np.ndarray, fs: float):
    n = len(iq)
    win = np.hanning(n)
    spectrum = np.fft.fftshift(np.fft.fft(iq * win) / n)
    freq = np.fft.fftshift(np.fft.fftfreq(n, d=1.0 / fs))
    full_scale = float(2 ** 15)
    dbfs = 20 * np.log10(np.maximum(np.abs(spectrum), 1e-30) / full_scale)
    return freq, dbfs


# -----------------------------------------------------------------------------
# Genalyzer FA result keys verified against installed binding (genalyzer 0.1.2,
# simplified_beta) on 2026-04-30 by probe in
# /home/tcollins/dev/test_capture/genalyzer/bindings/python/examples/simplified_beta/do_fourier_analysis.py.
#
# Top-level metrics keys: "sfdr", "snr", "sinad", "nsd", "fsnr", "abn".
#   NOTE: there is no "thd" key in the dict; THD is only available via
#   sb.get_fa_single_result("thd", ...).
# Per-tone keys are colon-delimited:
#   fundamental:   "A:ffinal", "A:freq", "A:mag_dbfs", "A:mag_dbc", "A:tag"
#   harmonics:     "{k}A:ffinal", "{k}A:mag_dbfs", "{k}A:mag_dbc"  (k=2,3,4,5)
#   neg-image:     "-A:ffinal", "-A:mag_dbfs", ...
#   dc:            "dc:ffinal", "dc:mag_dbfs", ...
#   worst-other:   "wo:ffinal", "wo:mag_dbfs", ...
# -----------------------------------------------------------------------------
def _genalyzer_analyze(iq: np.ndarray, fs: float, expected_tones: list[float]):
    """Return (freq_hz, dbfs, carriers, harmonics, metrics_dict)."""
    sb = _GENALYZER.simplified_beta
    n = len(iq)
    nfft = n
    navg = 1
    qres = 16
    win = 1  # Hann (genalyzer enum offset by -1 in the example)
    cfg = sb.config_fftz(n, qres, navg, nfft, win - 1)
    qi = np.real(iq).astype(np.int32).tolist()
    qq = np.imag(iq).astype(np.int32).tolist()
    fft_i, fft_q = sb.fftz(qi, qq, cfg)
    interleaved = [v for pair in zip(fft_i, fft_q) for v in pair]
    sb.config_set_sample_rate(fs, cfg)
    sb.config_fa(expected_tones[0], cfg)
    fa = sb.get_fa_results(interleaved, cfg)
    # THD is not exposed in the result dict; fetch it as a single result.
    try:
        thd_db = float(sb.get_fa_single_result("thd", interleaved, cfg))
    except Exception:
        thd_db = None
    sb.config_free(cfg)

    # Spectrum (one-sided complex magnitude in dBFS)
    fft_complex = np.array(fft_i) + 1j * np.array(fft_q)
    freq = np.fft.fftshift(np.fft.fftfreq(n, d=1.0 / fs))
    full_scale = float(2 ** (qres - 1))
    dbfs = 20 * np.log10(
        np.maximum(np.abs(np.fft.fftshift(fft_complex) / n), 1e-30) / full_scale
    )

    carriers: list[Component] = []
    harmonics: list[Component] = []
    metrics = {
        "sfdr_dbc": _safe_float(fa, "sfdr"),
        "snr_db": _safe_float(fa, "snr"),
        "sinad_db": _safe_float(fa, "sinad"),
        "thd_dbc": thd_db,
        "nsd_dbfs_per_hz": _safe_float(fa, "nsd"),
    }
    fund_dbfs = _safe_float(fa, "A:mag_dbfs")
    if fund_dbfs is None:
        fund_dbfs = 0.0
    fund_freq = _safe_float(fa, "A:ffinal")
    for i, f in enumerate(expected_tones):
        # Use genalyzer-reported fundamental for the first carrier; for
        # additional tones (two-tone case) genalyzer's single-fundamental
        # FA call doesn't enumerate them, so report the requested freq.
        freq_for_carrier = fund_freq if (i == 0 and fund_freq is not None) else float(f)
        carriers.append(
            Component(
                label="carrier",
                freq_hz=freq_for_carrier,
                power_dbfs=fund_dbfs if i == 0 else float("nan"),
                power_dbc=None,
                order=None,
            )
        )
    for k in (2, 3, 4, 5):
        key = f"{k}A:ffinal"
        f_h = fa.get(key)
        if f_h is None:
            continue
        amp = _safe_float(fa, f"{k}A:mag_dbfs")
        if amp is None:
            amp = _safe_float(fa, f"{k}A:mag_dbc")
        harmonics.append(
            Component(
                label=f"HD{k}",
                freq_hz=float(f_h),
                power_dbfs=amp if amp is not None else float("nan"),
                power_dbc=_safe_float(fa, f"{k}A:mag_dbc"),
                order=k,
            )
        )
    return freq, dbfs, carriers, harmonics, metrics


def _safe_float(d: dict, key: str):
    v = d.get(key)
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return None


def analyze(payload: dict) -> AnalysisResult:
    iq = _require(payload, "iq")
    fs = float(_require(payload, "fs"))
    domain = payload.get("domain", "complex")
    expected_tones = list(payload.get("expected_tones") or [])

    iq = np.asarray(iq)
    if domain == "complex" and not np.iscomplexobj(iq):
        raise PayloadError("domain='complex' but iq is not complex")

    if _GENALYZER is None or not expected_tones:
        freq, dbfs = _numpy_spectrum_complex(iq, fs)
        return AnalysisResult(
            spectrum_freq_hz=freq,
            spectrum_dbfs=dbfs,
            degraded=True,
            notes=(
                "genalyzer unavailable"
                if _GENALYZER is None
                else "no expected_tones supplied"
            ),
        )

    try:
        freq, dbfs, carriers, harmonics, metrics = _genalyzer_analyze(
            iq, fs, expected_tones
        )
    except Exception as exc:
        freq, dbfs = _numpy_spectrum_complex(iq, fs)
        return AnalysisResult(
            spectrum_freq_hz=freq,
            spectrum_dbfs=dbfs,
            degraded=True,
            notes=f"genalyzer FA failed: {exc}",
        )

    return AnalysisResult(
        spectrum_freq_hz=freq,
        spectrum_dbfs=dbfs,
        carriers=carriers,
        harmonics=harmonics,
        sfdr_dbc=metrics.get("sfdr_dbc"),
        snr_db=metrics.get("snr_db"),
        sinad_db=metrics.get("sinad_db"),
        thd_dbc=metrics.get("thd_dbc"),
        nsd_dbfs_per_hz=metrics.get("nsd_dbfs_per_hz"),
        degraded=False,
    )


# ---------- END: contents from analyze.py ----------


# ---------- BEGIN: contents from render.py ----------

try:
    import plotly.graph_objects as go
except ImportError as exc:
    raise RuntimeError(
        "plotly is required for prism_report; install via "
        "pip install -e '.[prism_report]'"
    ) from exc


_CARRIER_COLOR = "red"
_HARMONIC_COLOR = "orange"
_IMD_COLOR = "purple"
_IMAGE_COLOR = "cyan"
_DC_COLOR = "gray"
_NSD_COLOR = "lightgray"


def _vline(fig: "go.Figure", x: float, label: str, color: str, dash: str):
    fig.add_vline(x=x / 1e6, line_color=color, line_dash=dash, opacity=0.6)
    fig.add_annotation(
        x=x / 1e6,
        y=1.0,
        xref="x",
        yref="paper",
        text=label,
        showarrow=False,
        font=dict(size=10, color=color),
        bgcolor="rgba(255,255,255,0.7)",
        borderpad=2,
    )


def _format_metrics(r: AnalysisResult) -> str:
    parts = []
    if r.sfdr_dbc is not None:
        parts.append(f"SFDR {r.sfdr_dbc:.1f} dBc")
    if r.snr_db is not None:
        parts.append(f"SNR {r.snr_db:.1f} dB")
    if r.sinad_db is not None:
        parts.append(f"SINAD {r.sinad_db:.1f} dB")
    if r.thd_dbc is not None:
        parts.append(f"THD {r.thd_dbc:.1f} dBc")
    if r.nsd_dbfs_per_hz is not None:
        parts.append(f"NSD {r.nsd_dbfs_per_hz:.1f} dBFS/Hz")
    return " · ".join(parts) if parts else "(no FA metrics)"


def _format_params(params: dict) -> str:
    if not params:
        return ""
    keys_of_interest = (
        "sample_rate",
        "tx_lo",
        "rx_lo",
        "tx_hardwaregain_chan0",
        "rx_hardwaregain_chan0",
    )
    bits = []
    for k in keys_of_interest:
        if k in params:
            bits.append(f"{k}={params[k]}")
    return " · ".join(bits)


def _build_spectrum_figure(
    result: AnalysisResult, payload: dict, *, meta: dict[str, Any]
) -> "go.Figure":
    """Build the annotated spectrum figure. Pure: numpy + Plotly types only."""
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=result.spectrum_freq_hz / 1e6,
            y=result.spectrum_dbfs,
            mode="lines",
            name="spectrum",
            line=dict(width=1),
        )
    )

    for c in result.carriers:
        _vline(
            fig,
            c.freq_hz,
            f"f0={c.freq_hz / 1e6:.3f} MHz · {c.power_dbfs:.1f} dBFS",
            _CARRIER_COLOR,
            "solid",
        )
    for h in result.harmonics:
        _vline(
            fig,
            h.freq_hz,
            f"{h.label} · {h.power_dbc:.1f} dBc"
            if h.power_dbc is not None
            else f"{h.label} · {h.power_dbfs:.1f} dBFS",
            _HARMONIC_COLOR,
            "dash",
        )
    for i in result.imd:
        _vline(fig, i.freq_hz, f"{i.label} · {i.power_dbc:.1f} dBc", _IMD_COLOR, "dot")
    if result.image is not None:
        _vline(
            fig,
            result.image.freq_hz,
            f"image · {result.image.power_dbc:.1f} dBc",
            _IMAGE_COLOR,
            "dash",
        )
    if result.dc is not None:
        _vline(
            fig,
            result.dc.freq_hz,
            f"DC · {result.dc.power_dbfs:.1f} dBFS",
            _DC_COLOR,
            "dash",
        )
    if result.nsd_dbfs_per_hz is not None:
        fig.add_hline(
            y=result.nsd_dbfs_per_hz,
            line_color=_NSD_COLOR,
            line_dash="dot",
            annotation_text="NSD",
            annotation_position="bottom right",
        )

    badge = ""
    if meta.get("test_failed"):
        badge = (
            f"<span style='color:white;background:#c00;padding:2px 6px;"
            f"border-radius:3px;font-weight:bold;'>FAILED</span> "
            f"{meta.get('failure_summary', '')}"
        )

    title = f"{meta.get('test_id', '?')} · {payload.get('classname', '?')}"
    params_line = _format_params(payload.get("params") or {})
    if params_line:
        title += f"<br><span style='font-size:0.7em;color:#666;'>{params_line}</span>"
    if badge:
        title = f"{badge}<br>{title}"

    fig.update_layout(
        title=dict(text=title, x=0.0, xanchor="left"),
        xaxis_title="Frequency (MHz)",
        yaxis_title="Power (dBFS)",
        annotations=list(fig.layout.annotations)
        + [
            dict(
                text=_format_metrics(result),
                x=1.0,
                y=1.0,
                xref="paper",
                yref="paper",
                xanchor="right",
                yanchor="top",
                showarrow=False,
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#aaa",
                borderwidth=1,
                borderpad=6,
                font=dict(family="monospace", size=11),
            )
        ],
        margin=dict(l=60, r=20, t=80, b=50),
    )
    if result.degraded and result.notes:
        fig.add_annotation(
            text=f"⚠ {result.notes}",
            x=0.5,
            y=-0.15,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(color="#c00"),
        )
    return fig


def render_spectrum(
    result: AnalysisResult, payload: dict, *, meta: dict[str, Any]
) -> str:
    """Render the annotated spectrum to a self-contained HTML string."""
    fig = _build_spectrum_figure(result, payload, meta=meta)
    return fig.to_html(include_plotlyjs="cdn", full_html=True, div_id="prism-spectrum")


def render_spectrum_figure_json(
    result: AnalysisResult, payload: dict, *, meta: dict[str, Any]
) -> str:
    """Render the same annotated spectrum as a Plotly figure JSON spec.

    Suitable for fetching and rendering inline in a host UI (e.g. via
    react-plotly.js) without the iframe + content-type gymnastics that
    a full HTML payload requires.
    """
    fig = _build_spectrum_figure(result, payload, meta=meta)
    return fig.to_json()


# ---------- END: contents from render.py ----------


# ---------- IQRenderer wrapper ----------


class IQRenderer:
    """Renderer for the `"adi.iq"` payload kind."""

    payload_kind: ClassVar[str] = "adi.iq"

    def render(self, payload: Mapping[str, Any], ctx: RenderContext) -> RenderResult:
        result = analyze(dict(payload))
        meta = {
            "test_id": ctx.case_id,
            "test_failed": False,
            "failure_summary": "",
        }
        html = render_spectrum(result, dict(payload), meta=meta)
        figure_json = render_spectrum_figure_json(result, dict(payload), meta=meta)
        (ctx.case_dir / "spectrum.html").write_bytes(html.encode("utf-8"))
        (ctx.case_dir / "spectrum.json").write_bytes(figure_json.encode("utf-8"))

        iq_buf = io.BytesIO()
        np.savez_compressed(
            iq_buf,
            iq=np.asarray(payload["iq"]),
            fs=np.float64(payload["fs"]),
            expected_tones=np.array(payload.get("expected_tones") or []),
            domain=np.array(payload.get("domain", "complex")),
        )
        (ctx.case_dir / "iq.npz").write_bytes(iq_buf.getvalue())

        metrics = {
            "sfdr_dbc": result.sfdr_dbc,
            "snr_db": result.snr_db,
            "sinad_db": result.sinad_db,
            "thd_dbc": result.thd_dbc,
            "nsd_dbfs_per_hz": result.nsd_dbfs_per_hz,
            "test_metrics": payload.get("metrics", {}),
        }
        return RenderResult(
            files=[Path("spectrum.html"), Path("spectrum.json"), Path("iq.npz")],
            metrics={
                k: float(v) for k, v in metrics.items() if isinstance(v, (int, float))
            },
            primary_artifact="spectrum.html",
        )
