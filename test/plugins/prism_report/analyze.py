"""Spectrum + Fourier-Analysis wrapper.

Uses genalyzer.simplified_beta when available, falls back to a numpy FFT
(unannotated) otherwise. Pure: takes a dict, returns a dataclass. No I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

try:
    import genalyzer
    _GENALYZER: Any = genalyzer
except ImportError:
    _GENALYZER = None


class PayloadError(ValueError):
    """Payload from `pytest.data_log` is missing required keys."""


@dataclass(frozen=True)
class Component:
    label: str            # "carrier", "HD2", "IMD3 (2f1-f2)", "image", "DC"
    freq_hz: float
    power_dbfs: float
    power_dbc: float | None  # None for carrier; dBc relative to fundamental
    order: int | None        # harmonic order; None for non-harmonics


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
        carriers.append(Component(
            label="carrier",
            freq_hz=freq_for_carrier,
            power_dbfs=fund_dbfs if i == 0 else float("nan"),
            power_dbc=None,
            order=None,
        ))
    for k in (2, 3, 4, 5):
        key = f"{k}A:ffinal"
        f_h = fa.get(key)
        if f_h is None:
            continue
        amp = _safe_float(fa, f"{k}A:mag_dbfs")
        if amp is None:
            amp = _safe_float(fa, f"{k}A:mag_dbc")
        harmonics.append(Component(
            label=f"HD{k}",
            freq_hz=float(f_h),
            power_dbfs=amp if amp is not None else float("nan"),
            power_dbc=_safe_float(fa, f"{k}A:mag_dbc"),
            order=k,
        ))
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
            spectrum_freq_hz=freq, spectrum_dbfs=dbfs,
            degraded=True,
            notes=("genalyzer unavailable" if _GENALYZER is None
                   else "no expected_tones supplied"),
        )

    try:
        freq, dbfs, carriers, harmonics, metrics = _genalyzer_analyze(
            iq, fs, expected_tones
        )
    except Exception as exc:
        freq, dbfs = _numpy_spectrum_complex(iq, fs)
        return AnalysisResult(
            spectrum_freq_hz=freq, spectrum_dbfs=dbfs,
            degraded=True, notes=f"genalyzer FA failed: {exc}",
        )

    return AnalysisResult(
        spectrum_freq_hz=freq, spectrum_dbfs=dbfs,
        carriers=carriers, harmonics=harmonics,
        sfdr_dbc=metrics.get("sfdr_dbc"),
        snr_db=metrics.get("snr_db"),
        sinad_db=metrics.get("sinad_db"),
        thd_dbc=metrics.get("thd_dbc"),
        nsd_dbfs_per_hz=metrics.get("nsd_dbfs_per_hz"),
        degraded=False,
    )
