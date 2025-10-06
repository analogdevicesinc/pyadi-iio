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
from adi.sshfs import sshfs
import select
# import msvcrt
print(adi.__version__)

url = "ip:192.168.0.1"

conv = adi.adrv9009_zu11eg(url)
tddn = adi.tddn(url)
tddn.enable = 0
conv.trx_lo = int(4e9)
conv.trx_lo_chip_b = int(4e9)
conv.rx_enabled_channels = [0,1,2,3]
conv.tx_enabled_channels = [0,1,2,3]
conv.tx_cyclic_buffer = True


conv.tx_hardwaregain_chan0 = -10
conv.tx_hardwaregain_chan1 = -10
conv.tx_hardwaregain_chan0_chip_b = -10
conv.tx_hardwaregain_chan1_chip_b = -10
conv.gain_control_mode_chan0 = "slow_attack"
conv.gain_control_mode_chan1 = "slow_attack"
conv.gain_control_mode_chan0_chip_b = "slow_attack"
conv.gain_control_mode_chan1_chip_b = "slow_attack"
conv.rx_buffer_size = 2**16
tddn.burst_count          = 0
frame_length_ms           = 0.01
rx_time                   = 5 * frame_length_ms
generated_signal_time     = frame_length_ms/2
blank_time                = 0
use_tx_mxfe_en            = 0

tx_time                   = generated_signal_time - blank_time
capture_range             = 20

N_tx                      = int((generated_signal_time * conv.tx_sample_rate) / 1000)
N_rx                      = int((rx_time * conv.rx_sample_rate) / 1000)
conv.rx_buffer_size       = N_rx

tddn.startup_delay_ms     = 0
tddn.frame_length_ms = frame_length_ms
tddn.sync_external = 1

TX_OFFLOAD_SYNC = 0
RX_OFFLOAD_SYNC = 1
TDD_ENABLE      = 2
RX_MXFE_EN      = 3
TX_MXFE_EN      = 4
TX_STINGRAY_EN  = 5

for chan in [TDD_ENABLE,TX_MXFE_EN,RX_MXFE_EN,TX_STINGRAY_EN]:
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
A = 0.9 * 2**12  # -6 dBFS
B = 100e6
T = N_tx / fs
t = np.linspace(0, T, N_tx, endpoint=False)

i = A * np.cos(2 * math.pi * B * t)
q = A * np.sin(2 * math.pi * B * t)

tx_sig = i + 1j * q

conv.tx([tx_sig,tx_sig,tx_sig,tx_sig])

# Generate the TDD frame Rate
T_tdd = conv.rx_buffer_size / fs
tdd_t = np.linspace(0, T_tdd, conv.rx_buffer_size, endpoint=False)
tdd_amplitude = 1
tdd_freq = 1/(tddn.frame_length_ms* 1e-3)
tdd_frame_rate_plot = tdd_amplitude * np.sign(np.sin(2 * math.pi * tdd_freq * tdd_t))

rx_sig = np.zeros((capture_range,conv.rx_buffer_size))
tddn.sync_soft = 1
rx_sig2 = np.zeros((capture_range,conv.rx_buffer_size)) 

while True:
    print("Looping...")
    data  = conv.rx()
    rx_sig0=data[0]
    rx_sig1=data[1]
    rx_sig2=data[2]
    rx_sig3=data[3]
    print("Press Enter to stop...")
    i, o, e = select.select([sys.stdin], [], [], 1)
    if i:
        input()
        break
"""
for r in range(capture_range):

    data  = conv.rx()
    rx_sig0=data[0]
    rx_sig1=data[1]
    #rx_sig2[r]=data[2]
    rx_sig2 = data[2]
    rx_sig3=data[3]
"""
fig, axs = plt.subplots(3, 1)

for r in range(capture_range):

    # Plot the received signal
    #axs[0].plot(rx_sig0.real, 'red')
    #axs[0].plot(rx_sig1.real, 'green')
    #axs[0].plot(rx_sig2[r], 'black')
    axs[0].plot(rx_sig0, 'black')
    #axs[0].plot(rx_sig3.real, 'blue')
    axs[0].set_title(f"Received Signal - Capture number: {r}")
    axs[0].set_xlabel("Sample")
    axs[0].set_ylabel("Amplitude")

    # Plot the TDD frame rate

    axs[1].plot(tdd_frame_rate_plot)
    axs[1].set_title("TDD frame rate")
    axs[1].set_xlabel("Sample")
    axs[1].set_ylabel("Amplitude")

    tx_signal_padded = np.append(tx_sig.real, np.zeros(abs(len(rx_sig[0]) - len(tx_sig))))

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
print("done")



