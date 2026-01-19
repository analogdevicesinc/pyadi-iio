# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 15:17:26 2024

@author: Mark Thoren mark.thoren@analog.com
Modified version D.Sloan for AD4x8x Sept. 26th 2025
"""
import numpy
import numpy as np
import genalyzer as gn # note genalyzer for windows/linux must be installed for the .dll
import matplotlib
import matplotlib.pyplot as pl
from matplotlib.ticker import EngFormatter  # for engineering x-axis

from matplotlib.patches import Rectangle as MPRect
from matplotlib import pyplot as plt
from numpy.lib.function_base import average


def genalyzer_data_analysis(data_array, sampling_frequency, noise_bw, odr, fund_freq, qres, fsr, adc_chs=1, do_plots=True, do_histograms=True):
    ax_info_str = [""] * adc_chs
    voltage_array = []
    fft_db = []
    hist_data_array = []
    print("Sampling Frequency: ", sampling_frequency)
    print("Output Data Rate: ", odr)
    for ch_i in range(0, adc_chs):
        print("Channel: ", ch_i)
        if type(data_array) == numpy.ndarray:
            single_channel = True
            data = data_array.astype(np.int32)
        else:
            single_channel = False
            data = data_array[ch_i].astype(np.int32)
        hist_data= data - np.int32(np.average(data))   # Strip out DC
        hist_data_array.append(hist_data)
        print("Data Acquisition Size: ", len(data))
        nfft = len(data)
        navg = 1
        #data_nodc = data - np.average((data))  # Strip out DC
        # voltage = (data * fsr) / (2.0 ** qres)
        voltage_array.append((data * fsr) / (2.0 ** qres))
        # Set up Genalyzer parameters

        code_fmt = gn.CodeFormat.TWOS_COMPLEMENT  # ADC codes format
        rfft_scale = gn.RfftScale.DBFS_SIN  # FFT scale
        # window = gn.Window.NO_WINDOW  # FFT window
        window = gn.Window.BLACKMAN_HARRIS  # FFT window

        ssb_fund = 4  # Single side bin fundamental
        ssb_rest = 5
        # If we are not windowing then choose the closest coherent bin for fundamental
        if gn.Window.NO_WINDOW == window:
            # fund_freq = gn.coherent(nfft, sampling_frequency, fund_freq)
            fund_freq = gn.coherent(nfft, sampling_frequency, fund_freq)
            ssb_fund = 0
            ssb_rest = 0

        # Compute FFT
        fft_cplx = gn.rfft(np.array(data), qres, navg, nfft, window, code_fmt, rfft_scale)
        # Compute frequency axis
        #freq_axis = gn.freq_axis(nfft, gn.FreqAxisType.REAL, sampling_frequency)
        freq_axis = gn.freq_axis(nfft, gn.FreqAxisType.REAL, odr) # for overampled ADC
        # Compute FFT in db
        fft_db.append(gn.db(fft_cplx))

        # Fourier analysis configuration
        key = 'fa'
        gn.mgr_remove(key)
        gn.fa_create(key)
        gn.fa_analysis_band(key, "fdata*0.0", "fdata*1.0")
        gn.fa_fixed_tone(key, 'A', gn.FaCompTag.SIGNAL, fund_freq, ssb_fund)
        gn.fa_hd(key, 4)
        gn.fa_ssb(key, gn.FaSsb.DEFAULT, ssb_rest)
        gn.fa_ssb(key, gn.FaSsb.DC, -1)
        gn.fa_ssb(key, gn.FaSsb.SIGNAL, -1)
        gn.fa_ssb(key, gn.FaSsb.WO, -1)
        gn.fa_fsample(key, sampling_frequency)

        print("#########################")
        print("### Genalyzer Results ###")
        print("#########################")

        # print(gn.fa_preview(key, False))

        # Fourier analysis results
        fft_results = gn.fft_analysis(key, fft_cplx, nfft)
        # compute THD. Double-check the math, thd_rss is with respect to full-scale
        # so subtracting full-scale amplitude
        thd = 20 * np.log10(fft_results['thd_rss']) # - fft_results['A:mag_dbfs']
        # Convert the NSD to nV/sqrt(Hz)
        vref_rms = (fsr/(2*np.sqrt(2))) # careful here, this is making assumptions on the Vref and fsr ToDo: input Vref and Gain instead of fsr?
        nsd_volts = np.sqrt((vref_rms**2)*(10**(fft_results['nsd']/10)))*1e9 # report result in nV/sqrt(Hz)
        if ch_i == 0:
            ch_id = "A"
        else: ch_id = "B"
        ax_info_str[ch_i] = (
            "{:<14}\n"
            "{}{}{}\n"
            "{:<14}\n"
            "{:<14} {:<8.4f} {:<8}\n"
            "{:<14} {:<8.4f} {:<8}\n"
            "{:<14} {:<8.4f} {:<8}\n"
            "{:<14} {:<8.4f} {:<8}\n"
            "{:<14} {:<8.3f} {:<8}\n"
            "{:<14} {:<8.0f} {:<8}\n"
            "{:<14} {:<8.0f} {:<8}\n"
            "{:<14} {:<8.5f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.1f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14}\n"
            "{:<14}\n"
            "{:<14} {:<8.1f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.4f} {:<8}\n"
            "{:<14}\n"
            "{:<14}\n"
            "{:<14} {:<8.0f} {:<8}\n"
            "{:<14} {:<8.3f} {:<8}\n"
            "{:<14} {:<8}\n"
            "{:<14}\n"
            "{:<14}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8} {:<8}\n"
            "{:<14}\n"
            "{:<14}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14}\n"
            "{:<14}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
            "{:<14} {:<8.2f} {:<8}\n"
        ).format(
            "",
            "  ========= CHANNEL ",ch_id, " ==========",
            "  ============ ADC =============",
            "  Samp. freq.  :", (fft_results['fsample'] / 1e6), "MHz",
            "  ODR          :", (odr / 1e6), "MSPS",
            "  ADC BW       :", (noise_bw / 1e6), "MHz",
            "  Samp. period :", ((1 / fft_results['fsample']) * 1e6), "μs",
            "  Ref. volt.   :", fsr / 2, "V",
            "  Bits         :", qres, "bits",
            "  Quants       :", (2 ** qres), "lsb",
            "  Lsb          :", (fsr / 2 ** qres * 1e6), "μV",
            "  DYN RNG/SNR  :", fft_results['fsnr'], "dBFS",
            "  THD          :", thd, "dBFS",  # check this
            "  SINAD        :", fft_results['sinad'], "dB",
            "  ENOB         :", ((fft_results['fsnr'] - 1.76) / 6.02), "bits",
            # strictly speaking, should be sinad ,but works better for no signal input cases
            "  SFDR         :", fft_results['sfdr'], "dB",
            "  NSD          :", fft_results['nsd'], "dBFS/Hz",
            "  NSD          :", nsd_volts, "nV/√Hz",
            "",
            "  ======== Input signal ========",
            "  Frequency    :", fft_results['A:freq'], "Hz",
            "  Amplitude    :", fft_results['A:mag_dbfs'], "dBFS",
            "  DC offset    :", (average(voltage_array[ch_i]) * 1e3), "mV",
            "",
            "  ============ FFT =============",
            "  Points       :", fft_results['nfft'], "N",
            "  Freq. res.   :", fft_results['fbin'], "Hz",
            "  Window       :", "Blackman-Harris",
            "",
            "  ========== Harmonics =========",
            "  THD          :", thd, "dBc",
            "  2nd Harm.    :", fft_results['2A:mag_dbfs'], "dBFS",
            "  3rd Harm.    :", fft_results['3A:mag_dbfs'], "dBFS",
            "  4th Harm.    :", fft_results['4A:mag_dbfs'], "dBFS",
            "  5th Harm.    :", " ??? ", "??",
            "",
            "  ========== Spurious =========",
            "  Pk Spur Mag  :", fft_results['wo:mag_dbfs'], "dBFS",
            "  Pk Spur Freq :", fft_results['wo:freq'], "Hz",
            "",
            "  ========== Analysis =========",
            "  DC bins.     :", fft_results['dc:nbins'], "bins",
            "  Drop'd DC BW :", (fft_results['dc:nbins'] * fft_results['fbin']), "Hz",
            "  Signal bins. :", ssb_fund, "bins",
            "  Incl. Sig BW :", (fft_results['fbin'] * ssb_fund), "Hz",
            "  Non-Sig bins :", ssb_rest, "bins",
            "  Non-Sig BW   :", (fft_results['fbin'] * ssb_rest), "Hz"
        )

    ch_a_color = 'C0'
    ch_b_color = 'C7'
    # print(fft_results)
    # Plot FFT
    if do_plots is True:
        plt.figure(figsize=(14, 9.0))
        gs = matplotlib.gridspec.GridSpec(2, 3, width_ratios=[0.6, 1, 0.6])

        # Time domain plot
        plt.subplot(gs[0, 1])
        plt.plot(voltage_array[0], label='Channel A Data', color=ch_a_color)
        if single_channel == False:
            plt.plot(voltage_array[1], label='Channel B Data', color=ch_b_color)
        plt.tick_params(axis="both", labelsize=8)
        plt.grid()
        plt.legend(loc='upper right', fontsize=8)
        plt.title("Time Domain Plot", fontsize=12)
        plt.xlabel("Conversion Results", fontsize=8)
        plt.ylabel("Measured Voltage (V)", fontsize=8)
        formatter0 = EngFormatter(unit='V')
        plt.gca().yaxis.set_major_formatter(formatter0)
        plt.plot(voltage_array[0], label='Differential data', color=ch_a_color)
        if single_channel == False:
            plt.plot(voltage_array[1], label='Differential data', color=ch_b_color)
        # Frequency Domain Plot
        ax_freq = plt.subplot(gs[1, 1])
        ax_freq.grid(which='major', color='#DDDDDD', linewidth=0.9)
        ax_freq.grid(which='minor', color='#EEEEEE', linewidth=0.7)
        ax_freq.grid(zorder=2)
        ax_freq.grid(True, which="both")
        plt.tick_params(axis="both", labelsize=8)
        plt.title("Frequency Spectrum", fontsize=12)
        plt.xlabel("Frequency", fontsize=8)
        plt.ylabel("Magnitude (dB)", fontsize=8)
        ax_freq.plot(freq_axis, fft_db[0], color=ch_a_color, zorder=2, label="Spectrum")
        if single_channel == False:
            ax_freq.plot(freq_axis, fft_db[1], color=ch_b_color, zorder=2, label="Spectrum")
        ax_freq.set(ylabel='dB', ylim=[-180, 0])
        ax_freq.set_xscale('log')
        formatter0 = EngFormatter(unit='Hz')
        ax_freq.xaxis.set_major_formatter(formatter0)

        # Information table "plot" Channel A
        ax_info = plt.subplot(gs[:, 0])
        ax_info.set(xlim=[1, 10], xticks=[], ylim=[0, 10], yticks=[])
        ax_info.text(1, 10, ax_info_str[0], va='top', ha='left', family='monospace')

        # Information table "plot" Channel B
        ax_info = plt.subplot(gs[:, 2])
        ax_info.set(xlim=[1, 10], xticks=[], ylim=[0, 10], yticks=[])
        if single_channel == False:
            ax_info.text(1, 10, ax_info_str[1], va='top', ha='left', family='monospace')

        plt.tight_layout()
        # plt.style.use('bmh')
        plt.show()
    if do_histograms is True:
        # Create histogram with bin size of 1
        plt.hist(hist_data_array[0], bins=range(min(hist_data_array[0]), max(hist_data_array[0]) + 2), edgecolor='black', color=ch_a_color)
        if single_channel == False:
            plt.hist(hist_data_array[1], bins=range(min(hist_data_array[1]), max(hist_data_array[1]) + 2), edgecolor='black', color=ch_b_color)
        # Add labels and title
        plt.xlabel('ADC Code')
        plt.ylabel('Frequency')
        plt.title('Histogram of Codes')

        # Show the plot
        plt.show()
        return