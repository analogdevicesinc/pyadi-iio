# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np
import paramiko

print(adi.__version__)

talise_ip = "10.48.65.138" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

# Create radio
sdr  = adi.adrv9009_zu11eg(talise_uri)
tddn = adi.tddn(talise_uri)

# Configure the ffsom board: (make sure # pip install paramiko)
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(talise_ip, username="root", password="analog")
print(f"Run cmd: busybox devmem 0x9c450088 w 0x1")
stdin, stdout, stderr = ssh.exec_command(f"busybox devmem 0x9c450088 w 0x1")
stdout_str = stdout.read().decode()
stderr_str = stderr.read().decode()
print(stdout_str)
print(stderr_str)

# Configure properties
sdr.tx_enabled_channels = [0, 1]
sdr.trx_lo = 2400000000
# sdr.trx_lo = 1000000000
sdr.tx_hardwaregain_chan0 = -12
sdr.tx_hardwaregain_chan1 = -12
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"
sdr.tx_cyclic_buffer = True


TX_OFFLOAD_SYNC = 0
RX_OFFLOAD_SYNC = 1
TDD_ENABLE      = 2

#Configure TDD engine
tddn.enable = 0

# tddn.burst_count          = 0
# tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = 0.001 # 1 us

for chan in [TX_OFFLOAD_SYNC,RX_OFFLOAD_SYNC,TDD_ENABLE]:
    tddn.channel[chan].on_ms   = 0
    tddn.channel[chan].off_ms  = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable   = 1

tddn.enable = 1

print(f"TX Sample Rate: {sdr.tx_sample_rate/1e6:.2f} MSPS")
print(f"RX Sample Rate: {sdr.rx_sample_rate/1e6:.2f} MSPS") 
print(f"TDD_frame time[ms]:        {tddn.frame_length_ms}")
print(f"RX buffer length:          {sdr.rx_buffer_size}")


print(f"TRX LO: {sdr.trx_lo/1e9:.2f} GHz")
print(f"TX Gain Ch0/Ch1: {sdr.tx_hardwaregain_chan0}/{sdr.tx_hardwaregain_chan1} dB")
print(f"RX Gain Ch0/Ch1: {sdr.rx_hardwaregain_chan0}/{sdr.rx_hardwaregain_chan1} dB")
print(f"RX Buffer Size: {sdr.rx_buffer_size} samples")
# Read properties

fs = int(sdr.tx_sample_rate)
# carrier frequency for the I/Q signal = 1 MHz
fc = 1e6
# calculate N for 2 ms duration: N = fs * duration_in_seconds
duration_in_seconds = 0.002  # 2 ms
N = int(fs * duration_in_seconds)
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)

# I=cos(wt), Q=sin(wt) with reduced amplitude to avoid clipping
i = np.cos(2 * np.pi * fc * t) * 0.1
q = np.sin(2 * np.pi * fc * t) * 0.1

data = i + 1j * q
sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
iq_real = np.int16(np.real(data) * scale_factor)
iq_imag = np.int16(np.imag(data) * scale_factor)
iq = iq_real + 1j * iq_imag

# Print signal statistics for verification
print(f"Signal length: {len(iq)} samples")
print(f"Signal duration: {len(iq)/fs*1000:.2f} ms")
print(f"I component range: [{np.min(iq_real)}, {np.max(iq_real)}]")
print(f"Q component range: [{np.min(iq_imag)}, {np.max(iq_imag)}]")
print(f"Expected cycles in buffer: {fc * len(iq) / fs:.2f}")

sdr.tx_destroy_buffer()
sdr.tx([iq, iq])
tddn.sync_soft  = 1