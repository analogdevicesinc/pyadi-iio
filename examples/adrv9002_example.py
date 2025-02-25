import time
import numpy as np
import adi
import matplotlib.pyplot as plt
import keyboard
import commpy.utilities as util
import komm
import scipy.io

sdr = adi.adrv9002(uri="ip:10.48.65.203")

sdr.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

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

mod_8spk  = scipy.io.loadmat('modulated_data/input_mod_8PSK.mat')
mod_16qam = scipy.io.loadmat('modulated_data/input_mod_16QAM.mat')
mod_64qam = scipy.io.loadmat('modulated_data/input_mod_64QAM.mat')
mod_bspk  = scipy.io.loadmat('modulated_data/input_mod_BPSK.mat')
mod_cpfsk = scipy.io.loadmat('modulated_data/input_mod_CPFSK.mat')
mod_gfsk  = scipy.io.loadmat('modulated_data/input_mod_GFSK.mat')
mod_pam4  = scipy.io.loadmat('modulated_data/input_mod_PAM4.mat')
mod_qpsk  = scipy.io.loadmat('modulated_data/input_mod_QPSK.mat')

while True:
    modulation_number = input("Enter modulation type (1: 16QAM, 2: 64QAM, 3: 8PSK, 5: BPSK, 6: CPFSK, 8: GFSK, 9: PAM4, 10: QPSK, 11: ORIGINAL 0:EXIT): ")
    sdr.tx_destroy_buffer()
    print(modulation_number)
    modulation_type = modulation_map.get(modulation_number, "BPSK")
    print(modulation_type)

    match modulation_type:
        case "BPSK":
            data = mod_bspk['yc']
        case "QPSK":
            data = mod_qpsk['yc']
        case "8PSK":
            data = mod_8spk['yc']
        case "16QAM":
            data = mod_16qam['yc']
        case "64QAM":
            data = mod_64qam['yc']
        case "PAM4":
            data = mod_pam4['yc']
        case "GFSK":
            data = mod_gfsk['yc']
        case "CPFSK":
            data = mod_cpfsk['yc']
        case "ORIGINAL":
            data = i + 1j * q
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












