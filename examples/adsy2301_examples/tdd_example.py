from adi import adsy2301 as mr
import time
import adi
import matplotlib.pyplot as plt
import numpy as np
import math


# USER CONFIGURABLE PARAMETERS
talise_ip = "10.75.161.151"
tx_enabled_channels = [0, 1]
rx_enabled_channels = [0, 1]
desired_rf_frequency_hz = 4500e6
tx_hardware_gain_db = [-12, -12]
gain_control_mode = "slow_attack"

frame_pulses_to_plot = 3
capture_range = 5
frame_length_ms = 50e-3
tr_duty_cycle = 0.20
rf_cycles_to_transmit = 10

# TDD raw timing and offload-sync pulse settings.

tdd_tx_offload_pulse_start_ms = 0.00001
tx_pulse_start_ms = 0
tx_signal_amplitude = 0.1
tx_dac_scale = 2**15 - 1
capture_pause_seconds = 1
# END USER CONFIGURABLE PARAMETERS

tdd_clock_hz = 250e6
tdd_sync_duty_cycle = 0.0010

talise_uri = "ip:" + talise_ip

dev = mr.adsy2301(uri=talise_uri)
dev.init_ADRV9009()

# mr.tdd_init(dev,TXRX_Bit=0)
# mr.change_duty_cycle(dev,PRI_ms=0.1,off_ms=0.005)

# Create radio
sdr  = adi.adrv9009_zu11eg(talise_uri)
tddn = adi.tddn(talise_uri)

# Configure TX properties
sdr.tx_enabled_channels = tx_enabled_channels
sdr.tx_hardwaregain_chan0 = tx_hardware_gain_db[0]
sdr.tx_hardwaregain_chan1 = tx_hardware_gain_db[1]
sdr.gain_control_mode_chan0 = gain_control_mode
sdr.gain_control_mode_chan1 = gain_control_mode

# Derived pulse timing.
tx_pulse_width_ms = frame_length_ms * tr_duty_cycle
tx_pulse_stop_ms = tx_pulse_start_ms + tx_pulse_width_ms
tr_pulse_time = tx_pulse_width_ms

# Prepare TX data
fs = int(sdr.tx_sample_rate)
rx_fs = int(sdr.rx_sample_rate)
requested_frame_seconds = frame_length_ms * 1e-3

# Quantize the PRI to a period representable by the TX, RX, and TDD clocks.
# This prevents each subsystem from rounding the requested frame differently.
common_clock_hz = math.gcd(math.gcd(fs, rx_fs), int(tdd_clock_hz))
frame_ticks = max(1, round(requested_frame_seconds * common_clock_hz))
frame_length_seconds = frame_ticks / common_clock_hz
frame_length_ms = frame_length_seconds * 1e3
# Quantize the requested duty-cycle interval to whole TX samples. The actual
# TX/TR duty cycle is derived from this quantized width below.
target_pulse_seconds = frame_length_seconds * tr_duty_cycle
tx_pulse_samples = max(1, math.ceil(fs * target_pulse_seconds))
tx_pulse_duration_seconds = tx_pulse_samples / fs
tx_pulse_width_ms = tx_pulse_duration_seconds * 1e3
tx_pulse_stop_ms = tx_pulse_start_ms + tx_pulse_width_ms
tr_pulse_time = tx_pulse_width_ms
actual_tr_duty_cycle = tx_pulse_duration_seconds / frame_length_seconds
tdd_frame_raw = frame_ticks * (int(tdd_clock_hz) // common_clock_hz)
tdd_sync_pulse_raw = max(1, round(tdd_frame_raw * tdd_sync_duty_cycle))
# Calculate the LO so LO + baseband produces the desired RF frequency.
baseband_frequency_hz = rf_cycles_to_transmit / tx_pulse_duration_seconds
trx_lo_hz = desired_rf_frequency_hz - baseband_frequency_hz
sdr.trx_lo = int(trx_lo_hz)
fc = baseband_frequency_hz
# calculate N for full frame duration: N = fs * frame_length_seconds
N = int(fs * frame_length_seconds)
ts = 1 / float(fs)

# Calculate the TX pulse timing from the aligned, sample-quantized width.
rf_samples_per_cycle = math.ceil(fs / baseband_frequency_hz)
minimum_tx_samples = rf_cycles_to_transmit * rf_samples_per_cycle
tx_start_sample = int(fs * tx_pulse_start_ms * 1e-3)

if frame_length_seconds <= 0 or N < 1:
    raise ValueError("frame_length_ms must produce at least one TX sample")
if tx_pulse_duration_seconds <= 0 or tx_pulse_samples < 1:
    raise ValueError("tx_pulse_width_ms must produce at least one TX sample")
if tx_pulse_stop_ms > frame_length_ms:
    raise ValueError("TX/TR pulse must fit inside frame_length_ms")

# Create full time vector for entire frame
t = np.arange(0, N * ts, ts)

# Create full frame with zeros
i = np.zeros(N)
q = np.zeros(N)

# Generate sine wave only for the TX pulse period
for n in range(tx_start_sample, min(tx_start_sample + tx_pulse_samples, N)):
    t_sample = n * ts
    i[n] = np.cos(2 * np.pi * fc * t_sample) * tx_signal_amplitude
    q[n] = np.sin(2 * np.pi * fc * t_sample) * tx_signal_amplitude

data = i + 1j * q

# scaling for 16-bit DAC
# use most of the dynamic range but avoid clipping
iq_real = np.int16(np.real(data) * tx_dac_scale)
iq_imag = np.int16(np.imag(data) * tx_dac_scale)
iq = iq_real + 1j * iq_imag

# Configure TX data offload mode to cyclic
sdr._txdac.debug_attrs["pl_ddr_fifo_enable"].value = "1"
sdr.tx_cyclic_buffer = True

# Configure RX parameters
sdr.rx_enabled_channels = rx_enabled_channels

# Use an integer number of RX samples per frame so the capture window and
# the TDD PRI cannot diverge due to separate duration rounding.
rx_ts = 1 / float(rx_fs)
samples_per_frame = int(round(frame_length_seconds / rx_ts))
if samples_per_frame < 1:
    raise ValueError("frame_length_ms must produce at least one RX sample")
rx_buffer_samples = frame_pulses_to_plot * samples_per_frame
sdr.rx_buffer_size = rx_buffer_samples

# Create time vector for plotting
rx_t = np.arange(0, rx_buffer_samples * rx_ts, rx_ts)

# TDD signal channels

# TDD_TX_OFFLOAD_SYNC = 0
# TDD_RX_OFFLOAD_SYNC = 1
# TDD_ENABLE      = 6
# TDD_ADRV9009_RX_EN = 7
# TDD_ADRV9009_TX_EN = 8
# TDD_PA_ON     = 10  # PA_ON_0, PA_ON_1, PA_ON_2, PA_ON_3
# TDD_TR_PULSE     = 11  # TR Pulse
# TDD_RX_LOAD = 4
# TDD_TX_LOAD = 5

TDD_TX_OFFLOAD_SYNC = 0
TDD_RX_OFFLOAD_SYNC = 1
TDD_ENABLE      = 2
TDD_ADRV9009_RX_EN = 3
TDD_ADRV9009_TX_EN = 4
# TDD_ADSY2301_EN = 5
TDD_PA_ON     = 6  # PA_ON_0, PA_ON_1, PA_ON_2, PA_ON_3
TDD_TR_PULSE     = 7  # TR Pulse
TDD_RX_LOAD = 12
TDD_TX_LOAD = 13
    

ALWAYS_ON = [TDD_ENABLE, TDD_ADRV9009_RX_EN, TDD_ADRV9009_TX_EN, TDD_PA_ON]
TRIGGERS = [TDD_TX_OFFLOAD_SYNC, TDD_RX_OFFLOAD_SYNC, TDD_RX_LOAD, TDD_TX_LOAD]
ALL_CHANNELS = ALWAYS_ON + TRIGGERS + [TDD_TR_PULSE]

#Configure TDD engine
tddn.enable = 0

# tddn.burst_count          = 0 # continuous mode, period repetead forever
# tddn.startup_delay_ms     = 0
tddn.frame_length_ms      = frame_length_ms

for chan in [TDD_ENABLE, TDD_ADRV9009_RX_EN, TDD_ADRV9009_TX_EN, TDD_PA_ON]:
    tddn.channel[chan].on_ms   = 0
    tddn.channel[chan].off_ms  = 0
    tddn.channel[chan].polarity = 1
    tddn.channel[chan].enable   = 1

for chan in [TDD_TX_OFFLOAD_SYNC, TDD_RX_OFFLOAD_SYNC, TDD_RX_LOAD, TDD_TX_LOAD]:
    tddn.channel[chan].on_raw   = 0
    tddn.channel[chan].off_raw  = tdd_sync_pulse_raw
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable   = 1

tddn.channel[TDD_TR_PULSE].on_ms = 0
tddn.channel[TDD_TR_PULSE].off_ms = tr_pulse_time
tddn.channel[TDD_TR_PULSE].polarity = 0
tddn.channel[TDD_TR_PULSE].enable = 1

tddn.enable = 1

# Create the TR pulse train for the entire RX buffer duration
tr_pulse_train = np.zeros(rx_buffer_samples)
tr_pulse_samples = int(tr_pulse_time * 1e-3 / rx_ts)

for frame in range(frame_pulses_to_plot):
    tr_pulse_frame_start = frame * samples_per_frame
    tr_pulse_start = tr_pulse_frame_start
    tr_pulse_stop = tr_pulse_start + tr_pulse_samples
    tr_pulse_train[tr_pulse_start:tr_pulse_stop] = 1

tdd_tx_offload_frame_length_ms = frame_length_ms

# off_raw is in samples, so convert to time for offset calculation
off_raw_samples = tddn.channel[TDD_TX_OFFLOAD_SYNC].off_raw

# Create pulse train for the entire RX buffer duration
tdd_tx_offload_pulse_train = np.zeros(rx_buffer_samples)

# Calculate samples per frame and pulse
tdd_tx_offload_samples_per_frame = samples_per_frame
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

# Capture RX data
print("Capturing RX data...")

rx_ch0 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
rx_ch1 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)

for capture in range(capture_range):
    sdr.rx_destroy_buffer()
    tddn.sync_soft  = 1

    rx_data = sdr.rx()

    # Extract I/Q data for both channels
    rx_ch0[capture] = rx_data[0]
    rx_ch1[capture] = rx_data[1]

    time.sleep(capture_pause_seconds)

print(f"RX data captured - Ch0: {len(rx_ch0[-1])} samples, Ch1: {len(rx_ch1[-1])} samples")

# Print signal statistics for verification
print(f"TX Sample Rate: {sdr.tx_sample_rate/1e6:.2f} MSPS")
print(f"RX Sample Rate: {sdr.rx_sample_rate/1e6:.2f} MSPS")
print(f"Desired RF frequency: {desired_rf_frequency_hz / 1e9:.6f} GHz")
print(f"Calculated baseband frequency: {baseband_frequency_hz / 1e6:.6f} MHz")
print(f"Calculated TRX LO: {trx_lo_hz / 1e9:.6f} GHz")
print(f"Requested PRI: {requested_frame_seconds * 1e6:.3f} us")
print(f"Aligned PRI: {frame_length_seconds * 1e6:.3f} us")
print(f"Common timing clock: {common_clock_hz / 1e6:.6f} MHz")
print(f"TX/TR-high duration: {tx_pulse_duration_seconds * 1e6:.3f} us")
print(f"Requested TR duty cycle: {tr_duty_cycle * 100:.6f}%")
print(f"Actual aligned TR duty cycle: {actual_tr_duty_cycle * 100:.6f}%")
print(f"Baseband period: {1e6 / fc:.3f} us ({rf_samples_per_cycle} TX samples)")
print(f"TX RF cycles: {tx_pulse_samples / rf_samples_per_cycle:.2f}")

print(f"TX buffer duration: {len(iq)/fs*1000:.2f} ms")
print(f"RX buffer duration: {rx_buffer_samples/rx_fs*1000:.2f} ms")

print(f"TX I component range: [{np.min(iq_real)}, {np.max(iq_real)}]")
print(f"TX Q component range: [{np.min(iq_imag)}, {np.max(iq_imag)}]")
print(f"Expected cycles in buffer: {fc * len(iq) / fs:.2f}")

print(f"TX Gain Ch0/Ch1: {sdr.tx_hardwaregain_chan0}/{sdr.tx_hardwaregain_chan1} dB")
print(f"RX Gain Ch0/Ch1: {sdr.rx_hardwaregain_chan0}/{sdr.rx_hardwaregain_chan1} dB")

print(f"TX Buffer Size: {sdr._tx_buffer_size} samples")
print(f"RX Buffer Size: {sdr.rx_buffer_size} samples")

# Measure the delay from complex-IQ cross-correlation. Resample the known TX
# frame onto the RX clock so the correlation lag is expressed in RX samples.
tx_frame_time = np.arange(N) / fs
rx_frame_time = np.arange(samples_per_frame) / rx_fs
tx_reference_rx = (
    np.interp(rx_frame_time, tx_frame_time, np.real(iq[:N]))
    + 1j * np.interp(rx_frame_time, tx_frame_time, np.imag(iq[:N]))
)
rx_delay_samples = []

for capture in rx_ch0:
    rx_frame = capture[:samples_per_frame]
    correlation = np.correlate(rx_frame, tx_reference_rx, mode='full')
    zero_lag_index = len(tx_reference_rx) - 1
    positive_lag_correlation = correlation[zero_lag_index:]
    rx_delay_samples.append(int(np.argmax(np.abs(positive_lag_correlation))))

rx_delay_samples = np.asarray(rx_delay_samples)
rx_delay_ns = rx_delay_samples / rx_fs * 1e9
print("TX-to-RX delay from complex-IQ cross-correlation:")
for capture, delay in enumerate(rx_delay_ns):
    print(f"  Capture {capture}: {delay:.1f} ns ({rx_delay_samples[capture]} RX samples)")
print(f"Mean cross-correlation delay: {np.mean(rx_delay_ns):.1f} ns")
print(f"Delay spread: {np.ptp(rx_delay_ns):.1f} ns")

# Plot the results
fig, axes = plt.subplots(4, 1, figsize=(15, 10), sharex=True)
plot_x = rx_t * 1e6
plot_x_min = plot_x[0]
plot_x_max = frame_pulses_to_plot * frame_length_seconds * 1e6

# Plot TDD data offload sync pulse first
axes[0].plot(plot_x, tdd_tx_offload_pulse_train[:len(rx_t)], 'g-')
axes[0].set_title('TDD Data Offload Sync Pulse - Time Domain')
axes[0].set_xlabel('Time (μs)')
axes[0].set_ylabel('Pulse')
axes[0].grid(True)

# Plot TX data frame (time domain)
ax = axes[1]
tx_plot = np.real(iq[:N]).astype(float)
tx_plot /= max(np.max(np.abs(tx_plot)), 1)
tx_frame_time = np.arange(N) / fs
tx_frame_phase = np.mod(rx_t, frame_length_seconds)
tx_repeated = np.interp(tx_frame_phase, tx_frame_time, tx_plot)
ax.plot(rx_t * 1e6, tx_repeated, 'b-', label='TX Data Frame')
ax.set_xlabel('Time (μs)')
ax.set_ylabel('Normalized amplitude')
ax.set_title('TX Data Frame - Time Domain')
ax.grid(True)
ax.legend(loc='upper right', fontsize='small')

# Plot TR pulse between TX and RX
axes[2].plot(plot_x, tr_pulse_train[:len(rx_t)], 'm-')
axes[2].set_title('TR Pulse - Time Domain')
axes[2].set_xlabel('Time (μs)')
axes[2].set_ylabel('Pulse')
axes[2].grid(True)

# Plot RX data frames and correlation delays (time domain)
ax = axes[3]
for capture in range(capture_range):
    rx_plot = np.real(rx_ch0[capture]).astype(float)
    rx_plot /= max(np.max(np.abs(rx_plot)), 1)
    ax.plot(
        plot_x,
        rx_plot,
        '--',
        alpha=0.45,
        label='RX Data Frame' if capture == 0 else None,
    )
ax.set_xlabel('Time (μs)')
ax.set_ylabel('Normalized amplitude')
ax.set_title('RX Data Frames - Time Domain')
ax.grid(True)
ax.legend(loc='upper right', fontsize='small')

for shared_ax in axes:
    shared_ax.set_xlim(plot_x_min, plot_x_max)
    shared_ax.tick_params(axis='x', labelbottom=True)

# Mark each frame boundary on every subplot.
for frame_boundary in range(1, frame_pulses_to_plot):
    boundary_time_us = frame_boundary * frame_length_seconds * 1e6
    for shared_ax in axes:
        shared_ax.axvline(
            boundary_time_us,
            color='k',
            linestyle='--',
            linewidth=1,
            alpha=0.7,
        )

plt.tight_layout()
plt.show()

tddn.enable = 0

for chan in ALL_CHANNELS:
    tddn.channel[chan].on_ms = 0
    tddn.channel[chan].off_ms = 0
    tddn.channel[chan].polarity = 0
    tddn.channel[chan].enable = 1

tddn.enable = 1
tddn.enable = 0

sdr.tx_destroy_buffer()
sdr.rx_destroy_buffer()