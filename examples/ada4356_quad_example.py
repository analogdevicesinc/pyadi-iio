# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Quad ADA4356 — TDD-synchronized capture, per-channel signal quality, inter-channel skew.

A sinewave connected to J11 (distributed to all four ADC inputs) is used to
measure both the signal quality of each channel and the phase offset between
channels B/C/D relative to channel A.

Front-end note: the ADA4356 is a photodiode front end.  Its quiescent code sits
near the top of the ADC range, so the generator needs a DC offset of roughly
half its amplitude or the sine clips against +8191 regardless of gain.  At
GSEL=00 (133k) the working point is about 1.0 Vpp with +0.5 V offset.

Usage:
  python3 ada4356_quad_example.py ip:192.168.2.1
  python3 ada4356_quad_example.py ip:192.168.2.1 65536
  python3 ada4356_quad_example.py ip:192.168.2.1 65536 1000000
"""

import sys
import time

import matplotlib.pyplot as plt
import numpy as np

import adi

uri = sys.argv[1] if len(sys.argv) > 1 else "ip:192.168.2.1"
buffer_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 65536
sine_freq_hz = float(sys.argv[3]) if len(sys.argv) > 3 else 1_000_000.0

TDD_CLOCK_HZ = 125_000_000
FULL_SCALE = 8192.0  # 14-bit signed, +-8192 codes = +-1 V
N_HARMONICS = 9  # harmonics 2..9 are fitted and removed from the noise estimate

# Connect
dev = adi.ada4356_quad(uri=uri)
dev.rx_buffer_size = buffer_samples
fs = dev.sampling_frequency

TDD_ON_BASE = 100
TDD_OFF_BASE = 200

# Configure TDD — 1-second frame, all four DMA sync pulses fire at cycle 100.
# The 1-second frame gives all four Python threads plenty of time to arm and
# wait for the next rising edge, matching the dual-board ZCU102 approach.
tdd = dev.tdd
tdd.enable = False
tdd.burst_count = 0
tdd.frame_length_raw = TDD_CLOCK_HZ  # 1 s
tdd.channel[0].enable = False
for ch_idx in range(1, 5):
    tdd.channel[ch_idx].on_raw = TDD_ON_BASE
    tdd.channel[ch_idx].off_raw = TDD_OFF_BASE
    tdd.channel[ch_idx].enable = True
tdd.enable = True
try:
    tdd.sync_soft = True
except Exception:
    pass

time.sleep(0.3)

# Synchronized capture — all four DMAs armed concurrently, start on same TDD pulse
data = dev.rx()

labels = ["A", "B", "C", "D"]
colors = ["tab:blue", "tab:orange", "tab:green", "tab:red"]

N = buffer_samples
n = np.arange(N)
raw = [ch.astype(np.float64) for ch in data]


def design_matrix(f0, n_harm):
    """[DC, cos(w), sin(w), cos(2w), sin(2w), ...] for harmonics within Nyquist."""
    cols = [np.ones(N)]
    for h in range(1, n_harm + 1):
        if f0 * h >= fs / 2:
            break
        w = 2 * np.pi * f0 * h * n / fs
        cols.append(np.cos(w))
        cols.append(np.sin(w))
    return np.column_stack(cols)


def fit_at(x, f0, n_harm=N_HARMONICS):
    """Least-squares fit of DC + fundamental + harmonics at a fixed f0.

    Amplitude is taken from the fit, never by summing FFT bins: with a window
    the leakage spans several bins and summing their power overstates the
    amplitude by ~30%.  Solved via the normal equations — the design matrix is
    at most 19 columns, and this is ~10x faster than the SVD in lstsq.
    """
    A = design_matrix(f0, n_harm)
    coef = np.linalg.solve(A.T @ A, A.T @ x)
    model = A @ coef
    resid = x - model
    dc = coef[0]
    amps = np.hypot(coef[1::2], coef[2::2])
    phase = np.degrees(np.arctan2(-coef[2], coef[1]))
    return dc, amps, phase, resid, model


# --- Estimate the true tone frequency from channel A -------------------------
# The generator is never exactly on the requested frequency, and the fit is very
# sensitive to this: over a 0.5 ms record a 200 Hz error slips the model by 40
# degrees end-to-end, which lands in the residual and inflates every noise
# number by two orders of magnitude.  f0 needs to be right to ~1 Hz.
#
# A 3-point interpolation on the windowed FFT is NOT good enough here (it was
# 219 Hz out in test).  Search the windowed DFT directly instead, hierarchically
# so it stays a few seconds rather than half a minute.
window = np.hanning(N)
ac = [x - np.mean(x) for x in raw]
bin_hz = fs / N


def estimate_f0(x, f_req):
    """Hierarchical peak search on |windowed DFT|, refined against fit residual.

    Bounded to +-2 bins around the requested frequency on purpose: an
    unconstrained argmax over the whole spectrum will happily lock onto a
    spurious tone and produce a stable, reproducible, completely wrong answer.
    """
    xw = x * window

    def mag(f):
        return np.abs(np.dot(xw, np.exp(-2j * np.pi * f * n / fs)))

    lo, hi = f_req - 2 * bin_hz, f_req + 2 * bin_hz
    for _ in range(3):
        grid = np.linspace(max(lo, 1.0), hi, 41)
        m = np.array([mag(f) for f in grid])
        i = int(np.argmax(m))
        step = grid[1] - grid[0]
        lo, hi = grid[i] - step, grid[i] + step
    if 0 < i < len(grid) - 1:
        y0, y1, y2 = m[i - 1], m[i], m[i + 1]
        coarse = grid[i] + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2) * step
    else:
        coarse = grid[i]

    fine = coarse + np.linspace(-step, step, 11)
    return fine[int(np.argmin([np.std(fit_at(x, f)[3]) for f in fine]))]


f0 = estimate_f0(ac[0], sine_freq_hz)
fund_bin = int(round(f0 * N / fs))

# --- Fit every channel at the SAME f0 so the phases are comparable -----------
fits = [fit_at(x, f0) for x in raw]

print(f"\nSampling frequency : {fs / 1e6:.3f} MHz")
print(f"Buffer size        : {buffer_samples} samples ({buffer_samples / fs * 1e3:.3f} ms)")
print(f"Requested tone     : {sine_freq_hz / 1e3:.3f} kHz")
print(f"Fitted tone        : {f0 / 1e3:.6f} kHz  ({f0 * N / fs:.3f} bins, {f0 * N / fs:.2f} cycles)")

# --- Signal quality ----------------------------------------------------------
print("\n=== Signal quality (least-squares fit, harmonics 2..%d removed) ===" % N_HARMONICS)
print(
    f"{'Ch':>3}  {'ampl':>8}  {'dBFS':>7}  {'offset':>8}  {'noise':>7}  "
    f"{'SNR/FS':>7}  {'THD':>8}  {'SFDR':>7}  {'SINAD':>7}  {'ENOB':>6}  {'codes':>6}"
)

quality = []
for label, x, (dc, amps, phase, resid, model) in zip(labels, raw, fits):
    a1 = amps[0]
    harm = amps[1:]
    noise_rms = np.std(resid)

    # Largest non-harmonic spur, from the spectrum of the residual.
    # Mask DC and every fitted harmonic: the fit always leaves a little residue
    # in those bins and it would otherwise be reported as the worst spur.
    rspec = np.abs(np.fft.rfft(resid * window)) * 4.0 / N  # Hann coherent gain 0.5
    rspec[:10] = 0.0
    for h in range(1, N_HARMONICS + 1):
        b = int(round(f0 * h * N / fs))
        if b < len(rspec):
            rspec[max(0, b - 5): b + 6] = 0.0
    spur = rspec.max()
    spur_hz = np.fft.rfftfreq(N, 1.0 / fs)[int(np.argmax(rspec))]

    worst = max(spur, harm.max() if harm.size else 0.0)
    sfdr = 20 * np.log10(a1 / worst) if worst > 0 else np.inf
    thd = 10 * np.log10(np.sum(harm ** 2) / a1 ** 2) if harm.size else -np.inf
    snr_fs = 20 * np.log10((FULL_SCALE / np.sqrt(2)) / noise_rms)
    sinad = 10 * np.log10(
        (a1 ** 2 / 2) / (noise_rms ** 2 + np.sum(harm ** 2) / 2)
    )
    # ENOB referred to full scale, so a small signal is not penalised twice
    sinad_fs = sinad + 20 * np.log10(FULL_SCALE / a1)
    enob = (sinad_fs - 1.76) / 6.02
    distinct = len(np.unique(data[labels.index(label)]))

    quality.append((a1, dc, noise_rms, spur, spur_hz, harm, sfdr, thd, sinad_fs, enob))
    print(
        f"{label:>3}  {a1:>8.1f}  {20 * np.log10(a1 / FULL_SCALE):>7.2f}  {dc:>8.1f}  "
        f"{noise_rms:>7.2f}  {snr_fs:>7.2f}  {thd:>8.2f}  {sfdr:>7.2f}  "
        f"{sinad_fs:>7.2f}  {enob:>6.2f}  {distinct:>6}"
    )

print("  ampl/offset/noise in ADC codes · dB values in dB · ENOB referred to full scale")

clipped = [
    label for label, x in zip(labels, raw)
    if np.max(x) >= FULL_SCALE - 1 or np.min(x) <= -FULL_SCALE + 1
]
if clipped:
    print(f"\n  *** CLIPPING on channel(s) {', '.join(clipped)} — every number above is invalid.")
    print("  *** Reduce the generator amplitude and/or adjust its DC offset.")

# Harmonic breakdown
print("\n=== Harmonic content (dBc relative to the fundamental) ===")
hdr = "  ".join(f"{'H' + str(h):>7}" for h in range(2, N_HARMONICS + 1))
print(f"{'Ch':>3}  {hdr}   worst spur")
for label, (a1, dc, nr, spur, spur_hz, harm, *_rest) in zip(labels, quality):
    cells = "  ".join(
        f"{20 * np.log10(h / a1):>7.1f}" if h > 0 else f"{'-':>7}" for h in harm
    )
    print(f"{label:>3}  {cells}   {20 * np.log10(spur / a1):>6.1f} dBc @ {spur_hz / 1e6:.3f} MHz")

# =============================================================================
# Residual autocorrelation — the one thing the spectrum cannot show you
# -----------------------------------------------------------------------------
# A residual with periodic structure reaches the FFT as nothing more than a
# raised, featureless noise floor, so the spectrum can tell you the noise number
# is bad but never why.  Splitting the residual into a white part and a
# correlated part separates "this converter is noisy" from "this board has one
# narrowband intruder on it", and those two have opposite fixes.
# =============================================================================

MAX_LAG = 64
STRUCTURAL_LAGS = (1, 2, 4, 8, 16)


def autocorrelation(r, max_lag=MAX_LAG):
    """Normalised autocorrelation of the residual, via Wiener-Khinchin.

    O(N log N).  The np.correlate(mode="full") that used to live in this file
    was O(N^2) and hung for tens of minutes at N=65536.

    This is NOT the cross-correlation that was deliberately deleted from the
    skew section.  That one raced the FFT phase to answer the same question and
    lost.  This one asks a question the FFT does not answer: after the tone and
    its harmonics have been fitted out, is what remains actually white?
    """
    r = r - r.mean()
    nfft = 1 << int(np.ceil(np.log2(2 * r.size)))
    s = np.fft.rfft(r, nfft)
    ac = np.fft.irfft(np.abs(s) ** 2, nfft)[: max_lag + 1]
    return ac / ac[0]


sig_bound = 3.0 / np.sqrt(N)
acfs = [autocorrelation(f[3]) for f in fits]

print("\n=== Residual autocorrelation — is the leftover noise white? ===")
print(f"White noise gives |r| < {sig_bound:.4f} (3 sigma at N={N}) for every lag > 0")
print(f"\n{'Ch':>3}  " + "  ".join(f"{'lag' + str(L):>8}" for L in STRUCTURAL_LAGS)
      + "   other significant lags")
for label, acf in zip(labels, acfs):
    cells = "  ".join(f"{acf[L]:>8.4f}" for L in STRUCTURAL_LAGS)
    other = [L for L in range(1, MAX_LAG + 1)
             if abs(acf[L]) > sig_bound and L not in STRUCTURAL_LAGS]
    tail = ", ".join(str(L) for L in other[:8]) + (" ..." if len(other) > 8 else "")
    print(f"{label:>3}  {cells}   {tail if other else '-'}")

print("""
  lag 1 alone            -> band-limited noise; expected with FREQ_SEL=1, whose
                            filter is worth 1.3 ENOB and is meant to be on
  lag 4 and multiples    -> BUFR /4 divided-clock artefact
  lag 8 and multiples    -> 8:1 SERDES word boundary
  broad decaying tail    -> the residual is one narrowband thing, not noise;
                            the table below says what and how much""")

# A decaying ACF means the residual is dominated by something narrowband, and the
# `noise` column in the signal-quality table is then mostly THAT, not converter
# noise.  Split it: write resid = slow + white.  A component slow enough to be
# correlated at lag 1 contributes ~acf[1] of the variance, so the white part is
# var * (1 - acf[1]).  Its frequency follows from the ACF's first zero crossing,
# which for a narrowband process sits at a quarter period.
print(f"\n{'Ch':>3}  {'resid rms':>9}  {'white':>7}  {'correlated':>10}  "
      f"{'dominant':>10}  what the 'noise' column is actually measuring")
SMOOTH_ACF1 = 0.5
acf_summary = []  # (zero-crossing lag, dominant Hz, correlated fraction) per channel
for label, acf, (dc, amps, phase, resid, model) in zip(labels, acfs, fits):
    tot = np.std(resid)
    worst_lag = int(np.argmax(np.abs(acf[1:]))) + 1
    dom = None
    zc = None
    if abs(acf[worst_lag]) < sig_bound:
        white, verdict = tot, "white — the noise column is real converter noise"
    elif acf[1] < SMOOTH_ACF1:
        # Structured but not smooth: the lag-1 split assumes the correlated part
        # is still correlated at lag 1, which is false here, so do not guess.
        white, verdict = (float("nan"),
                          f"structured at lag {worst_lag} (r={acf[worst_lag]:+.3f}) — "
                          f"not smooth, so no split; see the lag table")
    else:
        white = min(tot * np.sqrt(max(1.0 - acf[1], 0.0)), tot)
        neg = np.flatnonzero(acf[1:] < 0)
        if neg.size == 0:
            verdict = (f"one slow component below {fs / (4 * MAX_LAG) / 1e6:.2f} MHz; "
                       "raise MAX_LAG to localise it")
        else:
            z = neg[0] + 1
            zc = z - 1 + acf[z - 1] / (acf[z - 1] - acf[z])
            dom = fs / (4 * zc)
            verdict = ("f0 is mis-fitted — fix estimate_f0, not a board fault"
                       if abs(dom - f0) < 0.2 * f0 else
                       f"a spur near {dom / 1e6:.2f} MHz, not noise; true SNR/FS "
                       f"{20 * np.log10(FULL_SCALE / np.sqrt(2) / white):.1f} dB")
    corr = np.sqrt(max(tot ** 2 - white ** 2, 0.0)) if white == white else float("nan")
    acf_summary.append((zc, dom, (corr / tot) ** 2 if corr == corr else float("nan")))
    fmt = lambda v: f"{v:.2f}" if v == v else "—"
    print(f"{label:>3}  {tot:>9.2f}  {fmt(white):>7}  {fmt(corr):>10}  "
          f"{(f'{dom / 1e6:.3f} MHz' if dom else '—'):>10}  {verdict}")
print("  The split assumes the correlated part is smooth at lag 1, which the"
      "\n  decaying ACF itself establishes. Cross-check 'dominant' against the"
      "\n  worst-spur column in the harmonic table — they should agree.")

# --- Inter-channel skew ------------------------------------------------------
# One sample is 360 * f0 / fs degrees.  If that is comparable to the run-to-run
# phase scatter the sample column is meaningless — this is the trap that
# produced three separate false skew results at 10 kHz.
deg_per_sample = 360.0 * f0 / fs
print("\n=== Inter-channel skew (vs channel A) ===")
print(f"1 sample = {deg_per_sample:.4f} deg at this tone; "
      f"unambiguous range +-{180.0 / deg_per_sample:.0f} samples")
print(f"\n{'Ch':>3}  {'phase (deg)':>12}  {'offset (deg)':>13}  {'skew (samp)':>12}  {'skew (ns)':>11}")
for label, (dc, amps, phase, resid, model) in zip(labels, fits):
    offset_deg = (phase - fits[0][2] + 180) % 360 - 180
    skew_samples = offset_deg / 360.0 * (fs / f0)
    print(
        f"{label:>3}  {phase:>12.3f}  {offset_deg:>13.3f}  "
        f"{skew_samples:>12.4f}  {skew_samples / fs * 1e9:>11.2f}"
    )

print("\n  To classify a non-zero skew, re-run at 10x the tone frequency:")
print("    skew in SAMPLES stays constant  -> digital/SERDES delay")
print("    skew in DEGREES stays constant  -> analog front-end pole mismatch")

# Cross-correlation was removed deliberately: on a clean sine it is algebraically
# identical to the FFT phase result, and np.correlate is dragged toward zero lag by
# the noise the channels share, so it reads as corroboration while being strictly
# worse. It was also O(N^2) and hung at N=65536.

print(f"\n{'Ch':>3}  {'mean':>10}  {'std':>10}  {'min':>10}  {'max':>10}")
for label, ch_data in zip(labels, data):
    print(
        f"{label:>3}  {np.mean(ch_data):>10.1f}  {np.std(ch_data):>10.1f}"
        f"  {int(np.min(ch_data)):>10}  {int(np.max(ch_data)):>10}"
    )

# --- Plot: time domain across the top, one FFT per channel below -------------
zoom_n = min(int(fs / f0 * 5), N)
t_us = np.arange(zoom_n) / fs * 1e6
freq_axis = np.fft.rfftfreq(N, d=1.0 / fs)
freq_mhz = freq_axis / 1e6

fig = plt.figure(figsize=(15, 11))
gs = fig.add_gridspec(3, 2, height_ratios=[1.1, 1, 1], hspace=0.38, wspace=0.18)

ax_t = fig.add_subplot(gs[0, :])
for a, label, color in zip(ac, labels, colors):
    ax_t.plot(t_us, a[:zoom_n], label=f"Ch {label}", color=color, linewidth=0.8)
ax_t.set_xlabel("Time (µs)")
ax_t.set_ylabel("ADC codes (DC removed)")
ax_t.set_title(f"TDD-synchronized capture — {f0 / 1e3:.3f} kHz — 5 periods")
ax_t.legend(loc="upper right", ncol=4)
ax_t.grid(True, alpha=0.3)

# Per-channel FFT, one subplot each so the traces never overlap
for idx, (a, label, color) in enumerate(zip(ac, labels, colors)):
    ax = fig.add_subplot(gs[1 + idx // 2, idx % 2])
    s = np.fft.rfft(a * window)
    psd = 20 * np.log10(np.abs(s) * 4 / N / FULL_SCALE + 1e-20)
    ax.plot(freq_mhz, psd, color=color, linewidth=0.6)

    a1, dc, noise_rms, spur, spur_hz, harm, sfdr, thd, sinad_fs, enob = quality[idx]

    # Mark the harmonics so distortion is visually attributable
    for h in range(2, N_HARMONICS + 1):
        fh = f0 * h
        if fh < fs / 2:
            ax.axvline(fh / 1e6, color="gray", linestyle=":", linewidth=0.6, alpha=0.7)
    ax.plot(spur_hz / 1e6, 20 * np.log10(spur / FULL_SCALE), "kv",
            markersize=5, label=f"worst spur {20 * np.log10(spur / a1):.0f} dBc")

    ax.set_title(
        f"Ch {label} — {20 * np.log10(a1 / FULL_SCALE):.1f} dBFS, "
        f"SFDR {sfdr:.1f} dB, THD {thd:.1f} dB, ENOB {enob:.2f}",
        fontsize=10,
    )
    ax.set_xlabel("Frequency (MHz)")
    ax.set_ylabel("dBFS")
    ax.set_ylim(-180, 5)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

plt.savefig("/tmp/ada4356_quad.png", dpi=150, bbox_inches="tight")
print("\nPlot saved: /tmp/ada4356_quad.png")

# --- Second figure: residual autocorrelation ---------------------------------
# The title states the FINDING rather than the decision rule: once the residual
# is dominated by a tone the white-noise band is ~1% of the axis and invisible,
# so "anything outside the band is structure" is unreadable exactly when it
# fires.  The zero crossing is the whole result, so it is drawn and labelled.
fig2, ax = plt.subplots(figsize=(11, 6.5))

for acf, label, color, (zc, dom, frac) in zip(acfs, labels, colors, acf_summary):
    tag = f"Ch {label} — $r_1$={acf[1]:.3f}"
    if frac == frac:
        tag += f", {100 * frac:.0f}% correlated"
    ax.plot(np.arange(1, MAX_LAG + 1), acf[1:], color=color, linewidth=1.0,
            marker=".", markersize=3, label=tag)

ax.axhspan(-sig_bound, sig_bound, color="gray", alpha=0.35,
           label=f"white noise would live entirely inside this (±{sig_bound:.4f})")

for L in (4, 8, 16, 32):
    ax.axvline(L, color="gray", linestyle=":", linewidth=0.6)
ax.annotate("lags 4/8/16/32 = clock-divider and SERDES-word\n"
            "fault signatures; smooth here means the digital side is clean",
            xy=(0.015, 0.03), xycoords="axes fraction", fontsize=8, color="gray")

# Mark the zero crossing of whichever channel is worst affected: it is the same
# tone on every channel, so one annotation carries the result for all of them.
worst = max(range(len(acf_summary)),
            key=lambda i: acf_summary[i][2] if acf_summary[i][2] == acf_summary[i][2] else -1)
zc, dom, _frac = acf_summary[worst]
if zc is not None and dom is not None:
    ax.axvline(zc, color="k", linestyle="--", linewidth=0.9)
    ax.axhline(0.0, color="k", linewidth=0.5)
    ax.annotate(f"zero crossing at lag {zc:.1f}\n= quarter period\n"
                f"$\\rightarrow$ {dom / 1e6:.2f} MHz",
                xy=(zc, 0.0), xytext=(zc + 0.08 * MAX_LAG, 0.45),
                fontsize=9,
                arrowprops=dict(arrowstyle="->", color="k", linewidth=0.8),
                bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.75))
    headline = (f"Residual autocorrelation — the leftover is a {dom / 1e6:.2f} MHz tone, "
                "not noise")
else:
    headline = "Residual autocorrelation — leftover is white, the noise column is real"

ax.set_xlabel("Lag (samples)")
ax.set_ylabel("Normalised autocorrelation")
ax.set_title(headline)
ax.legend(fontsize=8, loc="upper right")
ax.grid(True, alpha=0.3)

plt.savefig("/tmp/ada4356_quad_diag.png", dpi=150, bbox_inches="tight")
print("Plot saved: /tmp/ada4356_quad_diag.png")

for ch in dev.channels:
    ch.rx_destroy_buffer()
