# Copyright (C) 2021 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
