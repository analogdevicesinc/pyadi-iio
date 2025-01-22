# Copyright (C) 2024 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import matplotlib.pyplot as plt
import numpy as np

import adi

plt.close("all")

# This script uses the new Pluto TDD engine
# Make sure your Pluto firmware is updated to rev 0.39 (or later)
# And PYADI-IIO is rev 0.18 or greater
# TDD test with Pluto
# Connect a SMA cable from Tx1 to Rx1


# %% Configuration Variables
sample_rate = 10e6
center_freq = 2.1e9
signal_freq = 500e3
rx_gain = 20
tx_gain = -10

# %% Setup SDR
sdr_ip = "ip:192.168.2.1"  # usually "ip:192.168.2.1", or "ip:pluto.local"
gpio = adi.one_bit_adc_dac(sdr_ip)
my_sdr = adi.Pluto(uri=sdr_ip)
tddn = adi.tddn(sdr_ip)

# If you want repeatable alignment between transmit and receive then the rx_lo, tx_lo and sample_rate can only be set once after power up
# But if you don't care about this, then program sample_rate and LO's as much as you want
# So after bootup, check if the default sample_rate and LOs are being used, if so then program new ones!
if (
    30719990 < my_sdr.sample_rate < 30720009
    and 2399999990 < my_sdr.rx_lo < 2400000009
    and 2449999990 < my_sdr.tx_lo < 2450000009
):
    my_sdr.sample_rate = int(sample_rate)
    my_sdr.rx_lo = int(center_freq)
    my_sdr.tx_lo = int(center_freq)
    print("Pluto has just booted and I've set the sample rate and LOs!")


# Configure Rx
my_sdr.rx_enabled_channels = [0]
sample_rate = int(my_sdr.sample_rate)
# manual or slow_attack
my_sdr.gain_control_mode_chan0 = "manual"
my_sdr.rx_hardwaregain_chan0 = int(rx_gain)
# Default is 4 Rx buffers are stored, but to immediately see the result, set buffers=1
my_sdr._rxadc.set_kernel_buffers_count(1)

# Configure Tx
my_sdr.tx_enabled_channels = [0]
my_sdr.tx_hardwaregain_chan0 = int(tx_gain)
my_sdr.tx_cyclic_buffer = True  # must be true to use the TDD transmit

# Enable phaser logic in pluto
# when true, each channel[1] start outputs a pulse to Pluto L10P pin (TXDATA_1V8 on Phaser schematic)
gpio.gpio_phaser_enable = True

rx_time_ms = 4
tx_time_ms = rx_time_ms
frame_length_ms = rx_time_ms
capture_range = 100

frame_length_samples = int((rx_time_ms / 1000) * my_sdr.sample_rate)
N_rx = int(1 * frame_length_samples)
my_sdr.rx_buffer_size = N_rx

tddn.startup_delay_ms = 0
tddn.frame_length_ms = frame_length_ms
tddn.burst_count = 0  # 0 means repeat indefinitely

tddn.channel[0].on_raw = 0
tddn.channel[0].off_raw = 0
tddn.channel[0].polarity = 1
tddn.channel[0].enable = 1

# RX DMA SYNC
tddn.channel[1].on_raw = 0
tddn.channel[1].off_raw = 10
tddn.channel[1].polarity = 0
tddn.channel[1].enable = 1

# TX DMA SYNC
tddn.channel[2].on_raw = 0
tddn.channel[2].off_raw = 10
tddn.channel[2].polarity = 0
tddn.channel[2].enable = 1

tddn.sync_external = True  # enable external sync trigger
tddn.enable = True  # enable TDD engine

# Create a sinewave waveform
N = int(my_sdr.rx_buffer_size)
fc = signal_freq
ts = 1 / float(sample_rate)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 11
q = np.sin(2 * np.pi * t * fc) * 2 ** 11
iq = i + 1j * q

# Send data
print("sending IQ data")
my_sdr.tx(iq)

tddn.sync_soft = 1  # start the TDD transmit

# Print the configuration information
print(f"TX/RX Sampling_rate: {my_sdr.sample_rate}")
print(f"Number of samples in a frame: {frame_length_samples}")
print(f"RX buffer length: {N_rx}")
print(f"TX buffer length: {len(iq)}")
print(f"RX_receive time[ms]: {((1 / my_sdr.sample_rate) * N_rx) * 1000}")
print(f"TX_transmit time[ms]: {((1 / my_sdr.sample_rate) * len(iq)) * 1000}")
print(f"TDD_frame time[ms]: {tddn.frame_length_ms}")
print(f"TDD_frame time[raw]: {tddn.frame_length_raw}")

receive_array = np.zeros((capture_range, frame_length_samples)) * 1j

# Receive data
for r in range(capture_range):
    receive_array[r] = my_sdr.rx()

# Plot the received data
for i in range(r):
    plt.plot(receive_array[i].real)
    plt.xlim(0, 100)
plt.show()

# Pluto transmit shutdown
tddn.enable = 0
for i in range(3):
    tddn.channel[i].on_ms = 0
    tddn.channel[i].off_raw = 0
    tddn.channel[i].polarity = 0
    tddn.channel[i].enable = 1
tddn.enable = 1
tddn.enable = 0

my_sdr.tx_destroy_buffer()
print("Pluto Buffer Cleared!")
