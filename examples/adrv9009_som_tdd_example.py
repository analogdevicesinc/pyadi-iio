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

talise_ip = "192.168.0.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

# Create radio
sdr  = adi.adrv9009_zu11eg(talise_uri)
tddn = adi.tddn(talise_uri)

# USER CONFIGURABLE PARAMETERS
# Configure TX properties
sdr.tx_enabled_channels = [0, 1]
sdr.trx_lo = 2400000000
# sdr.trx_lo = 1000000000
sdr.tx_hardwaregain_chan0 = -12
sdr.tx_hardwaregain_chan1 = -12
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"

# Number of frame pulses to plot in the pulse train
# (will be used to calculate the RX buffer size)
frame_pulses_to_plot = 5

# Frame and pulse timing (in milliseconds)
frame_length_ms = 0.04 # 40 us
# sine data for 20 us pulse than 20 us of zero data
tx_pulse_start_ms = 0.00001 # 10 ns
tx_pulse_stop_ms = 0.02 # 20 us
# END USER CONFIGURABLE PARAMETERS

# Prepare TX data
fs = int(sdr.tx_sample_rate)
frame_length_seconds = frame_length_ms * 1e-3
# carrier frequency for the I/Q signal = 20 kHz
fc = 1000e3
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate samples for TX pulse duration
tx_pulse_duration_ms = tx_pulse_stop_ms - tx_pulse_start_ms
tx_pulse_duration_seconds = tx_pulse_duration_ms * 1e-3
tx_pulse_samples = int(fs * tx_pulse_duration_seconds)
tx_start_sample = int(fs * tx_pulse_start_ms * 1e-3)

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
i = np.zeros(N)
q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(tx_start_sample, min(tx_start_sample + tx_pulse_samples, N)):
    t_sample = n * ts
    i[n] = np.cos(2 * np.pi * fc * t_sample) * 0.1
    q[n] = np.sin(2 * np.pi * fc * t_sample) * 0.1

data = i + 1j * q
sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
iq_real = np.int16(np.real(data) * scale_factor)
iq_imag = np.int16(np.imag(data) * scale_factor)
iq = iq_real + 1j * iq_imag

# Configure RX parameters
sdr.rx_enabled_channels = [0, 1]

# Calculate RX buffer size to match TX duration
rx_fs = int(sdr.rx_sample_rate)

# Match RX buffer duration to TX duration
desired_rx_duration = frame_pulses_to_plot * len(iq) / fs * 1000  # ms
rx_buffer_samples = int(rx_fs * (desired_rx_duration * 1e-3))
sdr.rx_buffer_size = rx_buffer_samples

# Create time vector for plotting
rx_ts = 1 / float(rx_fs)
rx_t = np.arange(0, rx_buffer_samples * rx_ts, rx_ts)

# Create pulse train for the entire RX buffer duration
pulse_train = np.zeros(rx_buffer_samples)

# Calculate samples per frame and pulse
samples_per_frame = int(frame_length_ms * 1e-3 / rx_ts)
pulse_start_offset = int(tx_pulse_start_ms * 1e-3 / rx_ts)
pulse_stop_offset = int(tx_pulse_stop_ms * 1e-3 / rx_ts)

num_frames = len(rx_t) // samples_per_frame

for frame in range(num_frames):
    frame_start = frame * samples_per_frame
    pulse_start = frame_start + pulse_start_offset
    pulse_stop = frame_start + pulse_stop_offset
    pulse_train[pulse_start:pulse_stop] = 1

# TDD signal channels
TDD_TX_OFFLOAD_SYNC = 0
TDD_RX_OFFLOAD_SYNC = 1
TDD_ENABLE      = 2
TDD_ADRV9009_RX_EN = 3
TDD_ADRV9009_TX_EN = 4

#Configure TDD engine
tddn.enable = 0

# tddn.burst_count          = 0 # continuous mode, period repetead forever
# tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = frame_length_ms

for chan in [TDD_ENABLE,TDD_ADRV9009_TX_EN,TDD_ADRV9009_RX_EN]:
    tddn.channel[chan].on_ms   = 0
    tddn.channel[chan].off_ms  = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable   = 1

for chan in [TDD_TX_OFFLOAD_SYNC,TDD_RX_OFFLOAD_SYNC]:
    tddn.channel[chan].on_raw   = 0
    tddn.channel[chan].off_raw  = 10 # 10 samples at 250 MHz = 40 ns pulse width
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable   = 1

tddn.enable = 1

tdd_tx_offload_frame_length_ms = frame_length_ms
tdd_tx_offload_pulse_start_ms = 0.00001 # 10 ns

# off_raw is in samples, so convert to time for offset calculation
off_raw_samples = tddn.channel[TDD_TX_OFFLOAD_SYNC].off_raw

# Create pulse train for the entire RX buffer duration
tdd_tx_offload_pulse_train = np.zeros(rx_buffer_samples)

# Calculate samples per frame and pulse
tdd_tx_offload_samples_per_frame = int(frame_length_ms * 1e-3 / rx_ts)
tdd_tx_offload_pulse_start_offset = int(tdd_tx_offload_pulse_start_ms * 1e-3 / rx_ts)
# Pulse stays high for off_raw_samples
tdd_tx_offload_pulse_stop_offset = tdd_tx_offload_pulse_start_offset + off_raw_samples

# Only plot as many pulses as requested
for frame in range(frame_pulses_to_plot):
    tdd_tx_offload_frame_start = frame * tdd_tx_offload_samples_per_frame
    tdd_tx_offload_pulse_start = tdd_tx_offload_frame_start + tdd_tx_offload_pulse_start_offset
    tdd_tx_offload_pulse_stop = tdd_tx_offload_frame_start + tdd_tx_offload_pulse_stop_offset
    tdd_tx_offload_pulse_train[tdd_tx_offload_pulse_start:tdd_tx_offload_pulse_stop] = 1

# Send TX data
sdr.tx_destroy_buffer()
# When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
sdr.tx([iq, iq])

# Trigger TDD synchronization
tddn.sync_soft  = 1

# Force set the Data Offload Tx to run in cyclic mode
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(talise_ip, username="root", password="analog")
print(f"Run cmd: busybox devmem 0x9c460088 32 0x0")
stdin, stdout, stderr = ssh.exec_command(f"busybox devmem 0x9c460088 32 0x0")
stdout_str = stdout.read().decode()
stderr_str = stderr.read().decode()
print(stdout_str)
print(stderr_str)
stdout.close()
stderr.close()
ssh.close()

tddn.sync_soft  = 1

# Capture RX data
print("Capturing RX data...")

capture_range = 5

rx_ch0 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
rx_ch1 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)

for capture in range(capture_range):
    sdr.rx_destroy_buffer()
    tddn.sync_soft  = 1

    rx_data = sdr.rx()

    # Extract I/Q data for both channels
    rx_ch0[capture] = rx_data[0]
    rx_ch1[capture] = rx_data[1]

    time.sleep(1)  # Small delay between captures

print(f"RX data captured - Ch0: {len(rx_ch0[-1])} samples, Ch1: {len(rx_ch1[-1])} samples")

# Print signal statistics for verification
print(f"TX Sample Rate: {sdr.tx_sample_rate/1e6:.2f} MSPS")
print(f"RX Sample Rate: {sdr.rx_sample_rate/1e6:.2f} MSPS")
print(f"TRX LO: {sdr.trx_lo/1e9:.2f} GHz")

print(f"TX buffer duration: {len(iq)/fs*1000:.2f} ms")
print(f"RX buffer duration: {rx_buffer_samples/rx_fs*1000:.2f} ms")

print(f"TX I component range: [{np.min(iq_real)}, {np.max(iq_real)}]")
print(f"TX Q component range: [{np.min(iq_imag)}, {np.max(iq_imag)}]")
print(f"Expected cycles in buffer: {fc * len(iq) / fs:.2f}")

print(f"TX Gain Ch0/Ch1: {sdr.tx_hardwaregain_chan0}/{sdr.tx_hardwaregain_chan1} dB")
print(f"RX Gain Ch0/Ch1: {sdr.rx_hardwaregain_chan0}/{sdr.rx_hardwaregain_chan1} dB")

print(f"TX Buffer Size: {sdr._tx_buffer_size} samples")
print(f"RX Buffer Size: {sdr.rx_buffer_size} samples")

# Plot the results
plt.figure(figsize=(15, 10))

# Plot TX signal (time domain)
plt.subplot(4, 1, 1)
plt.plot(t[:N] * 1e6, np.real(iq[:N]), 'b-')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('TX Signal - Time Domain')
plt.grid(True)

# Plot tdd_data_offload pulse train for multiple frames
plt.subplot(4, 1, 2)
plt.plot(rx_t * 1e6, tdd_tx_offload_pulse_train[:len(rx_t)], 'g-')
plt.title(f"TDD Data Offload Sync Pulse - Time Domain")
plt.xlabel("Time (μs)")
plt.ylabel("Pulse")
plt.grid(True)

# Plot frame pulse train for multiple frames
plt.subplot(4, 1, 3)
plt.plot(rx_t * 1e6, pulse_train[:len(rx_t)], 'r-')
plt.title(f"RX Data Frame Pulse - Time Domain")
plt.xlabel("Time (μs)")
plt.ylabel("Pulse")
plt.grid(True)

# Plot RX Channel 0 (time domain)
plt.subplot(4, 1, 4)
for idx in range(capture_range):
    plt.plot(rx_t * 1e6, np.real(rx_ch0[idx]), label=f'Capture {idx}')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('Received data RX Channel 0 - Time Domain (All Captures)')
plt.grid(True)
plt.legend(loc="upper right")

plt.tight_layout()
plt.show()

tddn.enable = 0

for chan in [TDD_TX_OFFLOAD_SYNC, TDD_RX_OFFLOAD_SYNC, TDD_ENABLE, TDD_ADRV9009_RX_EN, TDD_ADRV9009_TX_EN]:
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable = 1

tddn.enable = 1
tddn.enable = 0

sdr.tx_destroy_buffer()
sdr.rx_destroy_buffer()