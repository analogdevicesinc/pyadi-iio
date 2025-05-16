# Copyright (C) 2024 Analog Devices, Inc. All Rights Reserved.
# This software is proprietary and confidential to Analog Devices, Inc. and its licensors.

import math
import time

import ad4080_local_sin_params as sp
import matplotlib  # ds added for grid
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import EngFormatter  # for engineering x axis


def process_adc_raw_data(adc, adc_test_channel, data_raw, sample_count, fs, avg_value):
    data = data_raw.astype(np.int32)

    # Create some empty arrays for later calculations
    data_no_dc = [0] * sample_count
    voltage_meas = [0] * sample_count

    # Setting gain to 1
    gain = 1

    # require 20 or 16 bits for differential mode, if it's 8 bits, then that would be the status channel
    # diff_bits = adc._ctrl.channels[0].data_format.bits
    diff_bits = 20
    # print("ADC Differential Channel bits:", diff_bits)
    # assert (diff_bits == 20) or (diff_bits == 16)

    # this is a fixed value for testing the EVBs
    vref = 3.00

    # Calculate the size of LSBs in voltage units
    vlsb_diff: float = (2 * vref) / (2 ** diff_bits)  # - 1)

    # Converter samples in counts to samples in voltage units
    voltage_diff = [vlsb_diff * i for i in data]

    # Combine DM/CM samples to get actual voltage
    for i in range(0, sample_count):
        voltage_meas[i] = voltage_diff[i] * gain

    data_dc = round(np.average(data))
    print(
        "Input data_dc (Counts):", data_dc, "\nInput data_dc (V):", data_dc * vlsb_diff
    )

    adc_amplitude_adj = 2.0 ** (diff_bits - 1)
    adc_amplitude_peak = max(data) - min(data)
    mag_adj = adc_amplitude_peak / (2 * adc_amplitude_adj)
    mag_adj_db = 20 * np.log10(mag_adj)

    # Removing DC content to avoid spectral leakage
    for i in range(0, sample_count):
        data_no_dc[i] = data[i] - data_dc

    # Implement 7-term Blackman-Harris Window 180dB
    a0 = 0.27105140069342
    a1 = 0.43329793923448
    a2 = 0.21812299954311
    a3 = 0.06592544638803
    a4 = 0.01081174209837
    a5 = 0.00077658482522
    a6 = 0.00001388721735
    t = np.linspace(0, 1, sample_count, False)
    norm = 1

    win = (
        a0
        - a1 * np.cos(2 * np.pi * t)
        + a2 * np.cos(4 * np.pi * t)
        - a3 * np.cos(6 * np.pi * t)
        + a4 * np.cos(8 * np.pi * t)
        - a5 * np.cos(10 * np.pi * t)
        + a6 * np.cos(12 * np.pi * t)
    )

    win = win * norm

    # Compute FFT of filter
    win_fft = (
        np.fft.fft(win, sample_count * 10) / sample_count
    )  # To increase resolution to see lobes
    win_fft_mag = 2 * (np.abs(win_fft[0 : int(sample_count / 2) + 1]))
    win_fft_mag_db = 20 * np.log10(win_fft_mag[1 : int(sample_count / 2) + 1])

    # Find the maximum value and shift everything down
    win_fft_mag_db_max = max(win_fft_mag_db)

    for i in range(0, len(win_fft_mag_db)):
        win_fft_mag_db[i] = win_fft_mag_db[i] - win_fft_mag_db_max

    # Windowed Data
    windowed_data = data_no_dc * win
    win_data_fft = np.fft.fft(windowed_data) / sample_count  # FFT normalized
    win_data_fft_mag = 2 * (np.abs(win_data_fft[0 : int(sample_count / 2) + 1]))
    global freq_domain_magnitude_db
    freq_domain_magnitude_db = 20 * np.log10(
        (win_data_fft_mag[1 : int(sample_count / 2) + 1]) / adc_amplitude_adj
    )
    freq_domain_mag_db_loss = mag_adj_db - max(
        freq_domain_magnitude_db
    )  # Amplitude loss due to windowing application

    for i in range(0, len(freq_domain_magnitude_db)):
        freq_domain_magnitude_db[i] = (
            freq_domain_magnitude_db[i] + freq_domain_mag_db_loss
        )

    freq_array = np.linspace(0, 0.5 * fs / avg_value, int(sample_count / 2), False)
    len_freq_array = len(freq_array)
    freq_array = freq_array[5:len_freq_array]
    freq_domain_magnitude_db = freq_domain_magnitude_db[5:len_freq_array]

    try:
        harmonics, snr, thd, sinad, enob, sfdr, floor = sp.sin_params_ad4080(
            data_no_dc, num_harms=9
        )

        f1_freq = (harmonics[1][1]) * ((fs / avg_value) / sample_count)

        sig_amp = np.sqrt(abs(harmonics[1][0]))
        fund_dbfs = 20 * np.log10(sig_amp / 2 ** (diff_bits - 1))
        f2 = 20 * np.log10((np.sqrt(abs(harmonics[2][0]))) / adc_amplitude_adj)
        f3 = 20 * np.log10((np.sqrt(abs(harmonics[3][0]))) / adc_amplitude_adj)
        f4 = 20 * np.log10((np.sqrt(abs(harmonics[4][0]))) / adc_amplitude_adj)
        f5 = 20 * np.log10((np.sqrt(abs(harmonics[5][0]))) / adc_amplitude_adj)

        # The floor is given in dBc. We add the fundamental to convert to dBFs
        floor += fund_dbfs

        max_code = max(data)
        min_code = min(data)
        bin_width = (fs / avg_value) / sample_count
        snr_adj = snr - fund_dbfs
        thd_calc = 10 * np.log10(
            (10 ** (f2 / 10))
            + (10 ** (f3 / 10))
            + (10 ** (f4 / 10))
            + (10 ** (f5 / 10))
        )
        sinad_calc = -10 * np.log10((10 ** (-snr_adj / 10)) + (10 ** (thd_calc / 10)))
        enob_calc = (sinad_calc - 1.76) / 6.02
        sfdr_adj = sfdr - fund_dbfs

        calculated_parameters = [
            ("Sample Averaging", str(avg_value), "Samples"),
            ("Bin Width", "{0:.3f}".format(round(bin_width, 3)), "Hz"),
            ("F1 Bin", str(harmonics[1][1]), "bin"),
            ("F1 Freq", "{0:.9f}".format(round(f1_freq, 9)), "Hz"),
            ("F1 Amp", "{0:.6f}".format(round(fund_dbfs, 6)), "dBFS"),
            ("F2 Amp", "{0:.2f}".format(round(f2, 2)), "dBFS"),
            ("F3 Amp", "{0:.2f}".format(round(f3, 2)), "dBFS"),
            ("F4 Amp", "{0:.2f}".format(round(f4, 2)), "dBFS"),
            ("F5 Amp", "{0:.2f}".format(round(f5, 2)), "dBFS"),
            ("SNR_FS", "{0:.2f}".format(round(snr_adj, 2)), "dB"),
            ("SINAD", "{0:.2f}".format(round(sinad_calc, 2)), "dB"),
            ("THD", "{0:.2f}".format(round(thd_calc, 2)), "dB"),
            ("SFDR", "{0:.2f}".format(round(sfdr_adj, 2)), "dB"),
            ("ENOB", "{0:.2f}".format(round(enob_calc, 2)), "bits"),
            ("Max", str(max_code), "bits"),
            ("Min", str(min_code), "bits"),
            ("DC Level", str(data_dc), "bits"),
            ("Floor", "{0:.2f}".format(round(floor, 2)), "dBFS"),
        ]

        print("\n**** Start of Information Only - Not Test Criteria ****")
        print(f"{'Parameter' : >20}   {'Value' : <16} {'Unit' : <8}")
        for _param, _val, _unit in calculated_parameters:
            print(f"{_param : >20}   {_val : <16} {_unit : <8}")

        print(
            "Average Measured Voltage value: "
            + "{0:.6f}".format(round(np.mean(voltage_meas), 6))
            + " V"
        )

        print("**** End of Information Only - Not Test Criteria ****\n")

    except Exception as e:
        print("Exception during AC Analysis\nHence no FFT")
        print("Exception Details...\n", e)

    # Create plots
    fig = plt.figure(figsize=(20, 8))
    gs = matplotlib.gridspec.GridSpec(2, 2, width_ratios=[3, 1])
    ax_time = plt.subplot(gs[0, 0])
    plt.plot(voltage_meas, label="Differential data", color="C0")
    # y_ceil = math.ceil(max(voltage_meas))
    # y_floor = math.floor(min(voltage_meas))
    # if abs(y_ceil - y_floor) > 1:
    #     plt.yticks(np.arange(y_floor, y_ceil, 1))
    # else:
    #     plt.yticks(np.arange(y_floor, y_ceil, 0.1))
    plt.tick_params(axis="both", labelsize=15)
    plt.grid()
    plt.legend(loc="upper right", fontsize=12)

    plt.title("Time Domain Plot", fontsize=15)
    plt.xlabel("Conversion Results", fontsize=15)
    plt.ylabel("Measured Voltage (V)", fontsize=15)
    plt.plot(voltage_meas, label="Differential data", color="C0")

    # Frequency plot
    ax_freq = plt.subplot(gs[1, 0])

    ax_freq.grid(which="major", color="#DDDDDD", linewidth=0.9)
    ax_freq.grid(which="minor", color="#EEEEEE", linewidth=0.7)
    ax_freq.grid(zorder=2)
    ax_freq.grid(True, which="both")
    plt.title("Frequency Spectrum", fontsize=15)
    plt.xlabel("Frequency (Hz)", fontsize=15)
    plt.ylabel("Magnitude (dB)", fontsize=15)
    ax_freq.plot(
        freq_array, freq_domain_magnitude_db, color="C0", zorder=2, label="Spectrum"
    )
    ax_freq.set(ylabel="dB", ylim=[-180, 10])
    ax_freq.set_xscale("log")

    formatter0 = EngFormatter(unit="Hz")
    ax_freq.xaxis.set_major_formatter(formatter0)

    #
    #     # Information plot
    ax_info = plt.subplot(gs[:, 1])
    ax_info.set(xlim=[0, 10], xticks=[], ylim=[0, 10], yticks=[])

    ax_info_str = """

    ================ ADC =================
    Sampling freq.   : {adc_freq:.4f}     MHz
    Sampling period  : {adc_prd:.4f}      us
    Reference volt.  : {adc_vref:.4f}     V
    Bits             : {adc_bits}         bits
    Codes            : {adc_quants}
    LSB              : {adc_quant:.2f}     uV
    DYN RNG/SNR      : {adc_snr:.2f}      dBFS
    SINAD            : {adc_sinad:.2f}    dB
    THD              : {adc_thd:.2f}      dB
    ENOB             : {adc_enob:.2f}     bits
    SFDR             : {adc_sfdr:.2f}     dBc
    Noise floor      : {adc_nfloor:.2f}   dBFS

    ========== Input signal ==========
    Frequency        : {sig_freq:.1f}     Hz
    Amplitude        : {sig_dbpeak:.2f}  dBFS
    DC offset        : {sig_dc:.4f}     V

    ============== FFT ===============
    Points           : {fft_n}
    Freq. resolution : {fft_res:.3f} Hz
    Window           : {fft_window}

    ============ Harmonics ===========
    2nd Harm.        : {harm_f2:.2f}    dBFS
    3rd Harm.        : {harm_f3:.2f}    dBFS
    4th Harm.        : {harm_f4:.2f}    dBFS
    5th Harm.        : {harm_f5:.2f}    dBFS


    """.format(
        fft_n=sample_count,
        fft_res=bin_width,
        fft_window="7-Term BH",
        harmonics_str="null",
        sig_freq=f1_freq,
        sig_dbpeak=mag_adj_db,
        sig_dc=np.mean(voltage_meas),
        adc_freq=(fs / 1e6),
        adc_prd=((1 / fs) * 1e6),
        adc_vref=vref,
        adc_bits=diff_bits,
        adc_quants=(2 ** diff_bits),
        adc_quant=(vlsb_diff * 1e6),
        adc_snr=snr_adj,
        adc_thd=thd_calc,
        adc_sinad=sinad_calc,
        adc_enob=enob_calc,
        adc_sfdr=sfdr_adj,
        adc_nfloor=floor,
        harm_f2=f2,
        harm_f3=f3,
        harm_f4=f4,
        harm_f5=f5,
    )
    ax_info.text(1, 9.5, ax_info_str, va="top", ha="left", family="monospace")

    # General plotting settings
    plt.tight_layout()
    plt.style.use("bmh")

    # Show the result
    plt.show()

    return snr_adj, thd_calc, f1_freq, fund_dbfs


def validate_results(data_validation):
    test_results = []
    print("\n**** Start of Test Results and Criteria ****")
    print(f"{'Parameter' : >20}   {'Value' : <16} {'Unit' : <8}")
    for test_type, test_var, min_limit, max_limit in data_validation:
        if (test_var >= min_limit) and (test_var <= max_limit):
            print(f" +++ PASS +++", end="")
            test_results.append(True)
        else:
            print(f" --- FAIL ---", end="")
            test_results.append(False)
        print(
            f"\t{test_type : >8} = {round(test_var, 2) :<8}\tMin = {min_limit :<8}\tMax = {max_limit : <8}"
        )
    print("**** End of Test Results and Criteria ****\n")
    return test_results
