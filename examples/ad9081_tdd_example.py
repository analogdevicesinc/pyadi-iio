# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys

import adi
import matplotlib.pyplot as plt
import numpy as np

url = "ip:analog-2.local" if len(sys.argv) == 1 else sys.argv[1]

trx = adi.ad9081(url)
tdd = adi.tdd(url)

trx.rx_channel_nco_frequencies = [0] * 4
trx.tx_channel_nco_frequencies = [0] * 4

trx.rx_main_nco_frequencies = [2450000000] * 4
trx.tx_main_nco_frequencies = [2450000000] * 4

trx.rx_enabled_channels = [0]
trx.tx_enabled_channels = [0]

trx.rx_nyquist_zone = ["odd"] * 4

N_rx = 2 ** 15
trx.rx_buffer_size = N_rx
trx.tx_cyclic_buffer = True

# Automatically enabled by TDD device tree
# trx.tx_ddr_offload = 1

# Generate TX signal

fs = int(trx.tx_sample_rate)

A = 0.5 * 2 ** 14  # -6 dBFS

B = fs / 2.5  # 100 MHz wide pulse @ 250 MS/s; 200 MHz @ 500 MS/s
N = 2 ** 14
T = N / fs

t = np.linspace(-T / 2, T / 2, N, endpoint=False)
tx_sig = A * np.sinc(B * t)
tx_sig_2 = A * np.exp(2j * np.pi * B * t)

tdd.en = False

# Setup TDD
tdd.frame_length_ms = 40.0
tdd.burst_count = 0
tdd.dma_gateing_mode = "rx_tx"
tdd.en_mode = "rx_tx"
tdd.secondary = False

tdd.en = True

# We only need to "trigger" the buffer, it doesn't need to stay high in this use case.
# The secondary values are disabled and unused
#
#                 Primary     Secondary
#                 on    off   on off
tdd.tx_dma_raw = [1010, 1020, 0, 0]
tdd.rx_dma_raw = [10, 20, 0, 0]

# Send off TX data
trx.tx(tx_sig)

rx_t = np.linspace(0, N_rx / fs, N_rx, endpoint=False)
for r in range(40):
    rx_sig = trx.rx()

    if r == 20:
        trx.tx_destroy_buffer()
        trx.tx(tx_sig_2)

    plt.clf()
    plt.plot(1000000 * rx_t, np.abs(rx_sig))
    plt.legend(["RX Signal", "TX Signal"])
    plt.xlabel("t / µs")
    plt.ylabel("Amplitude")
    plt.draw()
    plt.pause(0.10)

plt.show()
