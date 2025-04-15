# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np
from enum import Enum

print(adi.__version__)

url = "ip:192.168.0.5"

conv = adi.ad9081(url)
tddn = adi.tddn(url)

conv._rxadc.set_kernel_buffers_count(1)

# Set NCOs

conv.rx_channel_nco_frequencies = [0] * 4
conv.tx_channel_nco_frequencies = [0] * 4

conv.rx_main_nco_frequencies = [100000000] * 4
conv.tx_main_nco_frequencies = [100000000] * 4

conv.rx_enabled_channels = [0, 1, 2, 3]
conv.tx_enabled_channels = [0, 1, 2, 3]
conv.rx_nyquist_zone     = ["odd"] * 4

conv.tx_cyclic_buffer = True
conv.rx_cyclic_buffer = False

conv.tx_ddr_offload   = False

tddn.burst_count          = 10
frame_length_ms           = 0.005
rx_time                   = tddn.burst_count * frame_length_ms
generated_signal_time     = 0.005
blank_time                = 0
use_tx_mxfe_en            = 0

tx_time                   = generated_signal_time - blank_time
capture_range             = 10

N_tx                      = int((generated_signal_time * conv.tx_sample_rate) / 1000)
N_rx                      = int((rx_time * conv.rx_sample_rate) / 1000)

conv.rx_buffer_size       = N_rx

tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = frame_length_ms


TX_OFFLOAD_SYNC = 0
RX_OFFLOAD_SYNC = 1
TDD_ENABLE      = 2
RX_MXFE_EN      = 3
TX_MXFE_EN      = 4
TX_STINGRAY_EN  = 5

if use_tx_mxfe_en:
    print("0x001B:", conv.ad9081_register_read(0x001B))
    conv.ad9081_register_write(0x001B,0xf)
    print("0x001B:", conv.ad9081_register_read(0x001B))
    #
    print("0x0321:", conv.ad9081_register_read(0x0321))
    conv.ad9081_register_write(0x0321,0x00)
    print("0x0321:", conv.ad9081_register_read(0x0321))

    tddn.channel[TX_MXFE_EN].on_ms    = 0
    tddn.channel[TX_MXFE_EN].off_ms   = tx_time
    tddn.channel[TX_MXFE_EN].polarity = 0
    tddn.channel[TX_MXFE_EN].enable   = 1
else :
    tddn.channel[TX_MXFE_EN].on_ms    = 0
    tddn.channel[TX_MXFE_EN].off_ms   = 0
    tddn.channel[TX_MXFE_EN].polarity = 1
    tddn.channel[TX_MXFE_EN].enable   = 1


for chan in [TDD_ENABLE,RX_MXFE_EN,TX_STINGRAY_EN]:
    tddn.channel[chan].on_ms    = 0
    tddn.channel[chan].off_ms   = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable   = 1

for chan in [TX_OFFLOAD_SYNC,RX_OFFLOAD_SYNC]:
    tddn.channel[chan].on_raw   = 0
    tddn.channel[chan].off_raw  = 1
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable   = 1

tddn.enable = 1

print(f"TX Sampling_rate:          {conv.tx_sample_rate}")
print(f"TX buffer length:          {N_tx}")
print(f"Generated signal time[ms]: {generated_signal_time}")
print(f"TX_transmit time[ms]:      {tx_time}")
print(f"RX_recieve time[ms]:       {((1/conv.rx_sample_rate) * conv.rx_buffer_size)*1000}")
print(f"TDD_frame time[ms]:        {tddn.frame_length_ms}")
print(f"TDD_frame time[raw]:       {tddn.frame_length_raw}")
print(f"RX buffer length:          {conv.rx_buffer_size}")
print(f"RX Sampling_rate:          {conv.rx_sample_rate}")

fs = int(conv.tx_sample_rate)
A = 0.9 * 2**15  # -6 dBFS
B = 1e6
T = N_tx / fs
t = np.linspace(0, T, N_tx, endpoint=False)
tx_sig = A * np.sin(2 * math.pi * B * t)

conv.tx_destroy_buffer()
conv.tx([tx_sig,tx_sig,tx_sig,tx_sig])

# Generate the TDD frame Rate
T_tdd = conv.rx_buffer_size / fs
tdd_t = np.linspace(0, T_tdd, conv.rx_buffer_size, endpoint=False)
tdd_amplitude = 1
tdd_freq = 1/(tddn.frame_length_ms* 1e-3)
tdd_frame_rate_plot = tdd_amplitude * np.sign(np.sin(2 * math.pi * tdd_freq * tdd_t))


rx_sig = np.zeros((capture_range,conv.rx_buffer_size))

for r in range(capture_range):
    conv.rx_sync_start = "arm"
    conv.rx_destroy_buffer()
    conv._rx_init_channels()
    tddn.sync_soft  = 0
    tddn.sync_soft  = 1
    data  = conv.rx()
    rx_sig[r]=data[0].real

fig, axs = plt.subplots(3, 1)

for r in range(capture_range):

    # Plot the received signal

    axs[0].plot(rx_sig[r])
    axs[0].set_title(f"Received Signal - Capture number: {r}")
    axs[0].set_xlabel("Sample")
    axs[0].set_ylabel("Amplitude")

    # Plot the TDD frame rate

    axs[1].plot(tdd_frame_rate_plot)
    axs[1].set_title("TDD frame rate")
    axs[1].set_xlabel("Sample")
    axs[1].set_ylabel("Amplitude")

    tx_signal_padded = np.append(tx_sig, np.zeros(abs(len(rx_sig[0]) - len(tx_sig))))

    # Plot the transmitted signal

    axs[2].plot(tx_signal_padded)
    axs[2].set_title("Transmitted Signal")
    axs[2].set_xlabel("Sample")
    axs[2].set_ylabel("Amplitude")

plt.tight_layout()
plt.show()

tddn.enable = 0

for chan in [TX_OFFLOAD_SYNC, RX_OFFLOAD_SYNC, TDD_ENABLE, RX_MXFE_EN, TX_MXFE_EN, TX_STINGRAY_EN]:
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable = 1

tddn.enable = 1
tddn.enable = 0

conv.tx_destroy_buffer()
conv.rx_destroy_buffer()





