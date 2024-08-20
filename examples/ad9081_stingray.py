# Copyright (C) 2020 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np

url = "local:" if len(sys.argv) == 1 else sys.argv[1]
ssh = adi.sshfs(address=url, username="root", password="analog")

tx_offload_base_addr    = 0x9c440000
rx_offload_base_addr    = 0x9c450000
control_reg_offload     = 0x88

conv = adi.ad9081(url)
tddn = adi.tddn(url)

conv._rxadc.set_kernel_buffers_count(1)

# Set NCOs

conv.rx_channel_nco_frequencies = [0] * 4
conv.tx_channel_nco_frequencies = [0] * 4

conv.rx_main_nco_frequencies = [100000000] * 4 
conv.tx_main_nco_frequencies = [100000000] * 4 

conv.rx_enabled_channels = [0,1,2]
conv.tx_enabled_channels = [0,1,2]
conv.rx_nyquist_zone     = ["odd"] * 4

conv.tx_cyclic_buffer = True
conv.rx_cyclic_buffer = False
conv.tx_ddr_offload   = False
conv.rx_ddr_offload   = False

stdout, stderr = ssh._run(f"busybox devmem 0x{tx_offload_base_addr + control_reg_offload:02x} 32 0x2")
stdout, stderr = ssh._run(f"busybox devmem 0x{rx_offload_base_addr + control_reg_offload:02x} 32 0x2")

frame_length_ms           = 1
pulse_width_high          = 0.1
samples_per_frame_desired = (pulse_width_high * conv.tx_sample_rate) / 1000
N_tx                      = int(samples_per_frame_desired)
N_rx                      = 3 * N_tx
conv.rx_buffer_size       = N_rx

tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = frame_length_ms
tddn.burst_count          = 0

# TDD ENABLE

tddn.channel[2].on_ms    = 0
tddn.channel[2].off_ms   = 0
tddn.channel[2].polarity = 1
tddn.channel[2].enable   = 1 

# TX OFFFLOAD SYNC
tddn.channel[0].on_ms    = 0
tddn.channel[0].off_raw  = 1
tddn.channel[0].polarity = 0
tddn.channel[0].enable   = 1

# RX OFFFLOAD SYNC
tddn.channel[1].on_ms = 0
tddn.channel[1].off_raw = 1
tddn.channel[1].polarity = 0
tddn.channel[1].enable = 1

for chan in [3,4,5] :
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable = 1
 
tddn.enable = 1

print(f"TX Sampling_rate: {conv.tx_sample_rate}")
print(f"RX Sampling_rate: {conv.rx_sample_rate}")
print(f"TX buffer length: {N_tx}")
print(f"RX buffer length: {N_rx}")
print(f"TX_transmit time[ms]: {(samples_per_frame_desired / conv.tx_sample_rate) * 1000}")
print(f"RX_recieve time[ms]: {((1/conv.rx_sample_rate) * N_rx)*1000}")
print(f"TDD_frame time[ms]: {frame_length_ms}")

fs = int(conv.tx_sample_rate)
A = 0.9 * 2**15  # -6 dBFS
B = 1e4
T = N_tx / fs
t = np.linspace(0, T, N_tx, endpoint=False)
tx_sig = A * np.sin(2 * math.pi * B * t)
conv.tx([tx_sig,tx_sig,tx_sig])

tddn.sync_soft  = 0
tddn.sync_soft  = 1


capture_range = 500
enabled_channels = 3

rx_sig = np.zeros((capture_range,enabled_channels,N_rx)) 
rx_t = np.linspace(0,N_rx, N_rx , endpoint=False)

fig, (ch1, ch2) = plt.subplots(1, 2)

for r in range(capture_range):
    rx_sig[r]  = conv.rx()
    
for r in range(capture_range):
    plt.suptitle(f"Capture number: {r}")
    ch1.plot(rx_t, rx_sig[r][0])
    ch1.set_title("Channel 1 data")
    ch2.plot(rx_t, rx_sig[r][1])
    ch2.set_title("Channel 2 data")
plt.show()

tddn.enable = 0
   
for chan in [1,2,3,4,5] :
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable = 1

tddn.enable = 1
tddn.enable = 0

conv.tx_destroy_buffer()
conv.rx_destroy_buffer()





