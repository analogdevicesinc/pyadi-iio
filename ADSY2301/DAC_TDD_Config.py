# ==========================================================================
# ADSY2301 — DAC Waveform Generation & TDD Engine Configuration
# --------------------------------------------------------------------------
# This script configures the ADRV9009-ZU11EG transmit path and TDD timing
# engine for the ADSY2301 evaluation system.  It:
#   1. Connects to the ADRV9009-ZU11EG SoM and ADXUD1AEBZ up/down-converter.
#   2. Sets TX/RX gain and AGC modes.
#   3. Generates 4-channel pulsed I/Q waveforms at a configurable PRI and
#      duty cycle, then loads them into the DAC via Data Offload.
#   4. Programs the TDD engine channel timing (sync, enable, TR pulse, etc.).
#   5. Arms the TDD engine and triggers a soft-sync.
#
# USER-ADJUSTABLE PARAMETERS are at the top of the file (PRI, duty cycle,
# carrier frequency, etc.).
#
# Copyright (C) 2025 Analog Devices, Inc.
# SPDX short identifier: ADIBSD
# ==========================================================================

import adi
import numpy as np
import matplotlib.pyplot as plt

# ==========================================================================
# USER CONFIGURATION
# ==========================================================================
talise_uri = "ip:192.168.1.1"  # IP address of the ADRV9009-ZU11EG SoM

## Pulse Parameters ##
PRI_ms = 0.1       # Pulse repetition interval (ms)
DAC_duty_cycle = 1.0   # Duty cycle for DAC pulses (0.0 to 1.0)

## Initialize Talise SOM DACs ##
# The loop runs twice to ensure a clean init (first pass may fail after
# a cold boot; second pass confirms settings are applied).
for i in range(2):
    # Create radio and initialize TDD engine
    sdr  = adi.adrv9009_zu11eg(talise_uri)
    ctx = sdr._ctrl.ctx
    tddn = adi.tddn(talise_uri)

    # Setup ADXUD1AEBZ
    xud = ctx.find_device("xud_control")

    ## Updated XUD settings, PLLselect and RxGainMode ##
    PLLselect = xud.find_channel("voltage1", True)
    rxgainmode = xud.find_channel("voltage0", True)

    # XUD1A settings for Tx/Rx synchronization
    # 0 for rx, 1 for tx

    PLLselect.attrs["raw"].value = "1"
    rxgainmode.attrs["raw"].value = "0"


    # Configure TX/RX hardware gains (0 dB)
    sdr.tx_enabled_channels = [0, 1, 2, 3]
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

    ## RX frame and pulse timing (in milliseconds)
    frame_length_ms = 0.1    # 100 us frame
    tx_pulse_start_ms = 0.00001  # 10 ns offset
    tx_pulse_stop_ms = 0.100     # 100 us pulse width


    # Pulse parameters
    PRI_ms = 0.1                    # 100 us pulse repetition interval
    DAC_duty_cycle = 1                  # 100% duty cycle (CW mode)
    pulse_spacing_ms = 0.002        # 2 us spacing between pulse start times
    pulse_start_buffer_ms = 0.00001 # 10 ns guard
    pulse0_start_ms = pulse_start_buffer_ms
    pulse0_stop_ms = DAC_duty_cycle * PRI_ms + pulse_start_buffer_ms
    pulse1_start_ms = pulse0_stop_ms + pulse_spacing_ms
    pulse1_stop_ms = pulse1_start_ms + DAC_duty_cycle * PRI_ms
    pulse2_start_ms = pulse1_stop_ms + pulse_spacing_ms
    pulse2_stop_ms = pulse2_start_ms + DAC_duty_cycle * PRI_ms
    pulse3_start_ms = pulse2_stop_ms + pulse_spacing_ms
    pulse3_stop_ms = pulse3_start_ms + DAC_duty_cycle * PRI_ms

    # Prepare TX data
    fs = int(sdr.tx_sample_rate)
    frame_length_seconds = PRI_ms * 1e-3
    # TX carrier frequency (Hz)
    fc = 1000e3
    # calculate N for full frame duration: N = fs * frame_length_seconds
    N = int(fs * frame_length_seconds)
    ts = 1 / float(fs)
    frame_length_ms = PRI_ms

    #######################
    ## Setup DAC outputs ##
    #######################
    # Calculate samples for TX pulse duration
    pulse0_duration_ms = pulse0_stop_ms - pulse0_start_ms
    pulse0_duration_seconds = pulse0_duration_ms * 1e-3
    pulse0_samples = int(fs * pulse0_duration_seconds)
    pulse0_start_sample = int(fs * pulse0_start_ms * 1e-3)
    pulse1_duration_ms = pulse1_stop_ms - pulse1_start_ms
    pulse1_duration_seconds = pulse1_duration_ms * 1e-3
    pulse1_samples = int(fs * pulse1_duration_seconds)
    pulse1_start_sample = int(fs * pulse1_start_ms * 1e-3)
    pulse2_duration_ms = pulse2_stop_ms - pulse2_start_ms
    pulse2_duration_seconds = pulse2_duration_ms * 1e-3
    pulse2_samples = int(fs * pulse2_duration_seconds)
    pulse2_start_sample = int(fs * pulse2_start_ms * 1e-3)
    pulse3_duration_ms = pulse3_stop_ms - pulse3_start_ms
    pulse3_duration_seconds = pulse3_duration_ms * 1e-3
    pulse3_samples = int(fs * pulse3_duration_seconds)
    pulse3_start_sample = int(fs * pulse3_start_ms * 1e-3)

    # Create full time vector for entire frame
    t = np.arange(0, N * ts, ts)

    # Create full frame with zeros
    pulse0_i = np.zeros(N)
    pulse0_q = np.zeros(N)
    pulse1_i = np.zeros(N)
    pulse1_q = np.zeros(N)
    pulse2_i = np.zeros(N)
    pulse2_q = np.zeros(N)
    pulse3_i = np.zeros(N)
    pulse3_q = np.zeros(N)

    for n in range(pulse0_start_sample, min(pulse0_start_sample + pulse0_samples, N)):
        t_sample = n * ts
        pulse0_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
        pulse0_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1
    for n in range(pulse1_start_sample, min(pulse1_start_sample + pulse1_samples, N)):
        t_sample = n * ts
        pulse1_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
        pulse1_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1
    for n in range(pulse2_start_sample, min(pulse2_start_sample + pulse2_samples, N)):
        t_sample = n * ts
        pulse2_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
        pulse2_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1
    for n in range(pulse3_start_sample, min(pulse3_start_sample + pulse3_samples, N)):
        t_sample = n * ts
        pulse3_i[n] = np.cos(2 * np.pi * fc * t_sample) * 1
        pulse3_q[n] = np.sin(2 * np.pi * fc * t_sample) * 1

    pulse0_data = pulse0_i + 1j * pulse0_q
    pulse1_data = pulse1_i + 1j * pulse1_q
    pulse2_data = pulse2_i + 1j * pulse2_q
    pulse3_data = pulse3_i + 1j * pulse3_q

    sdr.tx_destroy_buffer()

    # scaling for 16-bit DAC
    # use most of the dynamic range but avoid clipping
    scale_factor = 2**15 - 1
    pulse0_iq_real = np.int16(np.real(pulse0_data) * scale_factor)
    pulse0_iq_imag = np.int16(np.imag(pulse0_data) * scale_factor)
    pulse0_iq = pulse0_iq_real + 1j * pulse0_iq_imag
    pulse1_iq_real = np.int16(np.real(pulse1_data) * scale_factor)
    pulse1_iq_imag = np.int16(np.imag(pulse1_data) * scale_factor)
    pulse1_iq = pulse1_iq_real + 1j * pulse1_iq_imag
    pulse2_iq_real = np.int16(np.real(pulse2_data) * scale_factor)
    pulse2_iq_imag = np.int16(np.imag(pulse2_data) * scale_factor)
    pulse2_iq = pulse2_iq_real + 1j * pulse2_iq_imag
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

    ###########################
    # TDD Engine Configuration
    ###########################

    TDD_TX_OFFLOAD_SYNC = 0
    TDD_RX_OFFLOAD_SYNC = 1
    TDD_ENABLE      = 2
    TDD_ADRV9009_RX_EN = 3
    TDD_ADRV9009_TX_EN = 4
    TDD_ADSY2301_EN = 5
    TDD_CHANNEL6     = 6  # PA_ON_0, PA_ON_1
    TDD_CHANNEL7     = 7  # TR Pulse

    # Configure TDD engine (disable during changes)
    tddn.enable = 0
    tddn.frame_length_ms = frame_length_ms  # frame_length_ms = PRI_ms

    # --- Group 1: Always-on channels ---
    for chan in [TDD_ENABLE,TDD_ADRV9009_TX_EN,TDD_ADRV9009_RX_EN, TDD_CHANNEL6]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = 0
        tddn.channel[chan].polarity = 1
        tddn.channel[chan].enable   = 1

    # --- Group 1b: ADSY2301 phased-array enable (always on) ---
    for chan in [TDD_ADSY2301_EN]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = 0
        tddn.channel[chan].polarity = 1
        tddn.channel[chan].enable   = 1

    # --- Group 2: TX/RX offload sync (raw sample counts) ---
    for chan in [TDD_TX_OFFLOAD_SYNC,TDD_RX_OFFLOAD_SYNC]:
        tddn.channel[chan].on_raw   = 0
        tddn.channel[chan].off_raw  = 10 
        tddn.channel[chan].polarity = 0
        tddn.channel[chan].enable   = 1

    # --- Group 3: TR pulse ---
    for chan in [TDD_CHANNEL7]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = 0.005  # 5 us TR pulse (5% duty cycle at 100 us PRI)
        tddn.channel[chan].polarity = 0      # polarity inverted
        tddn.channel[chan].enable   = 1

    # --- Enable TDD engine and trigger sync ---
    tddn.enable = 1
    tddn.sync_soft  = 1

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


    ##############################################
    ## Step 3: Send TX Data
    ##############################################

    sdr.tx_destroy_buffer()

    # Send the same waveform on all 4 TX channels
    sdr.tx([pulse0_iq, pulse0_iq, pulse0_iq, pulse0_iq])
    sdr.tx_cyclic_buffer

    # Trigger TDD synchronization
    tddn.sync_soft  = 1
