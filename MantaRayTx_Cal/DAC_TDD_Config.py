import adi
import pyvisa
from pyvisa import constants
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import N9000A_Driver as N9000A
import E8267D_Driver as E8267D
import N6705B_Driver as N6705B
import E36233A_Driver as E36233A
import paramiko
import MantaRay as mr
import math
import sys
import mbx_functions as mbx
import subprocess
import os
import sys


talise_uri = "ip:192.168.1.1"

## Pulse Parameters ##
PRI_ms = 0.1 # in milliseconds
duty_cycle = 1.0 # duty cycle for DAC pulsesin percentage (0 to 1.0)

## Initialize Talise SOM DACs ##
for i in range(2):
    # Create radio and initialize TDD engine
    sdr  = adi.adrv9009_zu11eg(talise_uri)
    ctx = sdr._ctrl.ctx
    tddn = adi.tddn(talise_uri)

    # Setup ADXUD1AEBZ
    xud = ctx.find_device("xud_control")

    # Find channel attribute for TX & RX
    # txrx1 = xud.find_channel("voltage1", True)
    # txrx2 = xud.find_channel("voltage2", True)
    # txrx3 = xud.find_channel("voltage3", True)
    # txrx4 = xud.find_channel("voltage4", True)

    ## Updated XUD settings, PLLselect and RxGainMode ##
    PLLselect = xud.find_channel("voltage1", True)
    rxgainmode = xud.find_channel("voltage0", True)

    
    # 0 for rx, 1 for tx
    # txrx1.attrs["raw"].value = "1" # Subarray 4
    # txrx2.attrs["raw"].value = "1" # Subarray 3
    # txrx3.attrs["raw"].value = "1" # Subarray 1
    # txrx4.attrs["raw"].value = "1" # Subarray 2
    PLLselect.attrs["raw"].value = "1"
    rxgainmode.attrs["raw"].value = "0"


    # Configure TX/RX properties
    sdr.tx_enabled_channels = [0, 1, 2, 3]
    ## TRx LO is preset to 4.5 GHz
    # sdr.trx_lo = 4500000000
    # sdr.trx_lo_chip_b = 4500000000
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
    # frame_length_ms = 0.1 # 100 us
    frame_length_ms = 0.1 # 1 ms
    # sine data for 10 us pulse than 90 us of zero data
    tx_pulse_start_ms = 0.00001 # 10 ns
    tx_pulse_stop_ms = 0.100 # 100 us


    # Pulse parameters #
    # PRI_ms = 0.1 #100 us pulse repitition interval
    PRI_ms = 0.100 # 0.1 ms pulse repitition interval
    # duty_cycle = 0.025 # 2.5% duty cycle
    duty_cycle = 1 # 100% duty cycle to send CW wave
    pulse_spacing_ms = 0.002 # 2 us spacing between pulse start times
    pulse_start_buffer_ms = 0.00001 # 10 ns
    pulse0_start_ms = pulse_start_buffer_ms
    pulse0_stop_ms = duty_cycle * PRI_ms + pulse_start_buffer_ms
    pulse1_start_ms = pulse0_stop_ms + pulse_spacing_ms
    pulse1_stop_ms = pulse1_start_ms + duty_cycle * PRI_ms
    pulse2_start_ms = pulse1_stop_ms + pulse_spacing_ms
    pulse2_stop_ms = pulse2_start_ms + duty_cycle * PRI_ms
    pulse3_start_ms = pulse2_stop_ms + pulse_spacing_ms
    pulse3_stop_ms = pulse3_start_ms + duty_cycle * PRI_ms

    # Prepare TX data
    fs = int(sdr.tx_sample_rate)
    frame_length_seconds = PRI_ms * 1e-3
    # carrier frequency for the I/Q signal = 20 kHz
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
    # # Configure TX data offload mode to cyclic
    # sdr._txdac.debug_attrs["pl_ddr_fifo_enable"].value = "1"
    # sdr.tx_cyclic_buffer = True


    #####################
    # TDD signal channels
    #####################

    TDD_TX_OFFLOAD_SYNC = 0
    TDD_RX_OFFLOAD_SYNC = 1
    TDD_ENABLE      = 2
    TDD_ADRV9009_RX_EN = 3
    TDD_ADRV9009_TX_EN = 4
    TDD_MANTARAY_EN = 5
    TDD_CHANNEL6     = 6  ## PA_ON_0, PA_ON_1
    TDD_CHANNEL7     = 7  ## TR Pulse

    #Configure TDD engine
    tddn.enable = 0  ## Set to 0 to make config changes
    # tddn.burst_count          = 0 # continuous mode, period repetead forever
    # tddn.startup_delay_ms     = 0
    tddn.frame_length_ms      = frame_length_ms  ## frame_length_ms = PRI_ms

    ## 3 Separate groups of TDD channels.

    ## Always on channels
    for chan in [TDD_ENABLE,TDD_ADRV9009_TX_EN,TDD_ADRV9009_RX_EN,TDD_MANTARAY_EN, TDD_CHANNEL6]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = 0
        tddn.channel[chan].polarity = 1
        tddn.channel[chan].enable   = 1

    ## Previously set by software team, untouched
    for chan in [TDD_TX_OFFLOAD_SYNC,TDD_RX_OFFLOAD_SYNC]:
        tddn.channel[chan].on_raw   = 0
        tddn.channel[chan].off_raw  = 10 # 10 samples at 250 MHz = 40 ns pulse width
        tddn.channel[chan].polarity = 0
        tddn.channel[chan].enable   = 1

    ## TR pulse channel
    for chan in [TDD_CHANNEL7]:
        tddn.channel[chan].on_ms   = 0
        tddn.channel[chan].off_ms  = 0.005 ## For 100 us PRI, 5 us TR pulse for 5% duty cycle
        tddn.channel[chan].polarity = 0 # polarity inverted
        tddn.channel[chan].enable   = 1


    ## Enable TDD engine after config chages
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
    ## Step 3: Send Tx Data ##
    ###############################################

    ## Destroy buffer before sending new data ##
    sdr.tx_destroy_buffer()


    # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
    # sdr.tx([pulse0_iq, pulse1_iq, pulse2_iq, pulse3_iq]) ## Use to send time interleaved pulses on each channel
    sdr.tx([pulse0_iq, pulse0_iq, pulse0_iq, pulse0_iq]) ## Use to send same data on all channels
    # sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*322*np.pi/180), pulse0_iq*np.exp(1j*209*np.pi/180), pulse0_iq*np.exp(1j*182*np.pi/180)])
    sdr.tx_cyclic_buffer


    # Trigger TDD synchronization
    tddn.sync_soft  = 1
