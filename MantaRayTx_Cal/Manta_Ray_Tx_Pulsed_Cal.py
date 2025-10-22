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
import paramiko
import MantaRay as mr
import math
import sys

rm = pyvisa.ResourceManager()

##############################################
## Step 1: Configure Manta Ray for Tx ##
###############################################


print("Set PA_ON to 0")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")
time.sleep(1)
ssh.close()


print("Turn on 4V, then -6V supplies")
input("Press Enter to continue...")
talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
talise_uri = "ip:" + talise_ip

print("Connecting to BFC Tile")


dev = adi.adar1000_array(
    "ip:192.168.1.1", 
    chip_ids= 	[	
                    "adar1000_csb_0_1_1", "adar1000_csb_0_1_2", "adar1000_csb_0_1_3", "adar1000_csb_0_1_4",
                    "adar1000_csb_1_1_1", "adar1000_csb_1_1_2", "adar1000_csb_1_1_3", "adar1000_csb_1_1_4",
                    "adar1000_csb_0_2_1", "adar1000_csb_0_2_2", "adar1000_csb_0_2_3", "adar1000_csb_0_2_4",
                    "adar1000_csb_1_2_1", "adar1000_csb_1_2_2", "adar1000_csb_1_2_3", "adar1000_csb_1_2_4"
                ],
    device_map=	[
                    [2, 1], 
                    [3, 4],
                    [6, 5], 
                    [7, 8],
                    [10, 9],
                    [11, 12],
                    [14, 13],
                    [15, 16],
                ],
    element_map=[
                    [1, 2, 3, 4], 
                    [5, 6, 7, 8], 
                    [9, 10, 11, 12], 
                    [13, 14, 15, 16],
                    [17, 18, 19, 20], 
                    [21, 22, 23, 24], 
                    [25, 26, 27, 28], 
                    [29, 30, 31, 32],
                    [33, 34, 35, 36], 
                    [37, 38, 39, 40], 
                    [41, 42, 43, 44], 
                    [45, 46, 47, 48],
                    [49, 50, 51, 52], 
                    [53, 54, 55, 56], 
                    [57, 58, 59, 60], 
                    [61, 62, 63, 64],
                ],
    device_element_map={
                1: 	[4, 8, 7, 3],
                2: 	[2, 6, 5, 1],
                3: 	[13, 9, 10, 14],
                4: 	[15, 11, 12, 16],
                5: 	[20, 24, 23, 19],
                6: 	[18, 22, 21, 17],
                7: 	[29, 25, 26, 30],
                8: 	[31, 27, 28, 32],
                9: 	[36, 40, 39, 35],
                10: 	[34, 38, 37, 33],
                11: 	[45, 41, 42, 46],
                12: 	[48, 44, 43, 47],
                13: 	[52, 56, 55, 51],
                14: 	[50, 54, 53, 49],
                15: 	[61, 57, 58, 62],
                16: 	[64, 60, 59, 63],
    },
)


for device in dev.devices.values():
    device.tr_source = "spi"
    
print("Connected to BFC Tile")

mr.disable_stingray_channel(dev)

print("Initializing BFC Tile")
dev.initialize_devices(-4.6, -4.6, -4.6, -4.6)
for device in dev.devices.values():
    device.mode = "rx"
    device.bias_dac_mode = "on"
    for channel in device.channels:
        # Default channel enable
        channel.rx_enable = True
print("Initialized BFC Tile")


print("Turn on 5.7V, current should be ~365mA")
input("Press Enter to continue...")


print("Turn on 18V, current should be ~4mA")
input("Press Enter to continue...")

## Set elements to turn on for Tx ##
subarray_ref = np.array([7, 39, 55, 23])


for i in subarray_ref:
    time.sleep(0.25)
    print("Setting element " + str(i) + " gain max")
    dev.elements[i].tx_gain = 127
    print("Setting element " + str(i) + " attenuator off")
    dev.elements[i].tx_attenuator = False
    print("Setting element " + str(i) + " phase 0")
    dev.elements[i].tx_phase = 0
    print("Setting element " + str(i) + " PA bias to -2.2")
    dev.elements[i].pa_bias_on = -2.2
    print("Setting element " + str(i) + " Tx Enable")
    dev.elements[i].tx_enable = True
    print("Setting Adar " + str(i) + " TR Source")
    for device in dev.devices.values():
        device.tr_source = "external"
        device.bias_dac_mode = "toggle"
    print("Load Tx Setting")
    dev.latch_tx_settings()

for i in range(2):
    ##############################################
    ## Step 2: Configure Talise DACs ##
    ###############################################


    talise_ip = "192.168.1.1" # ADRV9009-zu11eg board ip address
    talise_uri = "ip:" + talise_ip
    # Create radio
    sdr  = adi.adrv9009_zu11eg(talise_uri)
    tddn = adi.tddn(talise_uri)

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
    # 4 pulses for 4 Tx channels, pulse0 on chan0, pulse1 on chan1, pulse 2 on cham2, pulse3 on chan3
    PRI_ms = 0.1 #100 us pulse repitition interval
    duty_cycle = 0.1 # 10% duty cycle
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

    # # Capture RX data
    # print("Capturing RX data...")

    # capture_range = 1

    # rx_ch0 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
    # rx_ch1 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
    # rx_ch2 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
    # rx_ch3 = np.zeros((capture_range, sdr.rx_buffer_size), dtype=np.complex64)
    # for capture in range(capture_range):
    #     sdr.rx_destroy_buffer()
    #     tddn.sync_soft  = 1

    #     rx_data = sdr.rx()

    #     # Extract I/Q data for both channels
    #     rx_ch0[capture] = rx_data[0]
    #     rx_ch1[capture] = rx_data[1]
    #     rx_ch2[capture] = rx_data[2]
    #     rx_ch3[capture] = rx_data[3]

    #     time.sleep(1)  # Small delay between captures

    # print(f"RX data captured - Ch0: {len(rx_ch0[-1])} samples, Ch1: {len(rx_ch1[-1])} samples")




print("Setting PA_ON to 1")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 1")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 1")
time.sleep(1)
ssh.close()




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

SpecAn_Center_Freq = 9.9945e9   #Set to transmit frequency
SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
SpecAn_Res_BW = 10e3   #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
MinCodeVal = 0.015   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
NumChannels = 4   #Set to number of channels being used


SpecAn.select_iq_mode()    #Set spec an for complex IQ mode
SpecAn.reset()   
SpecAn_Center_Freq = 9.9945e9   #Set to transmit frequency
SpecAn_IQ_BW =  10e6   #Set based upon instrument - testing done at 10MHz (Maximum for CXA used)
SpecAn_Res_BW = 10e3   #Set Resolution Bandwidth of Spec An. 15kHz for 20% Duty Cycle was sufficient, 18kHz for 10% Duty Cycle was sufficient. Will automatically set #samples in FFT and FFT window length
SpecAn_Dig_IFBW = 10e6   #Set the digital IFBW of Spec An. Tested at 10MHz for both 10 and 20% Duty Cycles
MinCodeVal = 0.015   #Set to 0.00055 for 20% DC, 0.00031 for 10% DC
NumChannels = 4   #Set to number of channels being used          #Reset instrument
SpecAn.set_initiate_continuous_sweep('ON') #Set contionuous mode of spec an
SpecAn.set_iq_spec_span(SpecAn_IQ_BW)  #Set IQ bandwidth of instrument
SpecAn.set_iq_spec_bandwidth(SpecAn_Res_BW)    #Set ResBW
SpecAn.set_center_freq(SpecAn_Center_Freq)     #Set SpecAn center frequency
SpecAn.set_iq_mode_bandwidth(SpecAn_Dig_IFBW)  #Set Digital IFBW
SpecAn.bursttrig('POS', -5, 0, -45)    #Set trigger parameters for Spec An. First input is slope, second is delay (uS), third is relative level, last is absolute level
SpecAn.trigger()
SpecAn.wavexscale(0, 40000, 'LEFT', 'OFF')
SpecAn.waveyscale(0, 80, 'CENT', 'OFF')


numRuns = 1
PhaseAVG = 1
phaseValsAll = np.zeros((NumChannels, PhaseAVG))
for run in range(numRuns):

    ## Turn on PAs on Manta Ray ##
    print("Setting PA_ON to 1")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 1")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 1")
    time.sleep(1)
    ssh.close()

    ## Take Data from Spec An ##
    ComplexData = SpecAn.iq_complex_data()
    # SigGen.set_output_state('OFF')  #Turn off Sig Gen output

    # SpecAn.set_continuous_peak_search(1, 'ON')
    # peakPowerSingleElement = SpecAn.get_marker_power(marker=1)
    # print("Peak Power Single Element (dBm): ", peakPowerSingleElement)

    # Stop PAs from transmitting on Manta Ray ##
    time.sleep(1)  #Wait for any remaining data to be sent
    print("Setting PA_ON to 0")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
    ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")
    time.sleep(1)
    ssh.close()

    #Separate the I and Q components of the complex data
    I = np.real(ComplexData)
    Q = np.imag(ComplexData)

    #Plot the I and Q waveforms 
    plt.figure()
    plt.subplot(2, 1, 1)
    plt.plot(np.abs(I))
    plt.title('I Component')
    plt.subplot(2, 1, 2)
    plt.plot(np.abs(Q))
    plt.title('Q Component')


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



a=1
# sdr.tx_destroy_buffer()
# # When using sdr.tx, the the Data Offload Tx mode is automatically set to one shot...
# sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*phaseValsAvg[1]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[2]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[3]*np.pi/180)])


# Send phase aligned pulses out of DAC
sdr.tx_destroy_buffer()
sdr.tx([pulse0_iq, pulse0_iq*np.exp(1j*phaseValsAvg[1]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[2]*np.pi/180), pulse0_iq*np.exp(1j*phaseValsAvg[3]*np.pi/180)])


## Turn on PAs on Manta Ray ##
print("Setting PA_ON to 1")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 1")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 1")
time.sleep(1)
ssh.close()

## Take Data from Spec An ##
ComplexData = SpecAn.iq_complex_data()


time.sleep(1)  #Wait for any remaining data to be sent

## Turn off PAs from transmitting on Manta Ray ##
print("Setting PA_ON to 0")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(hostname="192.168.1.1", port=22, username="root", password="analog")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray0_control 'voltage0' 'raw' 0")
ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command("iio_attr -c stingray1_control 'voltage0' 'raw' 0")
time.sleep(1)
ssh.close()

phaseValsAll = np.zeros((NumChannels, numRuns))

#Separate the I and Q components of the complex data
I = np.real(ComplexData)
Q = np.imag(ComplexData)

#Plot the I and Q waveforms 
plt.figure()
plt.subplot(2, 1, 1)
plt.plot(np.abs(I))
plt.title('I Component')
plt.subplot(2, 1, 2)
plt.plot(np.abs(Q))
plt.title('Q Component')


########### Post Processing Section ############
#Find peaks above threshold
RealPk, _ = find_peaks(np.abs(I), height = MinCodeVal)
ImagPk, _ = find_peaks(np.abs(Q), height = MinCodeVal)


ComplexData = np.roll(ComplexData, -700, axis=0)

Period, InitialCross, FinalCross, NextCross, Midlev = pulseperiod(
    (np.abs(ComplexData) > MinCodeVal).astype(float))
channel0Start = int(np.ceil(InitialCross[0]))

timeZeroAlignedFirstRx = np.roll(ComplexData, -channel0Start)
timeZeroAligned = np.roll(ComplexData, -channel0Start, axis=0)


# peakPowerFourElements = SpecAn.get_marker_power(marker=1)
# print("Peak Power Four Elements (dBm): ", peakPowerFourElements)

print(channel0Start)

plt.figure()
plt.plot(np.abs(timeZeroAligned))
plt.title('Zero Aligned Samples')
plt.show()

# Now Determine the Phase Offsets for Each Tx Channel
phaseVals = np.zeros((NumChannels, 1))
relativePhaseVals = np.zeros((NumChannels, 1))

phaseVals = np.zeros((NumChannels, 1))
for i in range(NumChannels):
    phaseVals[i, 0] = (np.angle(timeZeroAlignedFirstRx[62 + (i*149)]) * (180/np.pi))
    relativePhaseVals[i, 0] = phaseVals[i, 0] - phaseVals[0, 0]
    relativePhaseVals[i, 0] = np.mod(relativePhaseVals[i, 0], 360)
print(relativePhaseVals)
phaseValsAll[:, run] = relativePhaseVals[:, 0]