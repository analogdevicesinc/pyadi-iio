## Manta Ray Tx Pulsed Cal Method ##

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

rm = pyvisa.ResourceManager()


##############################################
## Step 0: Initialize Power Supplies ##
###############################################
E36 = "TCPIP::192.168.1.35::inst0::INSTR"
PA_Supplies = E36233A.E36233A(rm, E36)
PA_Supplies.output_off(1)
PA_Supplies.output_off(2)


#18 Volt Rail
PA_Supplies.set_voltage(1,18)
PA_Supplies.set_current(1,3)

#1.8 Volt TR Toggle
PA_Supplies.set_voltage(2,1.8)
PA_Supplies.set_current(2,0.5)


N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B.N6705B(rm, N67)
Pwr_Supplies.output_off(2)
Pwr_Supplies.output_off(3)
Pwr_Supplies.output_off(4)

# 4 Volt Rail
Pwr_Supplies.set_voltage(4,4)
Pwr_Supplies.set_current(4,10)

# -6 Volt Rail
Pwr_Supplies.set_voltage(2,-6)
Pwr_Supplies.set_current(2,3)

#5.7 Volt Rail
Pwr_Supplies.set_voltage(3,5.7)
Pwr_Supplies.set_current(3,10)


##############################################
## Step 1: Configure Manta Ray for Tx ##
###############################################

print("Set PA_ON to 0")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")




#######################################################
########################################################

print("Turning on 4V, then -6V supplies")
Pwr_Supplies.output_on(4)
time.sleep(1)
print(f"4V Rail is {Pwr_Supplies.measure_voltage(4)}V and {Pwr_Supplies.measure_current(4)}A")

Pwr_Supplies.output_on(2)
time.sleep(1)
print(f"-6V Rail is {Pwr_Supplies.measure_voltage(2)}V and {Pwr_Supplies.measure_current(2)}A")

input("Press Enter to continue...")
talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

print("Connecting to BFC Tile")

subarray = np.array([
    [1, 2, 3, 4, 9, 10, 11, 12, 17, 18, 19, 20, 25, 26, 27, 28], # subarray 1
    [5, 6, 7, 8, 13, 14, 15, 16, 21, 22, 23, 24, 29, 30, 31, 32], # subarray 2
    [37, 38, 39, 40, 45, 46, 47, 48, 53, 54, 55, 56, 61, 62, 63, 64],  # subarray 3
    [33, 34, 35, 36, 41, 42, 43, 44, 49, 50, 51, 52, 57, 58, 59, 60], # subarray 4
    ])




dev = adi.adar1000_array(
    uri = talise_uri,
    
    chip_ids = ["adar1000_csb_0_1_2", "adar1000_csb_0_1_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_1",
                "adar1000_csb_0_1_3", "adar1000_csb_0_1_4", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",

                "adar1000_csb_1_1_2", "adar1000_csb_1_1_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_1",
                "adar1000_csb_1_1_3", "adar1000_csb_1_1_4", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"],

    
    device_map = [[1, 5, 2, 6], [3, 7, 4, 8], [9, 13, 10, 14], [11, 15, 12, 16]],
 
    element_map = np.array([[1, 9,  17, 25, 33, 41, 49, 57],
                            [2, 10, 18, 26, 34, 42, 50, 58],
                            [3, 11, 19, 27, 35, 43, 51, 59],
                            [4, 12, 20, 28, 36, 44, 52, 60],
                            
                            [5, 13, 21, 29, 37, 45, 53, 61],
                            [6, 14, 22, 30, 38, 46, 54, 62],
                            [7, 15, 23, 31, 39, 47, 55, 63],
                            [8, 16, 24, 32, 40, 48, 56, 64]]),
    
    device_element_map = {
 
        1:  [9, 10, 2, 1],      3:  [41, 42, 34, 33],
        2:  [25, 26, 18, 17],   4:  [57, 58, 50, 49],
        5:  [4, 3, 11, 12]  ,   7:  [36, 35, 43, 44],
        6:  [20, 19, 27, 28],   8:  [52, 51, 59, 60],
 
        9:  [13, 14, 6, 5],     11: [45, 46, 38, 37],
        10: [29, 30, 22, 21],   12: [61, 62, 54, 53],
        13: [8, 7, 15, 16],     15: [40, 39, 47, 48],
        14: [24, 23, 31, 32],   16: [56, 55, 63, 64],
    },
)
    
print("Connected to BFC Tile")
for device in dev.devices.values():
    device.tr_source = "spi"
    device.mode = "rx"
    device.bias_dac_mode = "on"


tries = 10

for device in dev.devices.values():
    device.mode = "rx"
    device.bias_dac_mode = "on"


    for channel in device.channels:
        channel.pa_bias_on = -4.8
        if round(channel.pa_bias_on,1) != -4.8:
            found = False
            for _ in range(tries):
                if round(channel.pa_bias_on,1) != -4.8:
                    pass
                else:
                    found = True
                    break
            if not found:
                print(f"Not set properly: {channel.pa_bias_on=}")
                print(f"Element number {channel}")
        
        channel.pa_bias_off = -4.8
        if round(channel.pa_bias_off,1) != -4.8:
            found = False
            for _ in range(tries):
                if round(channel.pa_bias_off,1) != -4.8:
                    pass
                else:
                    found = True
                    break
            if not found:
                print(f"Not set properly: {channel.pa_bias_off=}")
                print(f"Element number {channel}")
        dev.latch_tx_settings()


print("Initialized BFC Tile")
dev.latch_tx_settings()
dev.latch_rx_settings()


print("Turning on 5.7V, current should be ~365mA")
Pwr_Supplies.output_on(3)
time.sleep(1)
print(f"5.7V Rail is {Pwr_Supplies.measure_voltage(3)}V and {Pwr_Supplies.measure_current(3)}A")
input("Press Enter to continue...")

print("Turning on 18V, current should be ~4mA")
PA_Supplies.output_on(1)
PA_Supplies.output_on(2)
time.sleep(2)
print(f"18V Rail is {PA_Supplies.measure_voltage(1)}V and {PA_Supplies.measure_current(1)}A")
input("Press Enter to continue...")

## Set elements to turn on for Tx ##
subarray_ref = np.array([1, 5, 37, 33])


for i in range(2):
    ##############################################
    ## Step 2: Configure Talise DACs ##
    ###############################################


    talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
    talise_uri = "ip:" + talise_ip
    # Create radio
    sdr  = adi.adrv9009_zu11eg(talise_uri)
    tddn = adi.tddn(talise_uri)

    #Configure Manta Ray control for PA Bias ON/OFF Toggle
    ctx = sdr._ctrl.ctx
    manta_bus0_ctrl = ctx.find_device("stingray0_control")
    manta_bus1_ctrl = ctx.find_device("stingray1_control")

    PA_Bias_0_toggle = manta_bus0_ctrl.find_channel("voltage0", True)
    PA_Bias_1_toggle = manta_bus1_ctrl.find_channel("voltage0", True)

    print("Setting PA_ON to 0")
    PA_Bias_0_toggle.attrs["raw"].value = "0"
    PA_Bias_1_toggle.attrs["raw"].value = "0"

    # USER CONFIGURABLE PARAMETERS
    # Configure TX properties
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
    frame_length_ms = 0.1 # 100 us
    # sine data for 10 us pulse than 90 us of zero data
    tx_pulse_start_ms = 0.00001 # 10 ns
    tx_pulse_stop_ms = 0.100 # 100 us
    # END USER CONFIGURABLE PARAMETERS

    # Pulse parameters #
    # 4 pulses for 4 Tx channels, pulse on chan0, pulse1 on chan1, pulse 2 on cham2, pulse3 on chan3
    PRI_ms = 0.1 #100 us pulse repitition interval
    duty_cycle = 0.1 # 10% duty cycle
    pulse_spacing_ms = 0.002 # 2 us spacing between pulse start times
    pulse_start_buffer_ms = 0.00001 # 10 ns
    pulse_start_ms = pulse_start_buffer_ms
    pulse_stop_ms = duty_cycle * PRI_ms + pulse_start_buffer_ms


    # Prepare TX data
    fs = int(sdr.tx_sample_rate)
    frame_length_seconds = PRI_ms * 1e-3
    # carrier frequency for the I/Q signal = 20 kHz
    fc_0 = 1000e3
    fc_1 = 1000e3
    fc_2 = 1000e3
    fc_3 = 1000e3
    # calculate N for full frame duration: N = fs * frame_length_seconds
    N = int(fs * frame_length_seconds)
    ts = 1 / float(fs)
    frame_length_ms = PRI_ms

    # Calculate samples for TX pulse duration
    pulse_duration_ms = pulse_stop_ms - pulse_start_ms
    pulse_duration_seconds = pulse_duration_ms * 1e-3
    pulse_samples = int(fs * pulse_duration_seconds)
    pulse_start_sample = int(fs * pulse_start_ms * 1e-3)


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


    # Generate pulses for each channel, with 1 MHz offset per channel
    for n in range(pulse_start_sample, min(pulse_start_sample + pulse_samples, N)):
        t_sample = n * ts
        pulse0_i[n] = np.cos(2 * np.pi * fc_0 * t_sample) * 1
        pulse0_q[n] = np.sin(2 * np.pi * fc_0 * t_sample) * 1
    for n in range(pulse_start_sample, min(pulse_start_sample + pulse_samples, N)):
        t_sample = n * ts
        pulse1_i[n] = np.cos(2 * np.pi * fc_1 * t_sample) * 1
        pulse1_q[n] = np.sin(2 * np.pi * fc_1 * t_sample) * 1
    for n in range(pulse_start_sample, min(pulse_start_sample + pulse_samples, N)):
        t_sample = n * ts
        pulse2_i[n] = np.cos(2 * np.pi * fc_2 * t_sample) * 1
        pulse2_q[n] = np.sin(2 * np.pi * fc_2 * t_sample) * 1
    for n in range(pulse_start_sample, min(pulse_start_sample + pulse_samples, N)):
        t_sample = n * ts
        pulse3_i[n] = np.cos(2 * np.pi * fc_3 * t_sample) * 1
        pulse3_q[n] = np.sin(2 * np.pi * fc_3 * t_sample) * 1


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


    ##############################################
    ## Step 3: Send Tx Data ##
    ###############################################

    sdr.tx_destroy_buffer()
    # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
    sdr.tx([pulse0_iq, pulse1_iq, pulse2_iq, pulse3_iq])

    # Trigger TDD synchronization
    tddn.sync_soft  = 1

print("Setting PA_ON to 1")
PA_Bias_0_toggle.attrs["raw"].value = "1"
PA_Bias_1_toggle.attrs["raw"].value = "1"





##############################################
## Step 4: Receive data from Spectrum Analyzer and Calibrate ##
###############################################


CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
# PSG = "TCPIP0::192.168.20.25::inst0::INSTR"

SpecAn = N9000A.N9000A(rm, CXA)
# SigGen = E8267D.E8267D(rm, PSG)

######## DEFINE MATLAB PULSESEP and PULSEPERIOD FUNCTIONS ##########

def pulsesep(signal):
    edges = np.where(np.diff(signal.astype(int)) == 1)[0] + 1
    if len(edges) < 2:
        separation = np.array([])
        nextCross = np.array([])
    else:
        separation = np.diff(edges)
        nextCross = edges[1:]
    initialCross = edges[:-1] if len(edges) > 1 else edges
    finalCross = edges[1:] if len(edges) > 1 else edges
    midLev = 0.5
    return separation, initialCross, finalCross, nextCross, midLev

def pulseperiod(signal):
    #Functionally the same as pulse separation for our purposes - if the signal is no longer periodic, will need to add code here to change
    return(pulsesep(signal))

######## END DEFINE MATLAB PULSESEP and PULSEPERIOD FUNCTIONS ##########

SpecAn.reset()   
SpecAn_Center_Freq = 9.9945e9   #Set to transmit frequency
SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
# SpecAn_Res_BW = 10e3
SpecAn_Res_BW = 1e6    #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
MinCodeVal = 0.015   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
NumChannels = 4   #Set to number of channels being used #Reset instrument
SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency

## Take Data from Spec An ##

#Iterate 16 Times to get all TX Amplitude Data
detect = []


for device in dev.devices.values():
    device.tr_source = "external"
    device.bias_dac_mode = "toggle"

# print("Setting PA_ON to 0")
# PA_Bias_0_toggle.attrs["raw"].value = "0"
# PA_Bias_1_toggle.attrs["raw"].value = "0"
# mr.disable_pa_bias_channel(dev)

PA_Bias_0_toggle.attrs["raw"].value = "1"
PA_Bias_1_toggle.attrs["raw"].value = "1"


SpecAn.set_to_spec_an_mode()
## Set span to 10 MHz for spectrum analyzer mode ##
SpecAn.write("SENS:FREQ:SPAN 5E6")
# SpecAn.set_resolution_bandwidth(9e-3)
SpecAn.set_resolution_bandwidth(8)
SpecAn.set_continuous_peak_search(1,1)
wait = 2
mr.disable_pa_bias_channel(dev,subarray)
for i in range(16):

    #Enable 4 elements at a time, column wise
    # mr.enable_pa_bias_channel(dev,subarray[:,i])

    print(f"Capturing Elements: {subarray[:,i]}")

    mr.enable_pa_bias_channel(dev,subarray[0,i])

    ## Set center freq to 9.994 GHz ##
    SpecAn.set_center_freq(9.994e9)
    time.sleep(wait)
    tone_0 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_0)
    print(f"Element: {subarray[0,i]}")
    print(tone_0)
    mr.disable_pa_bias_channel(dev,subarray[0,i])

    mr.enable_pa_bias_channel(dev,subarray[1,i])
    time.sleep(wait)
    ## Set center freq to 9.979 GHz ##
    # SpecAn.set_center_freq(9.979e9)
    time.sleep(wait)
    tone_1 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_1)
    print(f"Element: {subarray[1,i]}")
    print(tone_1)
    mr.disable_pa_bias_channel(dev,subarray[1,i])

    mr.enable_pa_bias_channel(dev,subarray[2,i])
    time.sleep(wait)
    ## Set center freq to 9.984 GHz ##
    # SpecAn.set_center_freq(9.984e9)
    time.sleep(wait)
    tone_2 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_2)
    print(f"Element: {subarray[2,i]}")
    print(tone_2)
    mr.disable_pa_bias_channel(dev,subarray[2,i])

    mr.enable_pa_bias_channel(dev,subarray[3,i])
    time.sleep(wait)
    ## Set center freq to 9.989 GHz ##
    # SpecAn.set_center_freq(9.989e9)
    time.sleep(wait)
    tone_3 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_3)
    print(f"Element: {subarray[3,i]}")
    print(tone_3)
    mr.disable_pa_bias_channel(dev,subarray[3,i])

print("Setting PA_ON to 0")
PA_Bias_0_toggle.attrs["raw"].value = "0"
PA_Bias_1_toggle.attrs["raw"].value = "0"

#Calculate Statistics:
pre_detect_arr = np.array(detect, dtype=float)
pre_detect_mean = float(pre_detect_arr.mean())
pre_detect_min = float(pre_detect_arr.min())
pre_detect_max = float(pre_detect_arr.max())
pre_detect_var = float(pre_detect_arr.var())  # population variance; use ddof=1 for sample variance


gain_codes_cal, atten_cal = mr.gain_codes(dev,np.array(detect),mode="tx")
print(gain_codes_cal)

gain_dict_ref = subarray.transpose().flatten()
gain_dict = mr.create_dict(gain_dict_ref, gain_codes_cal)
print("gain_dict:", gain_dict)

atten_dict_ref = subarray.transpose().flatten()
atten_dict = mr.create_dict(atten_dict_ref, atten_cal)


for element in dev.elements.values():
    """
    Iterate through each element in the Stingray object
    Convert the element to a string and extract the last two digits
    This is used to map the element to its corresponding gain and attenuation values
    in the dictionaries created above
    """
    str_channel = str(element)
    print(element)
    value = int(mr.strip_to_last_two_digits(str_channel))

    # element.tx_attenuator = atten_dict[value]
    element.tx_attenuator = 1
    element.tx_gain = gain_dict[value]

    dev.latch_tx_settings() # Latch SPI settings to devices




#Iterate 16 Times to get all TX Amplitude Data
detect = []

print("Setting PA_ON to 1")
PA_Bias_0_toggle.attrs["raw"].value = "1"
PA_Bias_1_toggle.attrs["raw"].value = "1"

for i in range(16):

    #Enable 4 elements at a time, column wise
    # mr.enable_pa_bias_channel(dev,subarray[:,i])

    print(f"Capturing Elements: {subarray[:,i]}")

    mr.enable_pa_bias_channel(dev,subarray[0,i])

    ## Set center freq to 9.994 GHz ##
    SpecAn.set_center_freq(9.994e9)
    time.sleep(wait)
    tone_0 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_0)
    print(f"Element: {subarray[0,i]}")
    print(tone_0)
    mr.disable_pa_bias_channel(dev,subarray[0,i])

    mr.enable_pa_bias_channel(dev,subarray[1,i])
    time.sleep(wait)
    ## Set center freq to 9.979 GHz ##
    # SpecAn.set_center_freq(9.979e9)
    time.sleep(wait)
    tone_1 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_1)
    print(f"Element: {subarray[1,i]}")
    print(tone_1)
    mr.disable_pa_bias_channel(dev,subarray[1,i])

    mr.enable_pa_bias_channel(dev,subarray[2,i])
    time.sleep(wait)
    ## Set center freq to 9.984 GHz ##
    # SpecAn.set_center_freq(9.984e9)
    time.sleep(wait)
    tone_2 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_2)
    print(f"Element: {subarray[2,i]}")
    print(tone_2)
    mr.disable_pa_bias_channel(dev,subarray[2,i])

    mr.enable_pa_bias_channel(dev,subarray[3,i])
    time.sleep(wait)
    ## Set center freq to 9.989 GHz ##
    # SpecAn.set_center_freq(9.989e9)
    time.sleep(wait)
    tone_3 = SpecAn.get_marker_power(marker=1)
    detect.append(tone_3)
    print(f"Element: {subarray[3,i]}")
    print(tone_3)
    mr.disable_pa_bias_channel(dev,subarray[3,i])

print("Setting PA_ON to 0")
PA_Bias_0_toggle.attrs["raw"].value = "0"
PA_Bias_1_toggle.attrs["raw"].value = "0"

#Calculate Statistics:
post_detect_arr = np.array(detect, dtype=float)
post_detect_mean = float(post_detect_arr.mean())
post_detect_min = float(post_detect_arr.min())
post_detect_max = float(post_detect_arr.max())
post_detect_var = float(post_detect_arr.var())  # population variance; use ddof=1 for sample variance


print("Pre Gain Calibration Detection summary")
print(f"  mean: {pre_detect_mean:.6f}")
print(f"  min : {pre_detect_min:.6f}")
print(f"  max : {pre_detect_max:.6f}")
print(f"  var : {pre_detect_var:.6e}")

print("Post Gain Calibration Detection summary")
print(f"  mean: {post_detect_mean:.6f}")
print(f"  min : {post_detect_min:.6f}")
print(f"  max : {post_detect_max:.6f}")
print(f"  var : {post_detect_var:.6e}")





