"""Plotly figure builder for annotated spectra.

Pure: takes (AnalysisResult, payload, meta) -> returns HTML string. No I/O.
"""
from __future__ import annotations

from typing import Any

import numpy as np

try:
    import plotly.graph_objects as go
except ImportError as exc:
    raise RuntimeError(
        "plotly is required for prism_report; install via "
        "pip install -e '.[prism_report]'"
    ) from exc

from test.plugins.prism_report.analyze import AnalysisResult


_CARRIER_COLOR = "red"
_HARMONIC_COLOR = "orange"
_IMD_COLOR = "purple"
_IMAGE_COLOR = "cyan"
_DC_COLOR = "gray"
_NSD_COLOR = "lightgray"


def _vline(fig: "go.Figure", x: float, label: str, color: str, dash: str):
    fig.add_vline(x=x / 1e6, line_color=color, line_dash=dash, opacity=0.6)
    fig.add_annotation(
        x=x / 1e6, y=1.0, xref="x", yref="paper",
        text=label, showarrow=False, font=dict(size=10, color=color),
        bgcolor="rgba(255,255,255,0.7)", borderpad=2,
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
    keys_of_interest = ("sample_rate", "tx_lo", "rx_lo",
                        "tx_hardwaregain_chan0", "rx_hardwaregain_chan0")
    bits = []
    for k in keys_of_interest:
        if k in params:
            bits.append(f"{k}={params[k]}")
    return " · ".join(bits)


def render_spectrum(result: AnalysisResult, payload: dict, *,
                    meta: dict[str, Any]) -> str:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=result.spectrum_freq_hz / 1e6,
        y=result.spectrum_dbfs,
        mode="lines", name="spectrum", line=dict(width=1),
    ))

    for c in result.carriers:
        _vline(fig, c.freq_hz,
               f"f0={c.freq_hz/1e6:.3f} MHz · {c.power_dbfs:.1f} dBFS",
               _CARRIER_COLOR, "solid")
    for h in result.harmonics:
        _vline(fig, h.freq_hz,
               f"{h.label} · {h.power_dbc:.1f} dBc"
               if h.power_dbc is not None
               else f"{h.label} · {h.power_dbfs:.1f} dBFS",
               _HARMONIC_COLOR, "dash")
    for i in result.imd:
        _vline(fig, i.freq_hz, f"{i.label} · {i.power_dbc:.1f} dBc",
               _IMD_COLOR, "dot")
    if result.image is not None:
        _vline(fig, result.image.freq_hz,
               f"image · {result.image.power_dbc:.1f} dBc",
               _IMAGE_COLOR, "dash")
    if result.dc is not None:
        _vline(fig, result.dc.freq_hz,
               f"DC · {result.dc.power_dbfs:.1f} dBFS",
               _DC_COLOR, "dash")
    if result.nsd_dbfs_per_hz is not None:
        fig.add_hline(y=result.nsd_dbfs_per_hz, line_color=_NSD_COLOR,
                      line_dash="dot", annotation_text="NSD",
                      annotation_position="bottom right")

    badge = ""
    if meta.get("test_failed"):
        badge = (f"<span style='color:white;background:#c00;padding:2px 6px;"
                 f"border-radius:3px;font-weight:bold;'>FAILED</span> "
                 f"{meta.get('failure_summary', '')}")

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
        annotations=list(fig.layout.annotations) + [dict(
            text=_format_metrics(result),
            x=1.0, y=1.0, xref="paper", yref="paper",
            xanchor="right", yanchor="top", showarrow=False,
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#aaa", borderwidth=1, borderpad=6,
            font=dict(family="monospace", size=11),
        )],
        margin=dict(l=60, r=20, t=80, b=50),
    )
    if result.degraded and result.notes:
        fig.add_annotation(
            text=f"⚠ {result.notes}", x=0.5, y=-0.15, xref="paper", yref="paper",
            showarrow=False, font=dict(color="#c00"),
        )
    return fig.to_html(
        include_plotlyjs="cdn", full_html=True, div_id="prism-spectrum"
    )
