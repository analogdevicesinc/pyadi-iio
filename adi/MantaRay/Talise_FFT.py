import numpy as np
import matplotlib
matplotlib.use("Agg")   # Headless backend (no GUI)
import matplotlib.pyplot as plt
from scipy.io import loadmat
from pathlib import Path

# ============================
# User parameters
# ============================

FS_HZ = 245.76e6           # ADC sample rate (Hz)
F_RF_HZ = 11e9             # RF frequency (Hz) -- for documentation
N_BP = 2048                # Spatial FFT size (zero-padding)
OUT_DIR = Path("./plots")  # Output directory

MAT_FILE = (
    "/home/snuc/Desktop/repeatability_test_elevation_all64/"
    "sample_01_elevation_raw_iq_full_64element_10GHz_20260211_152753.mat"
)

OUT_DIR.mkdir(exist_ok=True)

# ============================
# Load IQ data
# ============================

mat = loadmat(MAT_FILE)
iq = mat["all_iq_data"]

assert iq.shape == (121, 4096, 4)
assert np.iscomplexobj(iq)

print("Loaded IQ shape:", iq.shape)

# ============================
# Utility functions
# ============================

def db20(x, floor_db=-160.0):
    mag = np.abs(x)
    mag = np.maximum(mag, 10**(floor_db/20))
    return 20 * np.log10(mag)

# ============================
# SUM / DELTA FFT (time)
# ============================

def compute_sum_delta_fft(iq, fs_hz, window="hann"):
    """
    iq shape: (121, 4096, 4)
    returns:
        f        : frequency axis (Hz)
        SUM_FFT  : (121, 4096)
        DEL_FFT  : (121, 4096)
    """
    n_elem, n_samp, _ = iq.shape

    # Window
    if window == "hann":
        w = np.hanning(n_samp)
    else:
        w = np.ones(n_samp)

    # SUM
    sum_time = np.sum(iq, axis=2) * w
    SUM_FFT = np.fft.fft(sum_time, axis=1)

    # DELTA (rotate ch2, ch3 by pi)
    iq_rot = iq.copy()
    iq_rot[:, :, 1] *= -1
    iq_rot[:, :, 2] *= -1
    delta_time = np.sum(iq_rot, axis=2) * w
    DEL_FFT = np.fft.fft(delta_time, axis=1)

    f = np.fft.fftfreq(n_samp, d=1/fs_hz)

    return f, SUM_FFT, DEL_FFT

# ============================
# Compute FFTs
# ============================

f, SUM_FFT, DEL_FFT = compute_sum_delta_fft(iq, FS_HZ)

# ============================
# Pick carrier bin automatically
# ============================

k0 = np.argmax(np.mean(np.abs(SUM_FFT), axis=0))
f0 = f[k0]

print(f"Selected carrier bin: {k0}")
print(f"Carrier frequency  : {f0/1e6:.3f} MHz")

sum_snapshot = SUM_FFT[:, k0]   # (121,)
del_snapshot = DEL_FFT[:, k0]   # (121,)

# ============================
# Spatial FFT → Beampattern
# λ/2 spacing at 11 GHz
# ============================

SUM_BP = np.fft.fftshift(np.fft.fft(sum_snapshot, n=N_BP))
DEL_BP = np.fft.fftshift(np.fft.fft(del_snapshot, n=N_BP))

# u = sin(theta) for λ/2 spacing
u = np.linspace(-1.0, 1.0, N_BP)
theta_deg = np.degrees(np.arcsin(np.clip(u, -1.0, 1.0)))

# Normalize
SUM_BP_DB = db20(SUM_BP) - np.max(db20(SUM_BP))
DEL_BP_DB = db20(DEL_BP) - np.max(db20(DEL_BP))

# ============================
# Plot 1: Frequency-domain check (element 0)
# ============================

plt.figure(figsize=(11, 5))
plt.plot(f/1e6, db20(SUM_FFT[0]), label="SUM FFT")
plt.plot(f/1e6, db20(DEL_FFT[0]), label="Δ FFT")
plt.grid(True, alpha=0.3)
plt.xlabel("Frequency (MHz)")
plt.ylabel("Magnitude (dB)")
plt.title("Element 0: SUM vs Δ FFT")
plt.legend()
plt.tight_layout()

plt.savefig(OUT_DIR / "sum_vs_delta_fft_element0.png", dpi=200)
plt.close()

# ============================
# Plot 2: Beampattern
# ============================

plt.figure(figsize=(10, 5))
plt.plot(theta_deg, SUM_BP_DB, label="SUM")
plt.plot(theta_deg, DEL_BP_DB, label="Δ")
plt.ylim(-60, 0)
plt.grid(True)
plt.xlabel("Angle (deg)")
plt.ylabel("Normalized Gain (dB)")
plt.title("Rx Beampattern (λ/2 spacing @ 11 GHz)")
plt.legend()
plt.tight_layout()

plt.savefig(OUT_DIR / "rx_beampattern_sum_delta.png", dpi=200)
plt.close()

print("Plots saved to:", OUT_DIR.resolve())
