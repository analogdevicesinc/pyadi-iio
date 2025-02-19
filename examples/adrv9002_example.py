import time
import numpy as np
import adi
import matplotlib.pyplot as plt
import keyboard
import commpy.utilities as util
import komm
import scipy.io

def rcosdesign(beta, span, sps, N=None):
    """
    Generate a raised cosine (RC) filter (FIR) impulse response.

    Parameters:
    beta (float): Roll-off factor (0 <= beta <= 1).
    span (int): Number of symbol periods the filter spans.
    sps (int): Samples per symbol.
    N (int, optional): Number of taps in the filter. If None, it defaults to span * sps + 1.

    Returns:
    np.ndarray: Impulse response of the raised cosine filter.
    """
    if N is None:
        N = span * sps + 1

    t = np.linspace(-span / 2, span / 2, N)
    h = np.sinc(t) * np.cos(np.pi * beta * t) / (1 - (2 * beta * t)**2)

    # Handle the singularity at t = 0
    h[t == 0] = 1.0
    # Handle the singularity at t = ±1/(2*beta)
    singularity_indices = np.isclose(t, 1 / (2 * beta)) | np.isclose(t, -1 / (2 * beta))
    h[singularity_indices] = beta / (2 * np.sqrt(2)) * ((1 + 2 / np.pi) * np.sin(np.pi / (2 * beta)) + (1 - 2 / np.pi) * np.cos(np.pi / (2 * beta)))

    return h

sdr = adi.adrv9002(uri="ip:10.48.65.154")
sdr.tx_ensm_mode_chan0 = "rf_enabled"
sdr.tx_ensm_mode_chan1 = "rf_enabled"
sdr.tx_cyclic_buffer = True
sdr.tx0_lo = 2400000000
sdr.tx1_lo = 2400000000
sdr.tx_hardwaregain_chan0 = -10
sdr.tx_hardwaregain_chan1 = -10
sdr.tx_enabled_channels=[0]
fs = int(sdr.rx0_sample_rate)

print(fs)
fc = 50000
N = 1024
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.sin(2 * np.pi * fc * t)
q = np.cos(2 * np.pi * fc * t)

spf = 2*N  # samples per frame
sps = 8  # samples per symbol

modulation_map = {
    "0": "EXIT",
    "1": "16QAM",
    "2": "64QAM",
    "3": "8PSK",
    "5": "BPSK",
    "6": "CPFSK",
    "8": "GFSK",
    "9": "PAM4",
    "10": "QPSK",
    "11": "ORIGINAL"
}

filterCoeffs = rcosdesign(0.35, 4, sps)
M = 2


mod_8spk  = scipy.io.loadmat('modulated_data/mod_8PSK.mat')
mod_16qam = scipy.io.loadmat('modulated_data/mod_16QAM.mat')
mod_64qam = scipy.io.loadmat('modulated_data/mod_64QAM.mat')
mod_bspk  = scipy.io.loadmat('modulated_data/mod_BPSK.mat')
mod_cpfsk = scipy.io.loadmat('modulated_data/mod_CPFSK.mat')
mod_gfsk  = scipy.io.loadmat('modulated_data/mod_GFSK.mat')
mod_pam4  = scipy.io.loadmat('modulated_data/mod_PAM4.mat')
mod_qpsk  = scipy.io.loadmat('modulated_data/mod_QPSK.mat')

while True:
    modulation_number = input("Enter modulation type (1: 16QAM, 2: 64QAM, 3: 8PSK, 5: BPSK, 6: CPFSK, 8: GFSK, 9: PAM4, 10: QPSK, 11: ORIGINAL 0:EXIT): ")
    sdr.tx_destroy_buffer()
    print(modulation_number)
    modulation_type = modulation_map.get(modulation_number, "BPSK")
    print(modulation_type)

    match modulation_type:
        case "BPSK":
            data = mod_bspk['rx']
        case "QPSK":
            data = mod_qpsk['rx']
        case "8PSK":
            data = mod_8spk['rx']
        case "16QAM":
            data = mod_16qam['rx']
        case "64QAM":
            data = mod_64qam['rx']
        case "PAM4":
            data = mod_pam4['rx']
        case "GFSK":
            data = mod_gfsk['rx']
        case "CPFSK":
            data = mod_cpfsk['rx']
        case "ORIGINAL":
            iq = i + 1j * q
        case "EXIT":
            sdr.tx_destroy_buffer()
            break
        case _:
            sdr.tx_destroy_buffer()
            break

    data=data.flatten()
    iq_real = np.int16(np.real(data) * 2**12-1)
    iq_imag = np.int16(np.imag(data) * 2**12-1)
    iq = iq_real + 1j * iq_imag
    sdr.tx(iq)
    # plt.figure()
    # plt.subplot(2, 1, 1)
    # plt.plot(data)
    # plt.subplot(2, 1, 2)
    # plt.plot(iq)
    # plt.tight_layout()
    # plt.show()












