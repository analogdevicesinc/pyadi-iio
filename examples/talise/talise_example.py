import sys
import numpy as np
import adi
import matplotlib.pyplot as plt
import time
from scipy import signal

# from talise_functions import (
#     phase_calibration,
# )

try:
    import config_custom_talise as config  # this has all the key parameters that the user would want to change (i.e. calibration phase and antenna element spacing)

    print("Found custom config file")
except:
    print("Didn't find custom config, looking for default.")
    try:
        import config_talise as config
    except:
        print("Make sure config.py is in this directory")
        sys.exit(0)

colors = ["black", "gray", "red", "orange", "yellow", "green", "blue", "purple"]


def talise_init(my_talise):
    # TODO: after first test, use config file 
    print("Transmitted baseband complex sinusoid frequency: " + str(config.tx_sine_baseband_freq))
    print("Numeric value of discrete amplitude of transmitted signal: " + str(config.amplitude_discrete))
    # frequency = 245760  # 245.760 kHz
    # amplitude = 2**14
    # my_talise.rx_sample_rate = config.sample_rate
    print("Number of samples per call to rx(): " + str(config.num_samps))
    # num_samps = int((20*sample_rate)/frequency) # number of samples per call to rx()

    # TODO: print text for every parameter set:
    my_talise.rx_enabled_channels = config.rx_channels_used
    my_talise.tx_enabled_channels = config.tx_channels_used

    my_talise.trx_lo = config.lo_freq
    my_talise.trx_lo_chip_b = config.lo_freq

    my_talise.tx_cyclic_buffer = True

    my_talise.gain_control_mode_chan0 = config.rx_gain_control_mode
    my_talise.gain_control_mode_chan1 = config.rx_gain_control_mode

    my_talise.tx_hardwaregain_chan0 = config.tx_gain
    my_talise.tx_hardwaregain_chan1 = config.tx_unused_channel_gain
    my_talise.tx_hardwaregain_chan0_chip_b = config.tx_unused_channel_gain
    my_talise.tx_hardwaregain_chan1_chip_b = config.tx_unused_channel_gain

    my_talise.gain_control_mode_chan0 = config.rx_gain_control_mode
    my_talise.gain_control_mode_chan1 = config.rx_gain_control_mode
    my_talise.gain_control_mode_chan0_chip_b = config.rx_gain_control_mode
    my_talise.gain_control_mode_chan1_chip_b = config.rx_gain_control_mode

    my_talise.rx_hardwaregain_chan0 = config.rx_gain
    my_talise.rx_hardwaregain_chan1 = config.rx_gain
    my_talise.rx_hardwaregain_chan0_chip_b = config.rx_gain
    my_talise.rx_hardwaregain_chan1_chip_b = config.rx_gain

    my_talise.rx_buffer_size = config.num_samps
    my_talise._tx_buffer_size = config.num_samps

    print("Syncing")
    my_talise.mcs_chips()
    print("Done syncing")
    print("Calibrating")
    my_talise.calibrate_rx_qec_en = 1
    my_talise.calibrate_rx_qec_en_chip_b = 1
    my_talise.calibrate_tx_qec_en = 1
    my_talise.calibrate_tx_qec_en_chip_b = 1
    my_talise.calibrate_rx_phase_correction_en_chip_b = 1
    my_talise.calibrate_rx_phase_correction_en = 1
    my_talise.calibrate = 1
    my_talise.calibrate_chip_b = 1
    print("Done calibrating")

    #TODO: load gain calibration coefficients (from .pkl files)
    # for phase they are needed to be loaded as degrees
    # TODO: add below two functions in adi.adrv9009_zu11eg
    # my_talise.load_gain_cal("gain_cal_val.pkl")
    # my_talise.load_phase_cal("phase_cal_val.pkl")
    # TODO: add in adi.adrv9009_zu11eg, phase constants as degrees between rx channel 0 and 1,2,3

def measure_phase_degrees(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error

def adjust_phase(talise_obj, rx_samples_ch1, rx_samples_ch2, rx_samples_ch3):
    ph1 = np.deg2rad(talise_obj.pcal[0])
    print("Phase of " + str(talise_obj.pcal[0]) + " to radians = " + str(ph1))
    ph2 = np.deg2rad(talise_obj.pcal[1])
    print("Phase of " + str(talise_obj.pcal[1]) + " to radians = " + str(ph2))
    ph3 = np.deg2rad(talise_obj.pcal[2])
    print("Phase of " + str(talise_obj.pcal[2]) + " to radians = " + str(ph3))
    rx_samples_ch1 = rx_samples_ch1 * np.exp(1j * ph1)
    rx_samples_ch2 = rx_samples_ch2 * np.exp(1j * ph2)
    rx_samples_ch3 = rx_samples_ch3 * np.exp(1j * ph3)
    
    return [rx_samples_ch1, rx_samples_ch2, rx_samples_ch3]   
    
def do_cal_phase(my_talise):
    # Configure talise and load calibration constants from file
    talise_init(my_talise)

    ############################################################################################################
    # Create and plot a complex sinusoid #######################################################################
    ############################################################################################################

    # Calculate time values
    t = np.arange(config.num_samps) / config.sample_rate
    # Generate sinusoidal waveform
    phase_shift = -np.pi/2  # Shift by -90 degrees
    tx_samples = config.amplitude_discrete * (np.cos(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift) + 1j*np.sin(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift))

    # Plot Tx time domain
    plt.figure(1)
    plt.plot(t, np.real(tx_samples), label = "I (Real)")
    plt.plot(t, np.imag(tx_samples), label = "Q (Imag)")
    plt.legend()
    plt.title('Tx time domain')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Amplitude')

    # Calculate Tx spectrum in dBFS
    tx_samples_fft = tx_samples * np.hanning(config.num_samps)
    ampl_tx = (np.abs(np.fft.fftshift(np.fft.fft(tx_samples_fft))))
    fft_txvals_iq_dbFS = 10*np.log10(np.real(ampl_tx)**2 + np.imag(ampl_tx)**2) + 20*np.log10(2/2**(16-1))\
                                            - 20*np.log10(len(ampl_tx))
    f = np.linspace(config.sample_rate/-2, config.sample_rate/2, len(fft_txvals_iq_dbFS))

    # Plot Tx freq domain
    plt.figure(2)
    plt.plot(f/1e6, fft_txvals_iq_dbFS)
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("dBFS")
    plt.title('Tx FFT')

    # Constellation plot for the transmit data
    plt.figure(3)
    plt.plot(np.real(tx_samples), np.imag(tx_samples), '.')
    plt.xlabel("I (Real) Sample Value")
    plt.ylabel("Q (Imag) Sample Value")
    plt.grid(True)
    plt.title('Constellation Plot Tx')
    ############################################################################################################
    ############################################################################################################

    ############################################################################################################
    # Call Tx function to start transmission ###################################################################
    ############################################################################################################
    my_talise.tx(tx_samples) # start transmitting
    ############################################################################################################
    ############################################################################################################
    
    time.sleep(1) # wait for internal calibrations
    # Clear buffer just to be safe
    for i in range (0, 40):
        raw_data = my_talise.rx()
    ############################################################################################################
    # Call Rx function to receive transmission and plot the data################################################
    ############################################################################################################
    # Receive and plot time domain data before calibration
    rx_samples = my_talise.rx()

    # Time values
    t = np.arange(config.num_samps) / config.sample_rate

    # Plot Rx time domain
    plt.figure(4)

    plt.plot(np.real(rx_samples[0]), label = "Ch0 I (Real)")
    plt.plot(np.imag(rx_samples[0]), label = "Ch0 I (Real)")

    plt.plot(np.real(rx_samples[1]), label = "Ch1 I (Real)")
    plt.plot(np.imag(rx_samples[1]), label = "Ch1 I (Real)")

    plt.plot(np.real(rx_samples[2]), label = "Ch2 I (Real)")
    plt.plot(np.imag(rx_samples[2]), label = "Ch2 I (Real)")

    plt.plot(np.real(rx_samples[3]), label = "Ch3 I (Real)")
    plt.plot(np.imag(rx_samples[3]), label = "Ch3 I (Real)")

    plt.legend()
    plt.title('Rx time domain before Ph Cal')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Amplitude')

    # Calulate phase difference between rx0 - rx1; rx0 - rx2; rx0 - rx3: 
    repeat_ph_calculations = 10
    ph_diff_ch0_minus_ch1 = []
    ph_diff_ch0_minus_ch2 = []
    ph_diff_ch0_minus_ch3 = []

    avg_ph_diff_ch0_minus_ch1 = 0
    avg_ph_diff_ch0_minus_ch2 = 0
    avg_ph_diff_ch0_minus_ch3 = 0

    sum_ph_diff_ch0_minus_ch1 = 0
    sum_ph_diff_ch0_minus_ch2 = 0
    sum_ph_diff_ch0_minus_ch3 = 0

    max_ph_diff_ch0_minus_ch1 = 0
    min_ph_diff_ch0_minus_ch1 = 0
    max_ph_diff_ch0_minus_ch2 = 0
    min_ph_diff_ch0_minus_ch2 = 0
    max_ph_diff_ch0_minus_ch3 = 0
    min_ph_diff_ch0_minus_ch3 = 0

    for i in range(repeat_ph_calculations):
        rx_samples = my_talise.rx()
        print("Iteration " + str(i) + ":")
        print("Ph Diff Between ch0 and ch1: " + str(measure_phase_degrees(rx_samples[0], rx_samples[1])))
        ph_diff_ch0_minus_ch1.append(measure_phase_degrees(rx_samples[0], rx_samples[1]))
        print("Ph Diff Between ch0 and ch2: " + str(measure_phase_degrees(rx_samples[0], rx_samples[2])))
        ph_diff_ch0_minus_ch2.append(measure_phase_degrees(rx_samples[0], rx_samples[2]))
        print("Ph Diff Between ch0 and ch3: " + str(measure_phase_degrees(rx_samples[0], rx_samples[3])))
        ph_diff_ch0_minus_ch3.append(measure_phase_degrees(rx_samples[0], rx_samples[3]))
        sum_ph_diff_ch0_minus_ch1 += ph_diff_ch0_minus_ch1[i]
        sum_ph_diff_ch0_minus_ch2 += ph_diff_ch0_minus_ch2[i]
        sum_ph_diff_ch0_minus_ch3 += ph_diff_ch0_minus_ch3[i]

    # Calculate average for each phase difference:
    avg_ph_diff_ch0_minus_ch1 = sum_ph_diff_ch0_minus_ch1/repeat_ph_calculations
    avg_ph_diff_ch0_minus_ch2 = sum_ph_diff_ch0_minus_ch2/repeat_ph_calculations
    avg_ph_diff_ch0_minus_ch3 = sum_ph_diff_ch0_minus_ch3/repeat_ph_calculations

    # Save Phase differences in degrees in .pkl file
#     values = [avg_ph_diff_ch0_minus_ch1, avg_ph_diff_ch0_minus_ch2, avg_ph_diff_ch0_minus_ch3]
#     if isinstance(values, list) and all(isinstance(item, float) for item in values):
#         if len(values) == (my_talise.num_elements - 1):
#                 x = values
#         print("IF OK: " + str(x))
    my_talise.pcal = [avg_ph_diff_ch0_minus_ch1, avg_ph_diff_ch0_minus_ch2, avg_ph_diff_ch0_minus_ch3]
    print("pcal values: " + str(my_talise.pcal))
    my_talise.save_phase_cal()
    my_talise.load_phase_cal()
    print("pcal values after save: " + str(my_talise.pcal))

    print("Avg ph diff for ch0 - ch1: " + str(avg_ph_diff_ch0_minus_ch1))
    print("Avg ph diff for ch0 - ch2: " + str(avg_ph_diff_ch0_minus_ch2))
    print("Avg ph diff for ch0 - ch3: " + str(avg_ph_diff_ch0_minus_ch3))

    # Calculate max and min ph diff
    max_ph_diff_ch0_minus_ch1 = max(ph_diff_ch0_minus_ch1)
    min_ph_diff_ch0_minus_ch1 = min(ph_diff_ch0_minus_ch1)
    max_ph_diff_ch0_minus_ch2 = max(ph_diff_ch0_minus_ch2)
    min_ph_diff_ch0_minus_ch2 = min(ph_diff_ch0_minus_ch2)
    max_ph_diff_ch0_minus_ch3 = max(ph_diff_ch0_minus_ch3)
    min_ph_diff_ch0_minus_ch3 = min(ph_diff_ch0_minus_ch3)

    print("Max diff in phase ch0-ch1: " + str(max_ph_diff_ch0_minus_ch1))
    print("Max diff in phase ch0-ch2: " + str(max_ph_diff_ch0_minus_ch2))
    print("Max diff in phase ch0-ch3: " + str(max_ph_diff_ch0_minus_ch3))

    print("Min diff in phase ch0-ch1: " + str(min_ph_diff_ch0_minus_ch1))
    print("Min diff in phase ch0-ch2: " + str(min_ph_diff_ch0_minus_ch2))
    print("Min diff in phase ch0-ch3: " + str(min_ph_diff_ch0_minus_ch3))

    print("Max variance: " + str(max((max_ph_diff_ch0_minus_ch1 - min_ph_diff_ch0_minus_ch1), (max_ph_diff_ch0_minus_ch2 - min_ph_diff_ch0_minus_ch2), (max_ph_diff_ch0_minus_ch3 - max_ph_diff_ch0_minus_ch3))))
    
    # Adjust phase
    arrays_adjusted = adjust_phase(my_talise, rx_samples[1], rx_samples[2], rx_samples[3])
    rx_samples[1] = arrays_adjusted[0]
    rx_samples[2] = arrays_adjusted[1]
    rx_samples[3] = arrays_adjusted[2]
    # Display time plot with phase adjusted
    # Time values
    t = np.arange(config.num_samps) / config.sample_rate

    # Plot Rx time domain
    plt.figure(5)

    plt.plot(np.real(rx_samples[0]), label = "Ch0 I (Real)")
    plt.plot(np.imag(rx_samples[0]), label = "Ch0 I (Real)")

    plt.plot(np.real(rx_samples[1]), label = "Ch1 I (Real)")
    plt.plot(np.imag(rx_samples[1]), label = "Ch1 I (Real)")

    plt.plot(np.real(rx_samples[2]), label = "Ch2 I (Real)")
    plt.plot(np.imag(rx_samples[2]), label = "Ch2 I (Real)")

    plt.plot(np.real(rx_samples[3]), label = "Ch3 I (Real)")
    plt.plot(np.imag(rx_samples[3]), label = "Ch3 I (Real)")

    plt.legend()
    plt.title('Rx time domain after Ph Cal')
    plt.xlabel('Time (seconds)')
    plt.ylabel('Amplitude') 
    # For testing:
    # print(my_talise.pcal)

    # TODO: test untill here
    
    # PhaseValues, plot_data = my_phaser.phase_calibration(
    #     verbose=True
    # # )  # Start Phase Calibration
    # PhaseValues, plot_data = phase_calibration(
    #     my_talise, verbose=True
    # )  # Start Phase Calibration
    # plt.figure(5)
    # plt.title("Phase sweeps of adjacent elements")
    # plt.xlabel("Phase difference (degrees)")
    # plt.ylabel("Amplitude (ADC counts)")
    # for i in range(0, 7):
    #     plt.plot(PhaseValues, plot_data[i], color=colors[i])

    # Stop transmitting
    my_talise.tx_destroy_buffer()
    plt.show()


# First try to connect to a locally connected Talise. On success, connect,
# on failure, connect to remote Talise

try:
    print("Attempting to connect to Talise via ip:localhost...")
    my_talise = adi.adrv9009_zu11eg(uri="ip:localhost")
    print("Found Talise.")

except:
    print("Talise not found.")

time.sleep(0.5)

func = sys.argv[1] if len(sys.argv) >= 2 else "plot"

if func == "cal":
    print("Calibrating Phase, verbosely, then saving cal file...")
    # TODO: add do cal_gain
    do_cal_phase(my_talise)  # Start Phase Calibration
    print("Done calibration")


if func == "plot":
    do_plot = True
else:
    do_plot = False

# while do_plot == True:
#     try:
#         # TODO: plot antenna pattern
#     except KeyboardInterrupt:
#         do_plot = False
#         print("Exiting Loop")
