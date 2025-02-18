import time
import numpy as np
import adi
import matplotlib.pyplot as plt
import keyboard
import commpy.utilities as util
import komm

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
fs = int(sdr.rx0_sample_rate)

print(fs)
fc = 10000
N = 1024
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.sin(2 * np.pi * fc * t)
q = np.cos(2 * np.pi * fc * t)

spf = 2*N  # samples per frame
sps = 8  # samples per symbol

modulation_map = {
    "0": "EXIT",
    "1": "BPSK",
    "2": "QPSK",
    "3": "8PSK",
    "4": "16QAM",
    "5": "64QAM",
    "6": "PAM4",
    "7": "GFSK",
    "8": "CPFSK",
    "9": "ORIGINAL"
}

filterCoeffs = rcosdesign(0.35, 4, sps)
M = 2

while True:
    modulation_number = input("Enter modulation type (1: BPSK, 2: QPSK, 3: 8PSK, 4: 16QAM, 5: 64QAM, 6: PAM4, 7:GFSK, 8: CPFSK, 9: ORIGINAL, 0:EXIT): ")
    sdr.tx_destroy_buffer()
    print(modulation_number)
    modulation_type = modulation_map.get(modulation_number, "BPSK")
    print(modulation_type)

    match modulation_type:
        case "BPSK":
          modulator = komm.PSKModulation(2)
          data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
          syms = modulator.modulate(data)
          syms_upsampled = util.upsample(syms, sps)
          iq = np.convolve(syms_upsampled, filterCoeffs,'same')
        case "QPSK":
          modulator = komm.PSKModulation(4, phase_offset=np.pi/4.0)
          data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
          syms = modulator.modulate(data)
          syms_upsampled = util.upsample(syms, sps)
          iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "8PSK":
          modulator = komm.PSKModulation(8)
          data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
          syms = modulator.modulate(data)
          syms_upsampled = util.upsample(syms, sps)
          iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "16QAM":
          modulator = komm.QAModulation(16)
          data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
          syms = modulator.modulate(data)
          syms_upsampled = util.upsample(syms, sps)
          iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "64QAM":
             modulator = komm.QAModulation(64)
             data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
             syms = modulator.modulate(data)
             syms_upsampled = util.upsample(syms, sps)
             iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "PAM4":
             modulator = komm.PAModulation(4)
             data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
             syms = modulator.modulate(data)
             syms_upsampled = util.upsample(syms, sps)
             iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "GFSK":
             modulator = komm.QAModulation(64)
             data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
             syms = modulator.modulate(data)
             syms_upsampled = util.upsample(syms, sps)
             iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "CPFSK":
             modulator = komm.QAModulation(64)
             data = np.random.randint(0, M, spf * modulator.bits_per_symbol)
             syms = modulator.modulate(data)
             syms_upsampled = util.upsample(syms, sps)
             iq = np.convolve(syms_upsampled, filterCoeffs, mode='same')
        case "ORIGINAL":
            iq = i + 1j * q
        case "EXIT":
            sdr.tx_destroy_buffer()
            break
        case _:
            sdr.tx_destroy_buffer()
            break

    iq = iq[4 * sps + 1:]
    maxVal = max(max(abs(np.real(iq))), max(abs(np.imag(iq))))
    iq = iq * 0.8 / maxVal
    iq_real = np.int16(np.real(iq) * 2**15)
    iq_imag = np.int16(np.imag(iq) * 2**15)
    iq = iq_real + 1j * iq_imag
    sdr.tx(iq)
    plt.plot(np.real(syms), np.imag(syms), 'o')
    plt.show()












