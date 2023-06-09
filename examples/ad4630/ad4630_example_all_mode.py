# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import time

import adi
import matplotlib.pyplot as plt
import numpy as np
import sin_params as sp

device_name = "ad4030-24"
fs = 2000000  # Sampling Frequency
N = 65536  # Length of rx buffer


def main():
    """ Instantiate the device and set th parameters."""
    adc = adi.ad4630(
        uri="ip:169.254.92.202", device_name=device_name
    )  # To connect via ip address 169.254.92.202
    adc.rx_buffer_size = N
    adc.sample_rate = fs

    """To switch the device b/w low_power_mode and normal_operating_mode."""
    adc.operating_mode = "normal_operating_mode"

    """sample_averaging is only supported by 30bit mode. and in this mode it cannot be OFF."""
    if adc.output_data_mode == "30bit_avg":
        adc.sample_averaging = 16

    """ Prints Current output data mode"""
    print(adc.output_data_mode)

    """ Differential Channel attributes"""
    adc.chan0.hw_gain = 2
    adc.chan0.offset = 2
    if device_name == "ad4630-24":
        adc.chan1.hw_gain = 2
        adc.chan1.offset = 2

    data = adc.rx()  # Receive the data
    adc.rx_destroy_buffer()  # Destroy the remaining data in buffer

    for ch in range(0, len(data)):
        x = np.arange(0, len(data[ch]))
        plt.figure(
            adc._ctrl.channels[ch]._name
        )  # Using hidden functions in example code is not advised
        plt.plot(x * (100 / fs), data[ch])

    plt.show()

    if adc.output_data_mode == "30bit_avg":
        diff_bits = 30
    elif adc.output_data_mode == "16bit_diff_8bit_cm":
        diff_bits = 16
    else:
        diff_bits = 24

    if adc.output_data_mode == "32bit_test_pattern":
        test_pattern_analysis(data[0])
        if device_name == "ad4630-24":
            test_pattern_analysis(data[1])
    else:
        analysis(diff_bits, data[0])
        if device_name == "ad4630-24":
            if (
                adc.output_data_mode == "16bit_diff_8bit_cm"
                or adc.output_data_mode == "24bit_diff_8bit_cm"
            ):
                analysis(diff_bits, data[2])
            else:
                analysis(diff_bits, data[1])


def analysis(bits, op_data):
    """Does the SNR Analysis and plots FFT"""

    adc_amplitude_adj = 2 ** (bits - 1)  # x**y is same as x^y
    adc_amplitude_peak = max(op_data) - min(op_data)
    mag_adj = adc_amplitude_peak / (2 * adc_amplitude_adj)
    mag_adj_db = 20 * np.log10(mag_adj)

    """SNR Analysis"""
    harmonics, snr, thd, sinad, enob, sfdr, floor = sp.sin_params(op_data)
    f1_freq = (harmonics[1][1]) * (fs / N)

    sig_amp = np.sqrt(abs(harmonics[1][0]))
    fund_dbfs = 20 * np.log10(sig_amp / 2 ** (bits - 1))
    f2 = 20 * np.log10((np.sqrt(abs(harmonics[2][0]))) / adc_amplitude_adj)
    f3 = 20 * np.log10((np.sqrt(abs(harmonics[3][0]))) / adc_amplitude_adj)
    f4 = 20 * np.log10((np.sqrt(abs(harmonics[4][0]))) / adc_amplitude_adj)
    f5 = 20 * np.log10((np.sqrt(abs(harmonics[5][0]))) / adc_amplitude_adj)

    floor += fund_dbfs
    max_code = max(op_data)
    min_code = min(op_data)
    bin_width = fs / N
    snr_adj = snr - fund_dbfs
    thd_calc = 10 * np.log10(
        (10 ** (f2 / 10)) + (10 ** (f3 / 10)) + (10 ** (f4 / 10)) + (10 ** (f5 / 10))
    )
    sinad_calc = -10 * np.log10((10 ** (-snr_adj / 10)) + (10 ** (thd_calc / 10)))
    enob_calc = (sinad_calc - 1.76) / 6.02
    sfdr_adj = sfdr - fund_dbfs

    """ Print the actual and calculated parameters"""
    print("Binwidth = ", bin_width)
    print("SNR (dB) = ", snr)
    print("SNR of Adjacent chan (dB) =", snr_adj)
    print("thd = " + str(thd) + " calculated thd = " + thd_calc)
    print("sfdr = " + str(sfdr) + " adjacent chan sfdr = " + sfdr_adj)
    print("ENOB = " + str(enob) + " calculated ENOB = " + enob_calc)
    print("sinad = " + str(sinad) + " calculated sinad = " + sinad_calc)
    print("Max code = " + str(max_code) + "Min code = " + str(min_code))
    print("Lent of each captured array =", len(op_data))


def test_pattern_analysis(data_op):
    """Perform analysis in 32bit test pattern output data mode."""

    print("32 bit pattern data from CHA = " + hex(data_op[int(N / 2)]))
    print("32 bit pattern data from CHB = " + hex(data_op[int(N / 2)]))
    custom_pattern_data = 0xFADB02EC
    custom_pattern_data_hex = hex(custom_pattern_data)
    custom_pattern_data_hex_3 = "0x" + custom_pattern_data_hex[2:4]
    custom_pattern_data_hex_2 = "0x" + custom_pattern_data_hex[4:6]
    custom_pattern_data_hex_1 = "0x" + custom_pattern_data_hex[6:8]
    custom_pattern_data_hex_0 = "0x" + custom_pattern_data_hex[8:10]
    adc._ctrl.reg_write(0x0026, int(custom_pattern_data_hex_3, 16))
    adc._ctrl.reg_write(0x0025, int(custom_pattern_data_hex_2, 16))
    adc._ctrl.reg_write(0x0024, int(custom_pattern_data_hex_1, 16))
    adc._ctrl.reg_write(0x0023, int(custom_pattern_data_hex_0, 16))


if __name__ == "__main__":
    main()
