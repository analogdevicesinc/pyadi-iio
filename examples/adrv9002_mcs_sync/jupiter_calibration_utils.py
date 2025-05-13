"""
This Python file contains application level calibration methods rocedures for phased
array antenna receiver system. It specifically focuses on performing gain and phase calibrations.
These methods work in conjunction with attributes and methods from adrv9002_multi class.
"""

import numpy as np
import matplotlib.pyplot as plt
import time
from jupiter_init_from_config import jupiter_init
import jupiter_config as config


def measure_phase_degrees(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error


def adjust_gain(jupiter_obj, *args):
    adjusted_samples = []
    if len(args) == config.used_rx_channels:
        for i, samples in enumerate(args):
            adjusted_samples.append(samples * jupiter_obj.gcal[i])
        return adjusted_samples
    else:
        print(
            "WARNING: Wrong number of input arrays, check used_rx_channels in the config file!"
        )
        return 0


def adjust_phase(jupiter_obj, phase_shift_deg, *args):
    adjusted_samples = []
    if len(args) == (config.used_rx_channels):
        # First channel is the reference channel and is not shifted
        adjusted_samples.append(args[0])
        for i, samples in enumerate(args[1:], start=1):
            phase_rad = np.deg2rad(
                ((phase_shift_deg * i) + jupiter_obj.pcal[i - 1]) % 360.0
            )
            # print("Phase of " + str(jupiter_obj.pcal[i]) + " to radians = " + str(phase_rad))
            adjusted_samples.append(samples * np.exp(1j * phase_rad))
        return adjusted_samples
    else:
        print(
            "WARNING: Wrong number of input arrays, check used_rx_channels in the config file!"
        )
        return 0


def do_cal_gain(sdrs):
    # Configure jupiter and load calibration constants from file
    jupiter_init(sdrs)

    #################################################
    # Create and plot a complex sinusoid ############
    #################################################

    # Calculate time values
    t = np.arange(config.num_samps) / config.sample_rate
    # Generate sinusoidal waveform
    phase_shift = -np.pi / 2  # Shift by -90 degrees
    tx_samples = config.amplitude_discrete * (
        np.cos(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift)
        + 1j * np.sin(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift)
    )

    #     # Plot Tx time domain
    #     plt.figure(1)
    #     plt.plot(t, np.real(tx_samples), label = "I (Real)")
    #     plt.plot(t, np.imag(tx_samples), label = "Q (Imag)")
    #     plt.legend()
    #     plt.title('Tx time domain')
    #     plt.xlabel('Time (seconds)')
    #     plt.ylabel('Amplitude')

    # Calculate Tx spectrum in dBFS
    tx_samples_fft = tx_samples * np.hanning(config.num_samps)
    ampl_tx = np.abs(np.fft.fftshift(np.fft.fft(tx_samples_fft)))
    fft_txvals_iq_dbFS = (
        10 * np.log10(np.real(ampl_tx) ** 2 + np.imag(ampl_tx) ** 2)
        + 20 * np.log10(2 / 2 ** (16 - 1))
        - 20 * np.log10(len(ampl_tx))
    )
    f = np.linspace(
        config.sample_rate / -2, config.sample_rate / 2, len(fft_txvals_iq_dbFS)
    )

    #     # Plot Tx freq domain
    #     plt.figure(2)
    #     plt.plot(f/1e6, fft_txvals_iq_dbFS)
    #     plt.xlabel("Frequency [MHz]")
    #     plt.ylabel("dBFS")
    #     plt.title('Tx FFT')
    #
    #     # Constellation plot for the transmit data
    #     plt.figure(3)
    #     plt.plot(np.real(tx_samples), np.imag(tx_samples), '.')
    #     plt.xlabel("I (Real) Sample Value")
    #     plt.ylabel("Q (Imag) Sample Value")
    #     plt.grid(True)
    #     plt.title('Constellation Plot Tx')
    ##################################################
    ##################################################

    ##################################################
    # Call Tx function to start transmission #########
    ##################################################
    sdrs.primary.tx(tx_samples)

    time.sleep(1)  # wait for internal calibrations
    # Clear buffer just to be safe
    for i in range(0, 2):
        raw_data = sdrs.rx()

    #############################################################
    # Call Rx function to receive transmission and plot the data#
    #############################################################
    # Receive and plot time domain data before calibration
    rx_samples = sdrs.rx()

    time.sleep(1)  # wait for internal calibrations
    # Adjust phase
    rx_samples = adjust_phase(
        sdrs, 0, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
    )

    # Time values
    t = np.arange(config.num_samps) / config.sample_rate

    # Plot Rx time domain before gain calibration
    # plt.figure(4)
    fig, axs = plt.subplots(nrows=2, sharex=False, figsize=(10, 8))
    # Full screen plot
    manager = plt.get_current_fig_manager()
    try:
        manager.window.attributes("-zoomed", True)
    except AttributeError:
        try:
            manager.window.showMaximized()
        except:
            print("Fullscreen not supported.")

    axs[0].plot(t, np.real(rx_samples[0]), label="Ch0 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[0]), label="Ch0 Q (Imag)")

    axs[0].plot(t, np.real(rx_samples[1]), label="Ch1 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[1]), label="Ch1 Q (Imag)")

    axs[0].plot(t, np.real(rx_samples[2]), label="Ch2 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[2]), label="Ch2 Q (Imag)")

    axs[0].plot(t, np.real(rx_samples[3]), label="Ch3 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[3]), label="Ch3 Q (Imag)")

    axs[0].legend()
    axs[0].grid(True)
    axs[0].set_title("Rx time domain before Gain Caliration")
    axs[0].set_xlabel("Time [seconds]")
    axs[0].set_ylabel("Amplitude [LSB]")

    amplitudes = [1.0] * (sdrs.num_rx_elements)
    max_amplitude = 0
    elem_with_max_amplitude = 0
    # Save received amplitudes from each channel
    for i in range(sdrs.num_rx_elements):
        max_amp_ch_i = np.max(np.real(rx_samples[i]))
        amplitudes[i] = max_amp_ch_i
        if max_amp_ch_i > max_amplitude:
            elem_with_max_amplitude = i

    print("Amplitudes list: " + str(amplitudes))

    # Calculate the calibration coefficents between the amplitude on the channel with max amplitude and other channels
    amplitude_cal_coeff = [1.0] * (sdrs.num_rx_elements)
    print("Empty aplitude_cal_coeff list" + str(type(amplitude_cal_coeff)))
    for i in range(sdrs.num_rx_elements):
        if i != elem_with_max_amplitude:
            amplitude_cal_coeff[i] = amplitudes[elem_with_max_amplitude] / amplitudes[i]
        else:
            amplitude_cal_coeff[i] = 1.0

    print("Type of amplitude_cal_coeff: " + str(type(amplitude_cal_coeff[0])))

    # Save gain calibration coefficents and print them
    sdrs.gcal = amplitude_cal_coeff
    print("Gain calibration coefficents: " + str(amplitude_cal_coeff))
    sdrs.save_gain_cal()
    sdrs.load_gain_cal()

    # Adjust gain
    arrays_adjusted = adjust_gain(
        sdrs, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
    )
    for i in range(sdrs.num_rx_elements):
        rx_samples[i] = arrays_adjusted[i]

    # Plot Rx time domain after gain calibration

    axs[1].plot(t, np.real(rx_samples[0]), label="Ch0 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[0]), label="Ch0 Q (Imag)")

    axs[1].plot(t, np.real(rx_samples[1]), label="Ch1 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[1]), label="Ch1 Q (Imag)")

    axs[1].plot(t, np.real(rx_samples[2]), label="Ch2 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[2]), label="Ch2 Q (Imag)")

    axs[1].plot(t, np.real(rx_samples[3]), label="Ch3 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[3]), label="Ch3 Q (Imag)")

    axs[1].legend()
    axs[1].grid(True)
    axs[1].set_title("Rx time domain after Gain Calibration")
    axs[1].set_xlabel("Time [seconds]")
    axs[1].set_ylabel("Amplitude [LSB]")

    # Stop transmitting
    sdrs.tx_destroy_buffer()

    plt.legend(loc="upper left")
    plt.tight_layout()
    print("Application level gain calibration done.")
    print("Close the plot to continue...")
    plt.show()


def do_cal_phase(sdrs):
    # Configure jupiter and load calibration constants from file
    jupiter_init(sdrs)

    ############################################################################################################
    # Create and plot a complex sinusoid #######################################################################
    ############################################################################################################

    # Calculate time values
    t = np.arange(config.num_samps) / config.sample_rate
    # Generate sinusoidal waveform
    phase_shift = -np.pi / 2  # Shift by -90 degrees
    tx_samples = config.amplitude_discrete * (
        np.cos(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift)
        + 1j * np.sin(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift)
    )

    #     # Plot Tx time domain
    #     plt.figure(1)
    #     plt.plot(t, np.real(tx_samples), label = "I (Real)")
    #     plt.plot(t, np.imag(tx_samples), label = "Q (Imag)")
    #     plt.legend()
    #     plt.title('Tx time domain')
    #     plt.xlabel('Time (seconds)')
    #     plt.ylabel('Amplitude')

    # Calculate Tx spectrum in dBFS
    tx_samples_fft = tx_samples * np.hanning(config.num_samps)
    ampl_tx = np.abs(np.fft.fftshift(np.fft.fft(tx_samples_fft)))
    fft_txvals_iq_dbFS = (
        10 * np.log10(np.real(ampl_tx) ** 2 + np.imag(ampl_tx) ** 2)
        + 20 * np.log10(2 / 2 ** (16 - 1))
        - 20 * np.log10(len(ampl_tx))
    )
    f = np.linspace(
        config.sample_rate / -2, config.sample_rate / 2, len(fft_txvals_iq_dbFS)
    )

    #     # Plot Tx freq domain
    #     plt.figure(2)
    #     plt.plot(f/1e6, fft_txvals_iq_dbFS)
    #     plt.xlabel("Frequency [MHz]")
    #     plt.ylabel("dBFS")
    #     plt.title('Tx FFT')
    #
    #     # Constellation plot for the transmit data
    #     plt.figure(3)
    #     plt.plot(np.real(tx_samples), np.imag(tx_samples), '.')
    #     plt.xlabel("I (Real) Sample Value")
    #     plt.ylabel("Q (Imag) Sample Value")
    #     plt.grid(True)
    #     plt.title('Constellation Plot Tx')
    ################################################################
    ################################################################

    ################################################################
    # Call Tx function to start transmission #######################
    ################################################################
    sdrs.primary.tx(tx_samples)
    ################################################################
    ################################################################

    time.sleep(1)  # wait for internal calibrations
    # Clear buffer just to be safe
    for i in range(0, 2):
        raw_data = sdrs.rx()
        print(str(raw_data))

    ################################################################
    # Call Rx function to receive transmission and plot the data####
    ################################################################
    # Receive and plot time domain data before calibration
    rx_samples = sdrs.rx()
    print(sdrs.rx())

    # Adjust Gain
    rx_samples = adjust_gain(
        sdrs, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
    )

    # Time values
    t = np.arange(config.num_samps) / config.sample_rate

    # Plot Rx time domain before phase calibration
    fig, axs = plt.subplots(nrows=2, sharex=False, figsize=(10, 8))
    # Full screen plot
    manager = plt.get_current_fig_manager()
    try:
        manager.window.attributes("-zoomed", True)
    except AttributeError:
        try:
            manager.window.showMaximized()
        except:
            print("Fullscreen not supported.")

    axs[0].plot(t, np.real(rx_samples[0]), label="Ch0 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[0]), label="Ch0 Q (Imag)")

    axs[0].plot(t, np.real(rx_samples[1]), label="Ch1 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[1]), label="Ch1 Q (Imag)")

    axs[0].plot(t, np.real(rx_samples[2]), label="Ch2 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[2]), label="Ch2 Q (Imag)")

    axs[0].plot(t, np.real(rx_samples[3]), label="Ch3 I (Real)")
    axs[0].plot(t, np.imag(rx_samples[3]), label="Ch3 Q (Imag)")

    axs[0].legend()
    axs[0].grid(True)
    axs[0].set_title("Rx time domain before Phase Calibration")
    axs[0].set_xlabel("Time [seconds]")
    axs[0].set_ylabel("Amplitude [LSB]")

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
        rx_samples = sdrs.rx()
        print("Iteration " + str(i) + ":")
        print(
            "Ph Diff Between ch0 and ch1: "
            + str(measure_phase_degrees(rx_samples[0], rx_samples[1]))
        )
        ph_diff_ch0_minus_ch1.append(
            measure_phase_degrees(rx_samples[0], rx_samples[1])
        )
        print(
            "Ph Diff Between ch0 and ch2: "
            + str(measure_phase_degrees(rx_samples[0], rx_samples[2]))
        )
        ph_diff_ch0_minus_ch2.append(
            measure_phase_degrees(rx_samples[0], rx_samples[2])
        )
        print(
            "Ph Diff Between ch0 and ch3: "
            + str(measure_phase_degrees(rx_samples[0], rx_samples[3]))
        )
        ph_diff_ch0_minus_ch3.append(
            measure_phase_degrees(rx_samples[0], rx_samples[3])
        )
        sum_ph_diff_ch0_minus_ch1 += ph_diff_ch0_minus_ch1[i]
        sum_ph_diff_ch0_minus_ch2 += ph_diff_ch0_minus_ch2[i]
        sum_ph_diff_ch0_minus_ch3 += ph_diff_ch0_minus_ch3[i]

    # Calculate average for each phase difference:
    avg_ph_diff_ch0_minus_ch1 = sum_ph_diff_ch0_minus_ch1 / repeat_ph_calculations
    avg_ph_diff_ch0_minus_ch2 = sum_ph_diff_ch0_minus_ch2 / repeat_ph_calculations
    avg_ph_diff_ch0_minus_ch3 = sum_ph_diff_ch0_minus_ch3 / repeat_ph_calculations

    sdrs.pcal = [
        avg_ph_diff_ch0_minus_ch1,
        avg_ph_diff_ch0_minus_ch2,
        avg_ph_diff_ch0_minus_ch3,
    ]
    print("pcal values: " + str(sdrs.pcal))
    sdrs.save_phase_cal()
    sdrs.load_phase_cal()
    print("pcal values after save: " + str(sdrs.pcal))

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

    # Adjust Gain
    arrays_adjusted = adjust_gain(
        sdrs, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
    )
    for i in range(sdrs.num_rx_elements):
        rx_samples[i] = arrays_adjusted[i]

    # Adjust phase
    rx_samples = adjust_phase(
        sdrs, 0, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
    )

    # Display time plot with phase adjusted
    # Time values
    t = np.arange(config.num_samps) / config.sample_rate

    # Plot Rx time domain after phase calibration
    axs[1].plot(t, np.real(rx_samples[0]), label="Ch0 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[0]), label="Ch0 Q (Imag)")

    axs[1].plot(t, np.real(rx_samples[1]), label="Ch1 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[1]), label="Ch1 Q (Imag)")

    axs[1].plot(t, np.real(rx_samples[2]), label="Ch2 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[2]), label="Ch2 Q (Imag)")

    axs[1].plot(t, np.real(rx_samples[3]), label="Ch3 I (Real)")
    axs[1].plot(t, np.imag(rx_samples[3]), label="Ch3 Q (Imag)")

    axs[1].legend()
    axs[1].grid(True)
    axs[1].set_title("Rx time domain after Phase Calibration")
    axs[1].set_xlabel("Time [seconds]")
    axs[1].set_ylabel("Amplitude [LSB]")

    # Stop transmitting
    sdrs.tx_destroy_buffer()

    plt.legend(loc="upper left")
    plt.tight_layout()
    print("Application level phase calibration done.")
    print("Close the plot to continue...")
    plt.show()


def calibrate_boresight(sdrs):
    print("If you are using antennas, place the trasmitting antenna at boresight")
    input("Press Enter to continue...")
    print("Starting application level phase calibration...")
    do_cal_phase(sdrs)
    print("Starting application level gain calibration...")
    do_cal_gain(sdrs)
