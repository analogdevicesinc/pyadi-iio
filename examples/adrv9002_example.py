import time

import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import adi
import keyboard

def change_modulation(modulation_type ,original_signal):
    if modulation_type == "BPSK":
        iq = original_signal * np.exp(1j * np.pi * (original_signal > 0))
    elif modulation_type == "QPSK":
        iq = original_signal * np.exp(1j * np.pi / 2 * (original_signal % 4))
    elif modulation_type == "8PSK":
        iq = original_signal * np.exp(1j * np.pi / 4 * (original_signal % 8))
    elif modulation_type == "16QAM":
        iq = (2 * (original_signal % 4) - 3) + 1j * (2 * (original_signal // 4) - 3)
    elif modulation_type == "64QAM":
        iq = (2 * (original_signal % 8) - 7) + 1j * (2 * (original_signal // 8) - 7)
    elif modulation_type == "PAM4":
        iq = 2 * (original_signal % 4) - 3
    elif modulation_type == "GFSK":
        iq = np.exp(1j * 2 * np.pi * np.cumsum(original_signal) / fs)
    elif modulation_type == "CPFSK":
        iq = np.exp(1j * 2 * np.pi * np.cumsum(original_signal) / fs)
    else:
        raise ValueError("Unsupported modulation type")
    return iq

sdr = adi.adrv9002(uri="ip:10.48.65.154")
sdr.rx_ensm_mode_chan0 = "rf_enabled"
sdr.rx_ensm_mode_chan1 = "rf_enabled"
sdr.tx_hardwaregain_chan0 = -20
sdr.tx_ensm_mode_chan0 = "rf_enabled"
sdr.tx_cyclic_buffer = True

fs = int(sdr.rx0_sample_rate)

fc = 1000000
N = 1024
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = i + 1j * q

modulation_map = {
    "1": "BPSK",
    "2": "QPSK",
    "3": "8PSK",
    "4": "16QAM",
    "5": "64QAM",
    "6": "PAM4",
    "7": "GFSK",
    "8": "CPFSK"
}

def switch_mode():
    sdr.tx_destroy_buffer()
    modulation_type = input("Enter modulation type (1: BPSK, 2: QPSK, 3: 8PSK, 4: 16QAM, 5: 64QAM, 6: PAM4, 7: GFSK, 8: CPFSK): ")
    modulation_type = modulation_map.get(modulation_type, "BPSK")
    modulated_signal = change_modulation(modulation_type,iq)
    sdr.tx(modulated_signal)

keyboard.add_hotkey('space', switch_mode)
print("Press 'space' to switch modulation mode. Press 'esc' to exit.")
keyboard.wait('esc')









