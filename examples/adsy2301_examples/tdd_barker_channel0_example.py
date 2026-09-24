from adi import adsy2301 as mr
import math
import time

import adi
import matplotlib.pyplot as plt
import numpy as np


# USER CONFIGURABLE PARAMETERS
# Connection and radio settings
talise_ip = "10.75.161.151"
channel = 0
desired_rf_frequency_hz = 4500e6
tx_hardware_gain_db = -12
gain_control_mode = "slow_attack"

# Capture and radar timing
frame_pulses_to_plot = 2
capture_range = 3
frame_length_ms = 15e-3
tr_duty_cycle = 0.061
barker_code = np.array([1, 1, 1, 1, 1, -1, -1, 1, 1, -1, 1, -1, 1])

# TDD timing
tdd_sync_duty_cycle = 0.001
tdd_tx_offload_pulse_start_ms = 0.00001

# Signal and measurement settings
tx_pulse_start_ms = 0
tx_signal_amplitude = 0.8
tx_dac_scale = 2**15 - 1
minimum_correlation_score = 0.10
minimum_correlation_peak_ratio = 1.5
# Use 0 for direct loopback. Set to tr_pulse_time for radar echoes.
rx_search_start_ms = 0
capture_pause_seconds = 1
# END USER CONFIGURABLE PARAMETERS


talise_uri = "ip:" + talise_ip
dev = mr.adsy2301(uri=talise_uri)
dev.init_ADRV9009()
sdr = adi.adrv9009_zu11eg(talise_uri)
tddn = adi.tddn(talise_uri)

# Configure only channel 0.
sdr.tx_enabled_channels = [channel]
sdr.rx_enabled_channels = [channel]
sdr.tx_hardwaregain_chan0 = tx_hardware_gain_db
sdr.gain_control_mode_chan0 = gain_control_mode

fs = int(sdr.tx_sample_rate)
rx_fs = int(sdr.rx_sample_rate)
tdd_clock_hz = rx_fs
requested_frame_length_ms = frame_length_ms
requested_frame_seconds = requested_frame_length_ms * 1e-3

# Align the PRI to the TX, RX, and TDD clock grid.
common_clock_hz = math.gcd(math.gcd(fs, rx_fs), int(tdd_clock_hz))
frame_ticks = max(1, round(requested_frame_seconds * common_clock_hz))
frame_length_seconds = frame_ticks / common_clock_hz
frame_length_ms = frame_length_seconds * 1e3

# Derive the TX/TR timing from the aligned PRI.
target_pulse_seconds = frame_length_seconds * tr_duty_cycle
tx_pulse_samples = max(1, math.ceil(fs * target_pulse_seconds))
tx_pulse_duration_seconds = tx_pulse_samples / fs
tx_pulse_width_ms = tx_pulse_duration_seconds * 1e3
tx_pulse_stop_ms = tx_pulse_start_ms + tx_pulse_width_ms
tr_pulse_time = tx_pulse_width_ms
actual_tr_duty_cycle = tx_pulse_duration_seconds / frame_length_seconds

# Use one baseband cycle across the TX pulse and derive the LO.
baseband_frequency_hz = 1 / tx_pulse_duration_seconds
trx_lo_hz = desired_rf_frequency_hz - baseband_frequency_hz
sdr.trx_lo = int(trx_lo_hz)
tdd_frame_raw = frame_ticks * (int(tdd_clock_hz) // common_clock_hz)
tdd_sync_pulse_raw = max(1, round(tdd_frame_raw * tdd_sync_duty_cycle))

N = int(fs * frame_length_seconds)
if N < 1 or tx_pulse_samples < 1:
    raise ValueError("The configured frame and pulse must contain samples")
if tx_pulse_stop_ms > frame_length_ms:
    raise ValueError("TX pulse must fit inside the frame")

# Build the exact complex Barker waveform transmitted on channel 0.
barker_samples = tx_pulse_samples
barker_chip_samples = barker_samples / len(barker_code)
barker_indices = (np.arange(barker_samples) * len(barker_code) // barker_samples).astype(int)
barker_sequence = barker_code[barker_indices]
tx_time = np.arange(barker_samples) / fs
barker_carrier = np.exp(1j * 2 * np.pi * baseband_frequency_hz * tx_time)
tx_barker = tx_signal_amplitude * barker_sequence * barker_carrier

data = np.zeros(N, dtype=np.complex128)
tx_start_sample = int(fs * tx_pulse_start_ms * 1e-3)
tx_stop_sample = min(tx_start_sample + barker_samples, N)
data[tx_start_sample:tx_stop_sample] = tx_barker[:tx_stop_sample - tx_start_sample]
iq = np.int16(np.real(data) * tx_dac_scale) + 1j * np.int16(np.imag(data) * tx_dac_scale)

# Configure cyclic TX offload and the single RX channel.
sdr._txdac.debug_attrs["pl_ddr_fifo_enable"].value = "1"
sdr.tx_cyclic_buffer = True
rx_ts = 1 / float(rx_fs)
samples_per_frame = int(round(frame_length_seconds / rx_ts))
if samples_per_frame < 1:
    raise ValueError("Frame must contain at least one RX sample")
rx_buffer_samples = frame_pulses_to_plot * samples_per_frame
sdr.rx_buffer_size = rx_buffer_samples
rx_t = np.arange(rx_buffer_samples) * rx_ts

# TDD channel IDs for this ADSY2301 design.
TDD_TX_OFFLOAD_SYNC = 0
TDD_RX_OFFLOAD_SYNC = 1
TDD_ENABLE = 2
TDD_ADRV9009_RX_EN = 3
TDD_ADRV9009_TX_EN = 4
TDD_PA_ON = 6
TDD_TR_PULSE = 7
TDD_RX_LOAD = 12
TDD_TX_LOAD = 13
ALL_CHANNELS = [
    TDD_ENABLE, TDD_ADRV9009_RX_EN, TDD_ADRV9009_TX_EN, TDD_PA_ON,
    TDD_TX_OFFLOAD_SYNC, TDD_RX_OFFLOAD_SYNC, TDD_RX_LOAD, TDD_TX_LOAD,
    TDD_TR_PULSE,
]

# Configure TDD.
tddn.enable = 0
tddn.frame_length_ms = frame_length_ms
programmed_frame_length_ms = float(tddn.frame_length_ms)
programmed_frame_length_raw = float(tddn.frame_length_raw)
print(f"Requested TDD PRI: {requested_frame_length_ms * 1e3:.3f} us")
print(f"Programmed TDD PRI: {programmed_frame_length_ms * 1e3:.3f} us")
print(f"Programmed TDD frame length: {programmed_frame_length_raw:.0f} raw clock cycles")
if not math.isclose(programmed_frame_length_ms, requested_frame_length_ms, rel_tol=0, abs_tol=1e-9):
    print(
        f"TDD hardware adjusted the requested PRI from {requested_frame_length_ms * 1e3:.3f} us "
        f"to {programmed_frame_length_ms * 1e3:.3f} us"
    )

for chan in [TDD_ENABLE, TDD_ADRV9009_RX_EN, TDD_ADRV9009_TX_EN, TDD_PA_ON]:
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable = 1
for chan in [TDD_TX_OFFLOAD_SYNC, TDD_RX_OFFLOAD_SYNC, TDD_RX_LOAD, TDD_TX_LOAD]:
    tddn.channel[chan].on_raw = 0
    tddn.channel[chan].off_raw = tdd_sync_pulse_raw
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable = 1
tddn.channel[TDD_TR_PULSE].on_ms = 0
tddn.channel[TDD_TR_PULSE].off_ms = tr_pulse_time
tddn.channel[TDD_TR_PULSE].polarity = 0
tddn.channel[TDD_TR_PULSE].enable = 1
tddn.enable = 1

# Build expected TDD timing signals.
tr_pulse_train = np.zeros(rx_buffer_samples)
tdd_tx_offload_pulse_train = np.zeros(rx_buffer_samples)
tr_pulse_samples = int(tr_pulse_time * 1e-3 / rx_ts)
tdd_tx_offload_pulse_start = int(tdd_tx_offload_pulse_start_ms * 1e-3 / rx_ts)
for frame in range(frame_pulses_to_plot):
    frame_start = frame * samples_per_frame
    tr_pulse_train[frame_start:frame_start + tr_pulse_samples] = 1
    sync_start = frame_start + tdd_tx_offload_pulse_start
    tdd_tx_offload_pulse_train[sync_start:sync_start + tdd_sync_pulse_raw] = 1

# Transmit and capture channel 0.
sdr.tx_destroy_buffer()
sdr.tx(iq)
tddn.sync_soft = 1
rx_captures = np.zeros((capture_range, rx_buffer_samples), dtype=np.complex64)
print("Capturing RX channel 0...")
for capture in range(capture_range):
    sdr.rx_destroy_buffer()
    tddn.sync_soft = 1
    rx_data = sdr.rx()
    rx_captures[capture] = rx_data[0]
    time.sleep(capture_pause_seconds)

# Matched-filter against the Barker burst and fold scores across repeated frames.
barker_rx_samples = max(1, math.ceil(barker_samples * rx_fs / fs))
barker_rx_time = np.arange(barker_rx_samples) / rx_fs
barker_template_rx = np.interp(
    barker_rx_time, np.arange(barker_samples) / fs, barker_sequence
).astype(np.complex128)
template_energy = np.sum(np.abs(barker_template_rx) ** 2)
demodulation_time = np.arange(rx_buffer_samples) / rx_fs
demodulation_carrier = np.exp(-1j * 2 * np.pi * baseband_frequency_hz * demodulation_time)
rx_search_start_samples = int(rx_search_start_ms * 1e-3 * rx_fs)
rx_delay_samples = []
rx_correlation_scores = []

for capture in rx_captures:
    direct = np.correlate(capture * demodulation_carrier, barker_template_rx, mode="valid")
    image = np.correlate(capture * np.conj(demodulation_carrier), barker_template_rx, mode="valid")
    window_energy = np.convolve(np.abs(capture) ** 2, np.ones(barker_rx_samples), mode="valid")
    normalized = np.maximum(np.abs(direct), np.abs(image)) / np.sqrt(
        np.maximum(window_energy * template_energy, np.finfo(float).eps)
    )
    max_frame_offset = samples_per_frame - barker_rx_samples
    frame_offsets = np.arange(max_frame_offset + 1)
    frame_indices = (
        np.arange(frame_pulses_to_plot)[:, np.newaxis] * samples_per_frame
        + frame_offsets[np.newaxis, :]
    )
    folded_scores = np.mean(normalized[frame_indices], axis=0)
    folded_scores[:rx_search_start_samples] = 0
    peak_offset = int(np.argmax(folded_scores))
    peak_score = folded_scores[peak_offset]
    background = folded_scores[rx_search_start_samples:]
    background_median = np.median(background)
    peak_ratio = peak_score / max(background_median, np.finfo(float).eps)
    if peak_score < minimum_correlation_score or peak_ratio < minimum_correlation_peak_ratio:
        raise RuntimeError(
            f"No reliable Barker signal found: peak={peak_score:.3f}, "
            f"background={background_median:.3f}, peak/background={peak_ratio:.2f}, "
            f"RX peak amplitude={np.max(np.abs(capture)):.1f}"
        )
    rx_delay_samples.append(peak_offset)
    rx_correlation_scores.append(peak_score)

rx_delay_samples = np.asarray(rx_delay_samples)
rx_correlation_scores = np.asarray(rx_correlation_scores)
rx_delay_ns = rx_delay_samples / rx_fs * 1e9
rx_arrival_time_us = rx_delay_ns / 1000
tr_fall_time_us = (tx_pulse_start_ms + tr_pulse_time) * 1e3

print(f"Channel: {channel}")
print(f"Desired RF frequency: {desired_rf_frequency_hz / 1e9:.6f} GHz")
print(f"Calculated baseband frequency: {baseband_frequency_hz / 1e6:.6f} MHz")
print(f"Calculated TRX LO: {trx_lo_hz / 1e9:.6f} GHz")
print(f"Aligned PRI: {frame_length_seconds * 1e6:.3f} us")
print(f"Requested TR duty cycle: {tr_duty_cycle * 100:.3f}%")
print(f"Actual TR duty cycle: {actual_tr_duty_cycle * 100:.3f}%")
print(f"Barker code length: {len(barker_code)} chips")
print(f"Barker chip width: {barker_chip_samples:.3f} TX samples")
print(f"Configured TR pulse goes low at: {tr_fall_time_us:.3f} us")
print("Frame-relative TX-to-RX delay from Barker matched correlation:")
for capture, delay in enumerate(rx_delay_ns):
    print(
        f"  Capture {capture}: RX received at {rx_arrival_time_us[capture]:.3f} us "
        f"({delay:.1f} ns, {rx_delay_samples[capture]} RX samples, "
        f"correlation={rx_correlation_scores[capture]:.3f})"
    )
print(f"Mean delay: {np.mean(rx_delay_ns):.1f} ns")
print(f"Delay spread: {np.ptp(rx_delay_ns):.1f} ns")

# Plot TDD sync, TX Barker waveform, TR timing, and channel-0 RX captures.
plot_x = rx_t * 1e6
fig, axes = plt.subplots(4, 1, figsize=(15, 10), sharex=True)
axes[0].plot(plot_x, tdd_tx_offload_pulse_train, "g-")
axes[0].set_title("TDD Data Offload Sync Pulse")
tx_plot = np.interp(np.arange(rx_buffer_samples) / rx_fs, np.arange(N) / fs, np.real(data))
axes[1].plot(plot_x, tx_plot, "b-")
axes[1].set_title("TX Barker-Coded Data, Channel 0")
axes[2].plot(plot_x, tr_pulse_train, "m-")
axes[2].set_title("TR Pulse")
for capture in rx_captures:
    axes[3].plot(plot_x, np.real(capture), "--", alpha=0.45)
axes[3].set_title("RX Channel 0 Data with Barker Correlation")

for axis in axes:
    axis.set_xlim(plot_x[0], frame_pulses_to_plot * frame_length_seconds * 1e6)
    axis.set_xlabel("Time (us)")
    axis.grid(True)
for boundary in range(1, frame_pulses_to_plot):
    for axis in axes:
        axis.axvline(boundary * frame_length_seconds * 1e6, color="k", linestyle="--", alpha=0.7)
plt.tight_layout()
plt.show()

tddn.enable = 0
for chan in ALL_CHANNELS:
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable = 1
tddn.enable = 0
sdr.tx_destroy_buffer()
sdr.rx_destroy_buffer()
