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
import mbx_functions as mbx
import subprocess
import os
import sys

talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

## Set up VISA for external instruments ##
rm = pyvisa.ResourceManager()

## Initialize settings to connect to mechanical gimbal ##
BAUDRATE                    = 57600    
DEVICENAME                  = "/dev/ttyUSB0" 

## Set Gimbal to go to boresight position ##
mbx.connect(DEVICENAME, BAUDRATE)
mbx.gotoZERO()

## Set whether or not to run bootstrap script
bootstrap_needed = False
config = True
DAC_config = False
Gain_calibration = True
Digi_Phase_calibration = False
Analog_Phase_calibration = True
operational_frequency = 9e9

##############################################
## Step 0: Initialize Power Supplies ##
###############################################

## Keysight E36233A Power Supply for Drain Voltage)
E36 = "TCPIP::192.168.1.35::inst0::INSTR"
PA_Supplies = E36233A.E36233A(rm, E36)
PA_Supplies.output_off(1)
PA_Supplies.output_off(2)

## Keysight N6705B Power Supply (modular) for Manta Ray Rails ##
N67 = "TCPIP::192.168.1.25::INSTR"
Pwr_Supplies = N6705B.N6705B(rm, N67)


#18 Volt Rail (Drain Voltage, Vdd)
PA_Supplies.set_voltage(1,18)  ## 18V Vdd
PA_Supplies.set_current(1,2)  ## 30A current limit

if bootstrap_needed == True:

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


    ## Setup SSH conection into Talise SOM for control ##
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")

    ## Turn on Manta Ray Power Supplies ##
    print("Turning on 4V, then -6V supplies")
    Pwr_Supplies.output_on(4)
    time.sleep(1)
    print(f"4V Rail is {Pwr_Supplies.measure_voltage(4)}V and {Pwr_Supplies.measure_current(4)}A")
    Pwr_Supplies.output_on(2)
    time.sleep(1)
    print(f"-6V Rail is {Pwr_Supplies.measure_voltage(2)}V and {Pwr_Supplies.measure_current(2)}A")


    talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
    talise_uri = "ip:" + talise_ip

    #######################################################
    # Run the bootstrap script and block until it completes
    ########################################################

    boot_cmd = "bash manta_ray_adar1000_boot.bash"
    stdin, stdout, stderr = ssh.exec_command(boot_cmd,get_pty=True)
    chan = stdout.channel

    # stream output while the command runs
    while not chan.exit_status_ready():
        if chan.recv_ready():
            out_chunk = chan.recv(1024).decode(errors="ignore")
            print(out_chunk, end="")
        if chan.recv_stderr_ready():
            err_chunk = chan.recv_stderr(1024).decode(errors="ignore")
            print(err_chunk, end="", file=sys.stderr)
        time.sleep(0.1)

    # flush any remaining output
    if chan.recv_ready():
        print(chan.recv(1024).decode(errors="ignore"), end="")
    if chan.recv_stderr_ready():
        print(chan.recv_stderr(1024).decode(errors="ignore"), end="", file=sys.stderr)

    exit_status = chan.recv_exit_status()
    if exit_status != 0:
        ssh.close()
        raise RuntimeError(f"Boot script failed (exit {exit_status})")
    else:
        print(f"Boot script completed (exit {exit_status})")
    ssh.close()


#########################################
## Setup array mapping of ADAR1000s and elements ##
##########################################

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

if config == True:
    ## Set attenuation to 1, gain to max, and phase to 0 for all elements ##
    
    
    ## Set TR Source, Mode, and Bias DAC Mode ##
    ## toggle with respect to T/R state.
    for device in dev.devices.values():
        device.tr_source = "spi"
    for device in dev.devices.values():    
        # device.mode = "rx"
        device.bias_dac_mode = "on"
    
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
        time.sleep(0.1)
        element.tx_gain = 127
        element.tx_phase = 0

        dev.latch_tx_settings() # Latch SPI settings to devices


    ## Set PA Bias ON/OFF to -4.8V for all channels ##
    tries = 10
    for device in dev.devices.values():
        # device.mode = "rx"
        # device.bias_dac_mode = "on"

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


dev.latch_tx_settings()
dev.latch_rx_settings()
print("Initialized BFC Tile")

print("Turning on 5.7V, current should be ~365mA")
Pwr_Supplies.output_on(3)
time.sleep(1)
print(f"5.7V Rail is {Pwr_Supplies.measure_voltage(3)}V and {Pwr_Supplies.measure_current(3)}A")


print("Turning on 18V, current should be ~4mA")
PA_Supplies.output_on(1)
PA_Supplies.output_on(2)
time.sleep(2)
print(f"18V Rail is {PA_Supplies.measure_voltage(1)}V and {PA_Supplies.measure_current(1)}A")


## Set elements to turn on for Tx ##
subarray_ref = np.array([1, 5, 37, 33])


#########################################################
#########################################################
############## Amplitude Cal ############################
#########################################################
#########################################################


##############################################
## Step 1: Configure Manta Ray for Tx ##
###############################################

## Set elements to turn on for Tx ##

subarray_ref = np.array([1, 5, 37, 33])

if DAC_config == True:
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
        sdr.tx_cyclic_buffer


        # Trigger TDD synchronization
        tddn.sync_soft  = 1


## Set TR Source to external and bias_dac_mode to toggle ##    
for device in dev.devices.values():
        device.tr_source = "external"
        device.bias_dac_mode = "toggle"

##############################################
## Step 4: Receive data from Spectrum Analyzer and Calibrate ##
###############################################

## Turn off 5.7V rail for heat management ##
print("Turning off 5.7V rail (LNA bias rail) for heat management")
Pwr_Supplies.output_off(3)

if Gain_calibration == True:
    print("Beginning Gain Calibration Routine")
    CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
    # PSG = "TCPIP0::192.168.20.25::inst0::INSTR"

    SpecAn = N9000A.N9000A(rm, CXA)
    # SigGen = E8267D.E8267D(rm, PSG)



    # SpecAn.reset()   
    SpecAn_Center_Freq = operational_frequency   #Set to transmit frequency
    SpecAn_Res_BW = 150    #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
    SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
    SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency
    # SpecAn.write("TRIGger:SEQ:RFB:LEV:ABS -60 dBm")
    #Iterate 16 Times to get all TX Amplitude Data
    detect = []

    ## Set TR Source to external and bias_dac_mode to toggle ##
    for device in dev.devices.values():
        device.tr_source = "external"
        device.bias_dac_mode = "toggle"


    ####################################
    ####################################
    ######## Begin Gain Cal ############   
    ####################################
    ####################################

    # Disable all channels before starting calibration
    mr.disable_pa_bias_channel(dev)

    # Set Spectrum Analyzer to Spec An mode 
    SpecAn.set_to_spec_an_mode()
    ## Set span to 5 MHz for spectrum analyzer mode ##
    SpecAn.write("SENS:FREQ:SPAN 18E3")
    # SpecAn.set_resolution_bandwidth(9e-3)
    SpecAn.set_resolution_bandwidth(150e-6)
    SpecAn.write("SENS:SWE:TIME 75E-3")
    SpecAn.set_continuous_peak_search(1,1)
    # # Configure spectrum analyzer video (RF envelope) trigger parameters
    # SpecAn.write("TRIGger:VIDeo:SOURce VIDeo")
    # SpecAn.write("TRIGger:VIDeo:LEVel -66.80 dBm")
    # SpecAn.write("TRIGger:VIDeo:SLOPe NEGative")
    # SpecAn.write("TRIGger:VIDeo:DELay -14.1E-6")
    # # enable the video trigger
    # SpecAn.write("TRIGger:VIDeo:STAT ON")


    wait = 0.5

    ## Disable all elemements
    mr.disable_pa_bias_channel(dev,)
    for i in range(16):

        print(f"Capturing Elements: {subarray[:,i]}")

        ## Set center freq to 9.994 GHz ##
        SpecAn.set_center_freq(operational_frequency)  
        # print(tone_0)


        mr.enable_pa_bias_channel(dev,subarray[0,i])
        time.sleep(wait)
        tone_0 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_0)
        print(f"Element: {subarray[0,i]}")
        print(tone_0)
        mr.disable_pa_bias_channel(dev,subarray[0,i])

        mr.enable_pa_bias_channel(dev,subarray[1,i])
        time.sleep(wait)
        tone_1 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_1)
        print(f"Element: {subarray[1,i]}")
        print(tone_1)
        mr.disable_pa_bias_channel(dev,subarray[1,i])

        mr.enable_pa_bias_channel(dev,subarray[2,i])
        time.sleep(wait)
        tone_2 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_2)
        print(f"Element: {subarray[2,i]}")
        print(tone_2)
        mr.disable_pa_bias_channel(dev,subarray[2,i])

        mr.enable_pa_bias_channel(dev,subarray[3,i])
        time.sleep(wait)
        tone_3 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_3)
        print(f"Element: {subarray[3,i]}")
        print(tone_3)
        mr.disable_pa_bias_channel(dev,subarray[3,i])


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



    ## Create array to hold amplitude data ##
    #Iterate 16 Times to get all TX Amplitude Data
    detect = []


    for i in range(16):

        

        print(f"Capturing Elements: {subarray[:,i]}")

        mr.enable_pa_bias_channel(dev,subarray[0,i])

        ## Set center freq to 9.994 GHz ##
        SpecAn.set_center_freq(operational_frequency)
        time.sleep(wait)
        tone_0 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_0)
        print(f"Element: {subarray[0,i]}")
        print(tone_0)
        mr.disable_pa_bias_channel(dev,subarray[0,i])

        mr.enable_pa_bias_channel(dev,subarray[1,i])
        time.sleep(wait)
        tone_1 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_1)
        print(f"Element: {subarray[1,i]}")
        print(tone_1)
        mr.disable_pa_bias_channel(dev,subarray[1,i])

        mr.enable_pa_bias_channel(dev,subarray[2,i])
        time.sleep(wait)
        tone_2 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_2)
        print(f"Element: {subarray[2,i]}")
        print(tone_2)
        mr.disable_pa_bias_channel(dev,subarray[2,i])

        mr.enable_pa_bias_channel(dev,subarray[3,i])
        time.sleep(wait)
        tone_3 = SpecAn.get_marker_power(marker=1)
        detect.append(tone_3)
        print(f"Element: {subarray[3,i]}")
        print(tone_3)
        mr.disable_pa_bias_channel(dev,subarray[3,i])


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


if Digi_Phase_calibration == True:
    print("Beginning Digital Phase Calibration Routine")
    #########################################################################
    #########################################################################
    ########################## Digital Phase Cal ############################
    #########################################################################
    #########################################################################


    # ### Set DACs to output interleaved pulses on each channel ##

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
        duty_cycle = 0.05 # 2.5% duty cycle
        # duty_cycle = 1 # 100% duty cycle to send CW wave
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
            tddn.channel[chan].off_ms  = 0.040 ## For 100 us PRI, 5 us TR pulse for 5% duty cycle
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
        sdr.tx([pulse0_iq, pulse1_iq, pulse2_iq, pulse3_iq]) ## Use to send time interleaved pulses on each channel
        # sdr.tx([pulse0_iq, pulse0_iq, pulse0_iq, pulse0_iq]) ## Use to send same data on all channels
        sdr.tx_cyclic_buffer


        # Trigger TDD synchronization
        tddn.sync_soft  = 1


    # ##############################################
    # ## Step 4: Receive data from Spectrum Analyzer and Calibrate ##
    # ###############################################


    CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
    # PSG = "TCPIP0::192.168.20.25::inst0::INSTR"

    SpecAn = N9000A.N9000A(rm, CXA)
    # SigGen = E8267D.E8267D(rm, PSG)

    time.sleep(1)

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

    SpecAn_Center_Freq = 9.9945e9   #Set to transmit frequency
    SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
    SpecAn_Res_BW = 10e3   #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
    SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
    MinCodeVal = 0.015   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
    NumChannels = 4   #Set to number of channels being used


    SpecAn.select_iq_mode()    #Set spec an for complex IQ mode
    # SpecAn.reset()   
    SpecAn_Center_Freq = 9.9945e9   #Set to transmit frequency
    SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
    SpecAn_Res_BW = 10e3   #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
    SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
    MinCodeVal = 0.004   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
    NumChannels = 4   #Set to number of channels being used          #Reset instrument
    SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
    SpecAn.set_iq_spec_span(SpecAn_IQ_BW)  #Set IQ bandwidth of instrument
    SpecAn.set_iq_spec_bandwidth(SpecAn_Res_BW)    #Set ResBW
    SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency
    SpecAn.set_iq_mode_bandwidth(SpecAn_Dig_IFBW)  #Set Digital IFBW
    # SpecAn.bursttrig('POS', -5, 0, -65)    #Set trigger parameters for Spec An. First input is slope, second is delay (uS), third is relative level, last is absolute level
    # SpecAn.trigger()
    SpecAn.wavexscale(0, 40000, 'LEFT', 'OFF')
    SpecAn.waveyscale(0, 80, 'CENT', 'OFF')

    mr.enable_pa_bias_channel(dev, subarray[:, 1])

    numRuns = 1
    PhaseAVG = 1
    phaseValsAll = np.zeros((NumChannels, PhaseAVG))
    for run in range(numRuns):



        ## Take Data from Spec An ##
        ComplexData = SpecAn.iq_complex_data()
        # SigGen.set_output_state('OFF')  #Turn off Sig Gen output

        # SpecAn.set_continuous_peak_search(1, 'ON')
        # peakPowerSingleElement = SpecAn.get_marker_power(marker=1)
        # print("Peak Power Single Element (dBm): ", peakPowerSingleElement)


        #Separate the I and Q components of the complex data
        I = np.real(ComplexData)
        Q = np.imag(ComplexData)

        # Plot the I and Q waveforms 
        # plt.figure()
        # plt.subplot(2, 1, 1)
        # plt.plot(np.abs(I))
        # plt.title('I Component')
        # plt.subplot(2, 1, 2)
        # plt.plot(np.abs(Q))
        # plt.title('Q Component')


        ########### Post Processign Section ############
        #Find peaks above threshold
        # RealPk, _ = find_peaks(np.abs(I), height = MinCodeVal)
        # ImagPk, _ = find_peaks(np.abs(Q), height = MinCodeVal)

        #Select I or Q component of complex data for calibration step
        # if(len(RealPk) >= len(ImagPk)):
        #     ProcessArray = I
        # else:
        #     ProcessArray = Q
        ComplexData = np.roll(ComplexData, -700, axis=0)        #Roll data to ensure reference pulse set is complete
        #Align Tx channels 
        #Find pulse corresponding to Tx0
        # if(abs(I[0]) > MinCodeVal or abs(Q[0]) > MinCodeVal or
        # abs(I[144]) > MinCodeVal or abs(Q[144]) > MinCodeVal):
        #     Separation, InitialCross, FinalCross, NextCross, Midlev = pulsesep(
        #         (np.abs(np.real(ComplexData)) > MinCodeVal).astype(float))
        #     maxloc = np.argmax(Separation)
        #     channel0Start = int(np.ceil(NextCross[maxloc]))
        # else:
        Period, InitialCross, FinalCross, NextCross, Midlev = pulseperiod(
            (np.abs(ComplexData) > MinCodeVal).astype(float))
        channel0Start = int(np.ceil(InitialCross[0]))

        timeZeroAlignedFirstRx = np.roll(ComplexData, -channel0Start)
        timeZeroAligned = np.roll(ComplexData, -channel0Start, axis=0)

        print(channel0Start)

        plt.figure()
        plt.plot(np.abs(timeZeroAligned))
        plt.title('Zero Aligned Samples')
        plt.show()



        # Now Determine the Phase Offsets for Each Tx Channel
        phaseVals = np.zeros((NumChannels, PhaseAVG))
        relativePhaseVals = np.zeros((NumChannels, PhaseAVG))
        

        for k in range(PhaseAVG):
            for i in range(NumChannels):
                phaseVals[i, k] = (np.angle(timeZeroAlignedFirstRx[62 + (i*149)]) * (180/np.pi))
                relativePhaseVals[i, k] = phaseVals[i, k] - phaseVals[0, k]
                # relativePhaseVals[i, k] = np.mod(relativePhaseVals[i, 0], 360)
                # if relativePhaseVals[i, k] > 360:
                #     relativePhaseVals[i, k] = relativePhaseVals[i, k] - 360
                #     relativePhaseVals[i, k] = relativePhaseVals[i, k] % 360
                # else:    
                relativePhaseVals[i, k] = relativePhaseVals[i, k] % 360
            ComplexData = np.roll(ComplexData, -600)        #Roll data to next pulse set for averaging
            Period, InitialCross, FinalCross, NextCross, Midlev = pulseperiod(
                (np.abs(ComplexData) > MinCodeVal).astype(float))
            channel0Start = int(np.ceil(InitialCross[0]))
            timeZeroAlignedFirstRx = np.roll(ComplexData, -channel0Start)
            timeZeroAligned = np.roll(ComplexData, -channel0Start, axis=0)
            phaseValsAll[i, k] = relativePhaseVals[i, k]
        
    # print(relativePhaseVals)

    print(relativePhaseVals)  

    # print('PhaseValsAll:\n', phaseValsAll)

    phaseValsAvg = np.mean(relativePhaseVals, axis=1)

    print('PhaseValsAvg:\n', phaseValsAvg)

    # sdr.tx_destroy_buffer()
    # # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
    # sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*phaseValsAvg[1]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[2]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[3]*np.pi/180)])


    # Send phase aligned pulses out of DAC
    sdr.tx_destroy_buffer()
    sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*phaseValsAvg[1]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[2]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[3]*np.pi/180)])

    dig_phase = [0, phaseValsAvg[1], phaseValsAvg[2], phaseValsAvg[3]]


if Analog_Phase_calibration == True:
    print("Beginning Analog Phase Calibration Routine")
    CXA = "TCPIP0::192.168.1.77::hislip0::INSTR"
    SpecAn = N9000A.N9000A(rm, CXA)
    # SpecAn.reset()  
    # SpecAn.set_to_spec_an_mode() 
    # SpecAn_Center_Freq = 10e9   #Set to transmit frequency
    # SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
    # # SpecAn_Res_BW = 10e3
    # SpecAn_Res_BW = 1e6    #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
    # SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
    # MinCodeVal = 0.015   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
    # NumChannels = 4   #Set to number of channels being used #Reset instrument
    # # SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
    # # SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency

    # # Set Spectrum Analyzer to Spec An mode 
    # SpecAn.set_to_spec_an_mode()
    # ## Set span to 5 MHz for spectrum analyzer mode ##
    # SpecAn.write("SENS:FREQ:SPAN 0E6")
    # # SpecAn.set_resolution_bandwidth(9e-3)
    # SpecAn.set_resolution_bandwidth(1)
    # SpecAn.write("SENS:SWE:TIME 20E-6")
    # SpecAn.set_continuous_peak_search(1,1)
    # # Configure spectrum analyzer video (RF envelope) trigger parameters
    # SpecAn.write("TRIGger:VIDeo:SOURce VIDeo")
    # SpecAn.write("TRIGger:VIDeo:LEVel -66.80 dBm")
    # SpecAn.write("TRIGger:VIDeo:SLOPe NEGative")
    # SpecAn.write("TRIGger:VIDeo:DELay -14.1E-6")
    # # enable the video trigger
    # SpecAn.write("TRIGger:VIDeo:STAT ON")
    # wait = 2

        # Set Spectrum Analyzer to Spec An mode 
    SpecAn.set_to_spec_an_mode()
    ## Set span to 5 MHz for spectrum analyzer mode ##
    SpecAn.write("SENS:FREQ:SPAN 18E3")
    # SpecAn.set_resolution_bandwidth(9e-3)
    SpecAn.set_resolution_bandwidth(150e-6)
    SpecAn.write("SENS:SWE:TIME 75E-3")
    SpecAn.set_continuous_peak_search(1,1)
    # # Configure spectrum analyzer video (RF envelope) trigger parameters
    # SpecAn.write("TRIGger:VIDeo:SOURce VIDeo")
    # SpecAn.write("TRIGger:VIDeo:LEVel -66.80 dBm")
    # SpecAn.write("TRIGger:VIDeo:SLOPe NEGative")
    # SpecAn.write("TRIGger:VIDeo:DELay -14.1E-6")
    # # enable the video trigger
    # SpecAn.write("TRIGger:VIDeo:STAT ON")


    ########################################################
    ################ Analog Phase Cal ######################
    ########################################################

    ## Set ADAR1000 phases to 0 degrees for all elements ##
    for element in dev.elements.values():
        str_channel = str(element)
        value = int(mr.strip_to_last_two_digits(str_channel))
        element.tx_phase = 0
        dev.latch_tx_settings()

    ## Change DACs back to CW tones ##
    ## Set TR Source to external and bias_dac_mode to toggle ##
    for device in dev.devices.values():
        device.tr_source = "external"
        device.bias_dac_mode = "toggle"

    mr.disable_pa_bias_channel(dev)


    ## NULL POWER PHASE CAL ##

    #Reference Channel
    ref_chan = subarray[0, 2]
    mr.enable_pa_bias_channel(dev, ref_chan)
    # dig_cal_channels = subarray[:, 2]
    matrix_64elem = np.arange(1,65)

    ## Enable channel one at a time.  Sweep phase 0-180 degrees and find null point.  ##
    ## Set calibrated phase to null point + 180 degrees ##
    digi_phase_values = []


    # Constants for the Coarse-Fine Search
COARSE_STEP = 15
FINE_RANGE = 15  # +/- 15 degrees from the coarse minimum

for element in dev.elements.values():
    str_channel = str(element)
    value = int(mr.strip_to_last_two_digits(str_channel))
    
    if value in matrix_64elem:
        
        if value == ref_chan:
            continue
        
        print(f"\n--- Element: {value} ---")
        
        # 1. SETUP
        # (Assuming SpecAn setup and trigger configuration is done outside this loop)
        mr.enable_pa_bias_channel(dev, value)
        mr.enable_pa_bias_channel(dev, ref_chan)

        
        # --- PHASE 1: COARSE SWEEP (0 to 180 degrees in COARSE_STEP increments) ---
        coarse_detect = {} # Dictionary to store {phase: power}
        
        print(f"Coarse Sweep (Step: {COARSE_STEP} deg)")
        for j in range(0, 196, COARSE_STEP):
            
            # Ensure phase wraps around 360, though your original script used 0-180
            # We'll stick to 0-180 for now as per your original script
            
            element.tx_phase = j
            dev.latch_tx_settings()
            
            # Measure Power
            tone_0 = SpecAn.get_marker_power(marker=1)
            # tone_0_freq = SpecAn.get_marker_freq(marker=1) # Unused, but kept for context
            
            coarse_detect[j] = tone_0
        
        # Find the phase with the minimum power from the coarse sweep
        # Use min() with a key to find the dictionary key (phase) with the minimum value (power)
        min_coarse_phase = min(coarse_detect, key=coarse_detect.get)
        min_coarse_power = coarse_detect[min_coarse_phase]
        
        print(f"Coarse min at {min_coarse_phase} deg with power {min_coarse_power:.2f} dBm")
        
        
        # --- PHASE 2: FINE SWEEP (+/- FINE_RANGE around the coarse minimum) ---
        fine_detect = {} # Dictionary to store {phase: power}
        
        # Define the fine sweep range, handling phase wrap (0-359 or 0-180 in your case)
        # Since your original code used 0 to 180, we will assume you expect the phase to stay in this range.
        # We will search from min_coarse_phase - FINE_RANGE to min_coarse_phase + FINE_RANGE
        start_fine = max(0, min_coarse_phase - FINE_RANGE)
        end_fine = min(196, min_coarse_phase + FINE_RANGE)
        
        print(f"Fine Sweep (Range: {start_fine} to {end_fine} deg)")

        # Sweep in 1 degree steps
        for j in range(start_fine, end_fine + 1):
            
            element.tx_phase = j
            dev.latch_tx_settings()
            
            # Measure Power
            tone_0 = SpecAn.get_marker_power(marker=1)
            fine_detect[j] = tone_0

        # Find the phase with the minimum power from the fine sweep
        min_fine_phase = min(fine_detect, key=fine_detect.get)
        min_fine_power = fine_detect[min_fine_phase]
        
        print(f'Fine min (final null) power at {min_fine_phase} deg')
        
        
        # --- PHASE 3: APPLY CALIBRATED PHASE ---
        
        # The null phase is 'min_fine_phase', so the in-phase setting is + 180 degrees
        calibrated_phase = (min_fine_phase + 180) % 360 # Use modulo for wrap around if required, or simply +180
        
        print(f'Setting {element} calibrated phase to {calibrated_phase} deg')
        
        element.tx_phase = calibrated_phase
        digi_phase_values.append(calibrated_phase)
        dev.latch_tx_settings()

        # 4. CLEANUP
        mr.disable_pa_bias_channel(dev, value)
        mr.disable_pa_bias_channel(dev, ref_chan)

    else: 
        pass


    # for element in dev.elements.values():
    #     str_channel = str(element)
    #     value = int(mr.strip_to_last_two_digits(str_channel))
    #     if value in matrix_64elem:
    #         detect = []
    #         if value == ref_chan:
    #             continue
    #         else:
    #             print(f"Element: {value}")
    #             # SpecAn.write("INIT:CONT OFF ")
    #             # SpecAn.write("TRIGger:VIDeo:STAT ON")
    #             # SpecAn.write("TRIGger:VIDeo:SOURce VIDeo")
    #             # SpecAn.write("TRIGger:VIDeo:LEVel -66.80 dBm")
    #             # SpecAn.write("TRIGger:VIDeo:SLOPe NEGative")
    #             # SpecAn.write("TRIGger:VIDeo:DELay -14.1E-6")
    #             # enable the video trigger
                
    #             mr.enable_pa_bias_channel(dev, value)
    #             mr.enable_pa_bias_channel(dev, ref_chan)


    #             for j in range(181):
                
    #                 element.tx_phase = j
    #                 dev.latch_tx_settings()
    #                 tone_0 = SpecAn.get_marker_power(marker=1)
    #                 tone_0_freq = SpecAn.get_marker_freq(marker = 1)
    #                 detect.append(tone_0)

                

    #         mr.disable_pa_bias_channel(dev, value)
    #         mr.disable_pa_bias_channel(dev, ref_chan)
    #         min_phase = detect.index(min(detect))
    #         print(f'Null power at {min_phase} deg')
            
    #         print(f'Setting {element} calibrated phase')
    #         element.tx_phase = min_phase + 180
    #         digi_phase_values.append(min_phase + 180)
    #         dev.latch_tx_settings()

    #     else: 
    #         pass

    ## Turn off all elements
    mr.disable_pa_bias_channel(dev)
    #Calculate Relative Digital Phase Values

    # NumChannels = 4
    # digi_phase_relative = np.zeros(NumChannels)
    # # for i in range(NumChannels):


    # sdr  = adi.adrv9009_zu11eg(talise_uri)
    # # Send phase aligned pulses out of DAC
    # sdr.tx_destroy_buffer()
    # sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*digi_phase_values[0]*np.pi/180), pulse0_iq*np.exp(1j*digi_phase_values[1]*np.pi/180), pulse0_iq*np.exp(1j*digi_phase_values[2]*np.pi/180)])

    # dig_phase = [0, digi_phase_values[0], digi_phase_values[1], digi_phase_values[2]]

    # #Reference Channel
    # # ref_channels = subarray[:, 1]
    # ref_channels = [3]
    # # mr.enable_pa_bias_channel(dev, ref_channels[0])
    # mr.enable_pa_bias_channel(dev, ref_channels)



    # ## Enable channel one at a time.  Sweep phase 0-180 degrees and find null point.  ##
    # ## Set calibrated phase to null point + 180 degrees ##
    # for element in dev.elements.values():
    #     str_channel = str(element)
    #     value = int(mr.strip_to_last_two_digits(str_channel))
    #     if value not in ref_channels:
    #         detect = []
    #         print(f"Element: {value}")
    #         mr.enable_pa_bias_channel(dev, value)
    #         mr.enable_pa_bias_channel(dev, ref_channels[0])


    #         for j in range(181):
            
    #             element.tx_phase = j
    #             print('Phase: ', element.tx_phase)
    #             dev.latch_tx_settings()
    #             tone_0 = SpecAn.get_marker_power(marker=1)
    #             detect.append(tone_0)
                

    #         mr.disable_pa_bias_channel(dev, value)
    #         mr.disable_pa_bias_channel(dev, ref_channels[0])
    #         min_phase = detect.index(min(detect))
    #         print(f'Null power at {min_phase} deg')
            
    #         print(f'Setting {element} calibrated phase')
    #         element.tx_phase = min_phase + 180
    #         dev.latch_tx_settings()

    #     else: 
    #         pass

    # ## Turn off all elements
    # mr.disable_pa_bias_channel(dev)

## Auto launch beamsteering plot script ##


try:
    script_path = os.path.join(os.path.dirname(__file__), "Manta_Ray_Tx_BeamsteeringPlots_draft_dec_11.py")
    print(f"Launching beamsteering plot script: {script_path}")
    result = subprocess.run([sys.executable, script_path], cwd=os.path.dirname(__file__))
    if result.returncode != 0:
        print(f"Beamsteering script exited with code {result.returncode}")
        sys.exit(result.returncode)
except Exception as e:
    print(f"Failed to launch beamsteering script: {e}")
    raise

