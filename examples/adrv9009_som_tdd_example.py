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

talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

# Create radio
sdr  = adi.adrv9009_zu11eg(talise_uri)
tddn = adi.tddn(talise_uri)

# USER CONFIGURABLE PARAMETERS
# Configure TX properties
sdr.tx_enabled_channels = [0, 1, 2, 3]
# sdr.trx_lo = 4500000000
# sdr.trx_lo_chip_b = 4500000000
# sdr.trx_lo = 1000000000
sdr.tx_hardwaregain_chan0 = 0
sdr.tx_hardwaregain_chan1 = 0
sdr.tx_hardwaregain_chan0_chip_b= 0
sdr.tx_hardwaregain_chan1_chip_b = 0
sdr.rx_hardwaregain_chan0 = 0
sdr.rx_hardwaregain_chan1 = 0
sdr.rx_hardwaregain_chan0_chip_b= 0
sdr.rx_hardwaregain_chan1_chip_b = 0
sdr.gain_control_mode_chan0 = "manual"
sdr.gain_control_mode_chan1 = "manual"
sdr.gain_control_mode_chan0_chip_b = "manual"
sdr.gain_control_mode_chan1_chip_b = "manual"
sdr.gain_control_mode_chan0 = "slow_attack"
sdr.gain_control_mode_chan1 = "slow_attack"
sdr.gain_control_mode_chan0_chip_b = "slow_attack"
sdr.gain_control_mode_chan1_chip_b = "slow_attack"

# Number of frame pulses to plot in the pulse train
# (will be used to calculate the RX buffer size)
frame_pulses_to_plot = 5

## RX properties XX
# Frame and pulse timing (in milliseconds)
frame_length_ms = 0.1 # 100 us
# sine data for 10 us pulse than 90 us of zero data
tx_pulse_start_ms = 0.00001 # 10 ns
tx_pulse_stop_ms = 0.100 # 100 us
# END USER CONFIGURABLE PARAMETERS


############### TX Pulse, DAC 0 ##############
# Frame and pulse timing (in milliseconds)
pulse0_frame_length_ms = 0.1 # 100 us
# sine data for 20 us pulse than 20 us of zero data
pulse0_tx_pulse_start_ms = 0.00001 # 10 ns (time zero)
pulse0_tx_pulse_stop_ms = 0.010 # 10 us
# END USER CONFIGURABLE PARAMETERS

# Prepare TX data
fs = int(sdr.tx_sample_rate)
frame_length_seconds = pulse0_frame_length_ms * 1e-3
# carrier frequency for the I/Q signal = 20 kHz
fc = 1000e3
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate samples for TX pulse duration
pulse0_tx_pulse_duration_ms = pulse0_tx_pulse_stop_ms - pulse0_tx_pulse_start_ms
pulse0_tx_pulse_duration_seconds = pulse0_tx_pulse_duration_ms * 1e-3
pulse0_tx_pulse_samples = int(fs * pulse0_tx_pulse_duration_seconds)
pulse0_tx_start_sample = int(fs * pulse0_tx_pulse_start_ms * 1e-3)

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
pulse0_i = np.zeros(N)
pulse0_q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(pulse0_tx_start_sample, min(pulse0_tx_start_sample + pulse0_tx_pulse_samples, N)):
    t_sample = n * ts
    pulse0_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
    pulse0_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1

pulse0_data = pulse0_i + 1j * pulse0_q

sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
pulse0_iq_real = np.int16(np.real(pulse0_data) * scale_factor)
pulse0_iq_imag = np.int16(np.imag(pulse0_data) * scale_factor)
pulse0_iq = pulse0_iq_real + 1j * pulse0_iq_imag


############### TX Pulse, DAC 1 ##############
# Frame and pulse timing (in milliseconds)
pulse1_frame_length_ms = 0.100 # 40 us
# sine data for 20 us pulse than 20 us of zero data
pulse1_tx_pulse_start_ms = 0.00001 + 0.015 # 15 us
pulse1_tx_pulse_stop_ms = 0.025 # 25 us
# END USER CONFIGURABLE PARAMETERS

# Prepare TX data
fs = int(sdr.tx_sample_rate)
frame_length_seconds = pulse1_frame_length_ms * 1e-3
# carrier frequency for the I/Q signal = 20 kHz
fc = 1000e3
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate samples for TX pulse duration
pulse1_tx_pulse_duration_ms = pulse1_tx_pulse_stop_ms - pulse1_tx_pulse_start_ms
pulse1_tx_pulse_duration_seconds = pulse1_tx_pulse_duration_ms * 1e-3
pulse1_tx_pulse_samples = int(fs * pulse1_tx_pulse_duration_seconds)
pulse1_tx_start_sample = int(fs * pulse1_tx_pulse_start_ms * 1e-3)

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
pulse1_i = np.zeros(N)
pulse1_q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(pulse1_tx_start_sample, min(pulse1_tx_start_sample + pulse1_tx_pulse_samples, N)):
    t_sample = n * ts
    pulse1_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
    pulse1_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1

pulse1_data = (pulse1_i + 1j * pulse1_q)

sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
pulse1_iq_real = np.int16(np.real(pulse1_data) * scale_factor)
pulse1_iq_imag = np.int16(np.imag(pulse1_data) * scale_factor)
pulse1_iq = pulse1_iq_real + 1j * pulse1_iq_imag

############### TX Pulse, DAC 2 ##############
# Frame and pulse timing (in milliseconds)
pulse2_frame_length_ms = 0.100 # 40 us
# sine data for 20 us pulse than 20 us of zero data
pulse2_tx_pulse_start_ms = 0.00001 + 0.03 # 30 us
pulse2_tx_pulse_stop_ms = 0.040 # 50 us
# END USER CONFIGURABLE PARAMETERS

# Prepare TX data
fs = int(sdr.tx_sample_rate)
frame_length_seconds = pulse2_frame_length_ms * 1e-3
# carrier frequency for the I/Q signal = 20 kHz
fc = 1000e3
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate samples for TX pulse duration
pulse2_tx_pulse_duration_ms = pulse2_tx_pulse_stop_ms - pulse2_tx_pulse_start_ms
pulse2_tx_pulse_duration_seconds = pulse2_tx_pulse_duration_ms * 1e-3
pulse2_tx_pulse_samples = int(fs * pulse2_tx_pulse_duration_seconds)
pulse2_tx_start_sample = int(fs * pulse2_tx_pulse_start_ms * 1e-3)

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
pulse2_i = np.zeros(N)
pulse2_q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(pulse2_tx_start_sample, min(pulse2_tx_start_sample + pulse2_tx_pulse_samples, N)):
    t_sample = n * ts
    pulse2_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
    pulse2_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1

pulse2_data = pulse2_i + 1j * pulse2_q

sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
pulse2_iq_real = np.int16(np.real(pulse2_data) * scale_factor)
pulse2_iq_imag = np.int16(np.imag(pulse2_data) * scale_factor)
pulse2_iq = pulse2_iq_real + 1j * pulse2_iq_imag

############### TX Pulse, DAC 3 ##############
# Frame and pulse timing (in milliseconds)
pulse3_frame_length_ms = 0.100 # 40 us
#sine data for 20 us pulse than 20 us of zero data
pulse3_tx_pulse_start_ms = 0.00001 + 0.045 # 45 us
pulse3_tx_pulse_stop_ms = 0.055 # 55 us
# END USER CONFIGURABLE PARAMETERS

# Prepare TX data
fs = int(sdr.tx_sample_rate)
frame_length_seconds = pulse3_frame_length_ms * 1e-3
# carrier frequency for the I/Q signal = 20 kHz
fc = 1000e3
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate samples for TX pulse duration
pulse3_tx_pulse_duration_ms = pulse3_tx_pulse_stop_ms - pulse3_tx_pulse_start_ms
pulse3_tx_pulse_duration_seconds = pulse3_tx_pulse_duration_ms * 1e-3
pulse3_tx_pulse_samples = int(fs * pulse3_tx_pulse_duration_seconds)
pulse3_tx_start_sample = int(fs * pulse3_tx_pulse_start_ms * 1e-3)

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
pulse3_i = np.zeros(N)
pulse3_q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(pulse3_tx_start_sample, min(pulse3_tx_start_sample + pulse3_tx_pulse_samples, N)):
    t_sample = n * ts
    pulse3_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
    pulse3_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1

pulse3_data = pulse3_i + 1j * pulse3_q

sdr.tx_destroy_buffer()

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
scale_factor = 2**15 - 1
pulse3_iq_real = np.int16(np.real(pulse3_data) * scale_factor)
pulse3_iq_imag = np.int16(np.imag(pulse3_data) * scale_factor)
pulse3_iq = pulse3_iq_real + 1j * pulse3_iq_imag



# Configure TX data offload mode to cyclic
sdr._txdac.debug_attrs["pl_ddr_fifo_enable"].value = "1"
sdr.tx_cyclic_buffer = True

# Configure RX parameters
sdr.rx_enabled_channels = [0, 1, 2, 3]

# Calculate RX buffer size to match TX duration
rx_fs = int(sdr.rx_sample_rate)

# Match RX buffer duration to TX duration
desired_rx_duration = frame_pulses_to_plot * len(pulse0_iq) / fs * 1000  # ms
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
TDD_MANTARAY_EN = 5

#Configure TDD engine
tddn.enable = 0

# tddn.burst_count          = 0 # continuous mode, period repetead forever
# tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = frame_length_ms

for chan in [TDD_ENABLE,TDD_ADRV9009_TX_EN,TDD_ADRV9009_RX_EN,TDD_MANTARAY_EN]:
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

# # Send TX data
sdr.tx_destroy_buffer()
# When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
sdr.tx([pulse0_iq, pulse1_iq, pulse2_iq, pulse3_iq])

# # Send cal'd TX data
# sdr.tx_destroy_buffer()
# # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
# sdr.tx([pulse0_iq, pulse1_iq*np.exp(1j*212.4*np.pi/180), pulse2_iq*np.exp(1j*272.76*np.pi/180), pulse3_iq*np.exp(1j*110.3*np.pi/180)])

# Send cal'd TX data
# sdr.tx_destroy_buffer()
# # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
# sdr.tx([pulse0_iq, np.zeros(N), np.zeros(N), np.zeros(N)])

# # Send cal'd TX data
# sdr.tx_destroy_buffer()
# # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
# sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*212.4*np.pi/180), pulse0_iq*np.exp(1j*272.8*np.pi/180), pulse0_iq*np.exp(1j*110.3*np.pi/180)])


# Trigger TDD synchronization
tddn.sync_soft  = 1

# Capture RX data
print("Capturing RX data...")

capture_range = 1

rx_ch0 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
rx_ch1 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
rx_ch2 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
rx_ch3 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
for capture in range(capture_range):
    sdr.rx_destroy_buffer()
    tddn.sync_soft  = 1

    rx_data = sdr.rx()

    # Extract I/Q data for both channels
    rx_ch0[capture] = rx_data[0]
    rx_ch1[capture] = rx_data[1]
    rx_ch2[capture] = rx_data[2]
    rx_ch3[capture] = rx_data[3]

    time.sleep(1)  # Small delay between captures

print(f"RX data captured - Ch0: {len(rx_ch0[-1])} samples, Ch1: {len(rx_ch1[-1])} samples")

# # Print signal statistics for verification
# print(f"TX Sample Rate: {sdr.tx_sample_rate/1e6:.2f} MSPS")
# print(f"RX Sample Rate: {sdr.rx_sample_rate/1e6:.2f} MSPS")
# print(f"TRX LO: {sdr.trx_lo/1e9:.2f} GHz")

# print(f"TX buffer duration: {len(iq)/fs*1000:.2f} ms")
# print(f"RX buffer duration: {rx_buffer_samples/rx_fs*1000:.2f} ms")

# print(f"TX I component range: [{np.min(iq_real)}, {np.max(iq_real)}]")
# print(f"TX Q component range: [{np.min(iq_imag)}, {np.max(iq_imag)}]")
# print(f"Expected cycles in buffer: {fc * len(iq) / fs:.2f}")

# print(f"TX Gain Ch0/Ch1: {sdr.tx_hardwaregain_chan0}/{sdr.tx_hardwaregain_chan1} dB")
# print(f"RX Gain Ch0/Ch1: {sdr.rx_hardwaregain_chan0}/{sdr.rx_hardwaregain_chan1} dB")

# print(f"TX Buffer Size: {sdr._tx_buffer_size} samples")
# print(f"RX Buffer Size: {sdr.rx_buffer_size} samples")

# Plot the results
plt.figure(figsize=(15, 10))

# Plot TX signal (time domain)
plt.subplot(6, 1, 1)
plt.plot(t[:N] * 1e6, np.real(pulse0_iq[:N]), 'b-')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('DAC0 TX Signal - Time Domain')
plt.grid(True)

# Plot TX signal (time domain)
plt.subplot(6, 1, 2)
plt.plot(t[:N] * 1e6, np.real(pulse1_iq[:N]), 'b-')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('DAC1 TX Signal - Time Domain')
plt.grid(True)

# Plot TX signal (time domain)
plt.subplot(6, 1, 3)
plt.plot(t[:N] * 1e6, np.real(pulse2_iq[:N]), 'b-')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('DAC2 TX Signal - Time Domain')
plt.grid(True)

# Plot TX signal (time domain)
plt.subplot(6, 1, 4)
plt.plot(t[:N] * 1e6, np.real(pulse3_iq[:N]), 'b-')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('DAC3 TX Signal - Time Domain')
plt.grid(True)

# # Plot tdd_data_offload pulse train for multiple frames
# plt.subplot(7, 1, 5)
# plt.plot(rx_t * 1e6, tdd_tx_offload_pulse_train[:len(rx_t)], 'g-')
# plt.title(f"TDD Data Offload Sync Pulse - Time Domain")
# plt.xlabel("Time (μs)")
# plt.ylabel("Pulse")
# plt.grid(True)

# Plot frame pulse train for multiple frames
plt.subplot(6, 1, 5)
plt.plot(rx_t * 1e6, pulse_train[:len(rx_t)], 'r-')
plt.title(f"RX Data Frame Pulse - Time Domain")
plt.xlabel("Time (μs)")
plt.ylabel("Pulse")
plt.grid(True)

# Plot RX Channel 0 (time domain)
plt.subplot(6, 1, 6)
for idx in range(capture_range):
    plt.plot(rx_t * 1e6, np.real(rx_ch0[idx]), label=f'Capture {idx}')
    plt.plot(rx_t * 1e6, np.real(rx_ch1[idx]), label=f'Capture {idx}')
    plt.plot(rx_t * 1e6, np.real(rx_ch2[idx]), label=f'Capture {idx}')
    plt.plot(rx_t * 1e6, np.real(rx_ch3[idx]), label=f'Capture {idx}')
plt.xlabel('Time (μs)')
plt.ylabel('Amplitude')
plt.title('Received data RX Channel 0 - Time Domain (All Captures)')
plt.grid(True)
plt.legend(loc="upper right")

plt.tight_layout()
plt.show()

# tddn.enable = 0

# for chan in [TDD_TX_OFFLOAD_SYNC, TDD_RX_OFFLOAD_SYNC, TDD_ENABLE, TDD_ADRV9009_RX_EN, TDD_ADRV9009_TX_EN]:
#     tddn.channel[chan].on_ms = 0
#     tddn.channel[chan].off_ms = 0
#     tddn.channel[chan].polarity = 0
#     tddn.channel[chan].enable = 1

# tddn.enable = 1
# tddn.enable = 0

# sdr.tx_destroy_buffer()
# sdr.rx_destroy_buffer()

