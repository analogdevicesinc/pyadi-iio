import time
import numpy as np
import adi
import matplotlib.pyplot as plt
import keyboard
import commpy.utilities as util
import komm
import scipy.io

sdr  = adi.adrv9002(uri="ip:10.48.65.203")
sdr.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

sdr.tx0_port_en = "spi"
sdr.tx1_port_en = "spi"
sdr.tx_ensm_mode_chan0 = "rf_enabled"
sdr.tx_ensm_mode_chan1 = "rf_enabled"
sdr.tx_cyclic_buffer = True
sdr.tx2_cyclic_buffer = True
sdr.tx0_lo = 2400000000
sdr.tx1_lo = 2400000000
sdr.tx_hardwaregain_chan0 = -10
sdr.tx_hardwaregain_chan1 = -10


sdr1 = adi.adrv9002(uri="ip:10.48.65.154")
sdr1.write_stream_profile( "lte_40_lvds_api_68_14_10.stream" ,"lte_40_lvds_api_68_14_10.json")

sdr1.tx0_port_en = "spi"
sdr1.tx1_port_en = "spi"
sdr1.tx_ensm_mode_chan0 = "rf_enabled"
sdr1.tx_ensm_mode_chan1 = "rf_enabled"
sdr1.tx_cyclic_buffer = True
sdr1.tx2_cyclic_buffer = True
sdr1.tx0_lo = 2400000000
sdr1.tx1_lo = 2400000000
sdr1.tx_hardwaregain_chan0 = -10
sdr1.tx_hardwaregain_chan1 = -10


fs = int(sdr1.tx0_sample_rate)

print(fs)
fc = 50000
N = 49120
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.sin(2 * np.pi * fc * t)
q = np.cos(2 * np.pi * fc * t)

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
    "11": "ORIGINAL",
    "12": "DISABLED"
}

mod_8spk  = scipy.io.loadmat('modulated_data/mod_8PSK.mat')
mod_16qam = scipy.io.loadmat('modulated_data/mod_16QAM.mat')
mod_64qam = scipy.io.loadmat('modulated_data/mod_64QAM.mat')
mod_bspk  = scipy.io.loadmat('modulated_data/mod_BPSK.mat')
mod_cpfsk = scipy.io.loadmat('modulated_data/mod_CPFSK.mat')
mod_gfsk  = scipy.io.loadmat('modulated_data/mod_GFSK.mat')
mod_pam4  = scipy.io.loadmat('modulated_data/mod_PAM4.mat')
mod_qpsk  = scipy.io.loadmat('modulated_data/mod_QPSK.mat')

while True:

    modulation_number = input("Enter modulation type (1: 16QAM, 2: 64QAM, 3: 8PSK, 5: BPSK, 6: CPFSK, 8: GFSK, 9: PAM4, 10: QPSK, 11: ORIGINAL, 12: DISABLED, 0:EXIT): ")
    sdr.tx0_en  = 1
    sdr.tx1_en  = 1
    sdr1.tx0_en = 1
    sdr1.tx1_en = 1
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
            data = i + 1j * q
        case "DISABLED":
            data = i + 1j * q
            sdr._tx2.tx_destroy_buffer()
            sdr.tx_destroy_buffer()
            sdr1._tx2.tx_destroy_buffer()
            sdr1.tx_destroy_buffer()
            sdr.tx0_en  = 0
            sdr.tx1_en  = 0
            sdr1.tx0_en = 0
            sdr1.tx1_en = 0


        case "EXIT":
            sdr._tx2.tx_destroy_buffer()
            sdr.tx_destroy_buffer()

            sdr1._tx2.tx_destroy_buffer()
            sdr1.tx_destroy_buffer()

            break

    data=data.flatten()
    iq_real = np.int16(np.real(data) * 2**12-1)
    iq_imag = np.int16(np.imag(data) * 2**12-1)
    iq = iq_real + 1j * iq_imag

    sdr1.tx_destroy_buffer()
    sdr1._tx2.tx_destroy_buffer()

    sdr.tx_destroy_buffer()
    sdr._tx2.tx_destroy_buffer()

    sdr1.tx(iq)
    sdr1.tx2(iq)

    sdr.tx(iq)
    sdr.tx2(iq)






