from __future__ import division

import numpy as np
import adi
from numpy import (
    absolute,
    argmax,
    argsort,
    cos,
    exp,
    floor,
    linspace,
    log10,
    multiply,
    pi,
)
from numpy.fft import fft, fftfreq, fftshift
from scipy import signal
from scipy.signal import find_peaks


def spec_est(x, fs, ref=2 ** 15, num_ffts=2, enable_windowing=False, plot=False):

    N = len(x)
    fft_len = int(np.floor(N/num_ffts))
    possible_ffts = num_ffts

    indx = 0
    ampl_ave = np.zeros(fft_len)
    freqs_ave = np.zeros(fft_len)

    for n_fft in range(num_ffts):

        seg = x[indx:indx+fft_len]
        indx += fft_len

        # Apply window
        if enable_windowing:
            window = np.hanning(fft_len)
            seg = multiply(seg, window)

        # Use FFT to get the amplitude of the spectrum
        ampl = 1 / N * absolute(fft(seg))
        ampl = 20 * log10(ampl / ref + 10 ** -20)

        # FFT frequency bins
        freqs = fftfreq(len(ampl), 1 / fs)

        ampl_ave += ampl
        freqs_ave += freqs

    ampl_ave /= num_ffts
    freqs_ave /= num_ffts

    # ampl and freqs for real data
    if not np.iscomplexobj(x):
        ampl_ave = ampl[0 : len(ampl_ave) // 2]
        freqs_ave = freqs_ave[0 : len(freqs_ave) // 2]

    if plot:
        # Plot signal, showing how endpoints wrap from one chunk to the next
        import matplotlib.pyplot as plt

        plt.subplot(2, 1, 1)
        plt.plot(x, ".-")
        plt.plot(1, 1, "r.")  # first sample of next chunk
        plt.margins(0.1, 0.1)
        plt.xlabel("Time [s]")
        # Plot shifted data on a shifted axis
        plt.subplot(2, 1, 2)
        plt.plot(fftshift(freqs_ave), fftshift(ampl_ave))
        plt.margins(0.1, 0.1)
        plt.xlabel("Frequency [Hz]")
        plt.tight_layout()
        plt.show()

    return ampl_ave, freqs_ave


def find_peaks_cust(x, num_peaks=4):

    loc = argmax(x)
    print(x[loc : loc + 10])
    for p in range(1, num_peaks):
        l_loc = loc - 1
        r_loc = loc + 1
        l_peaks = []
        r_peaks = []
        # roll down left
        case = "up"
        while l_loc > 0:
            if case == "up":
                if x[l_loc] > x[l_loc - 1]:
                    # Data trending back up, time to find peak
                    case = "down"
            else:
                if x[l_loc] < x[l_loc - 1]:
                    # peak found
                    l_peaks.append(l_loc - 1)
                    case = "up"
            l_loc = l_loc - 1
        # roll down right
        case = "up"
        while r_loc < len(x):
            if case == "up":
                if x[r_loc - 1] < x[r_loc]:
                    # Data trending back up, time to find peak
                    case = "down"
            else:
                if x[r_loc - 1] > x[r_loc]:
                    # peak found
                    r_peaks.append(r_loc - 1)
                    case = "up"
            r_loc = r_loc + 1
        peaks = [loc] + l_peaks + r_peaks
        return peaks


def measure_peaks(x, num_peaks=4):
    peak_indxs = []
    peak_vals = []
    x_t = x.copy()
    m = min(x_t)
    for indx in range(num_peaks):
        loc = argmax(x_t)
        print(x_t[loc], x[loc], loc)
        peak_vals.append(x_t[loc])
        peak_indxs.append(loc)
        x_t[loc] = m
    return peak_vals, peak_indxs


def measure_peaks_without_center(x, num_peaks=4):
    peak_indxs = []
    peak_vals = []
    x_t = x.copy()
    m = min(x_t)
    main_diff = 700
    indx = 0
    while indx < num_peaks:
        loc = argmax(x_t)
        if indx == 0:
            ml = loc
            peak_vals.append(x_t[loc])
            peak_indxs.append(loc)
            indx += 1
        # print(x_t[loc], x[loc], loc)
        if indx > 0 and absolute(ml - loc) > main_diff:
            peak_vals.append(x_t[loc])
            peak_indxs.append(loc)
            indx += 1
        x_t[loc] = m
    return peak_vals, peak_indxs


def find_harmonics(x, freqs, num_harmonics=6, tolerance=0.01):
    vals, indxs = measure_peaks(x, num_harmonics)
    main = absolute(freqs[indxs[0]])
    main_loc = indxs[0]
    # print("Main",main)
    harmonics_locs = []
    harmonics_vals = []
    lx = len(x)
    dc_loc = floor(lx / 2)
    for indx in range(1, len(vals)):
        if absolute(indx - dc_loc) < (tolerance * lx):
            print("DC ignored", freqs[indxs[indx]])
            continue
        dif = absolute(freqs[indxs[indx]]) % main
        if dif < main * tolerance:
            harmonics_locs.append(indxs[indx])
            harmonics_vals.append(vals[indx])
            # print("Harmonic",freqs[indxs[indx]])
    return main, main_loc, harmonics_vals, harmonics_locs


def find_harmonics_from_main(
    x, freqs, fs, num_harmonics=6, tolerance=0.01, plot=False
):
    """Find harmonic tone magnitudes based on found fundamental"""
    vals, indxs = measure_peaks(x, num_harmonics)
    main = freqs[indxs[0]]
    main_loc = indxs[0]
    # Calculate other harmonic locations
    harmonic_freqz = [main * harmonic for harmonic in range(2, num_harmonics + 2)]
    harmonic_freqz_neg = [main - h for h in harmonic_freqz]
    # print("Main", main)
    # print(f"Estimated harmonics {harmonic_freqz}")
    # print(f"Estimated negative harmonics {harmonic_freqz_neg}")
    harmonics_locs = []
    harmonics_vals = []
    lx = len(x)
    bin_width = fs / lx
    for freq in harmonic_freqz + harmonic_freqz_neg:
        if absolute(freq) < (bin_width / 2):
            print("DC ignored", freq)
            continue
        # Get closest index
        indx = np.argmin(absolute(freqs - freq))
        if absolute(freqs[indx] - freq) < (bin_width / 2):
            # print(f"Harmonic found at {freqs[indx]} with mag {x[indx]}")
            harmonics_locs.append(indx)
            harmonics_vals.append(x[indx])

    if plot:
        import matplotlib.pyplot as plt

        # Plot shifted data on a shifted axis
        plt.plot(freqs, x)
        plt.plot(main, x[main_loc], "+")
        plt.plot(freqs[harmonics_locs], harmonics_vals, "x")
        plt.margins(0.1, 0.1)
        plt.xlabel("Frequency [Hz]")
        plt.tight_layout()
        plt.show()
    
    return main, main_loc, harmonics_vals, harmonics_locs

def find_harmonics_reduced(x, freqs, num_harmonics=6, tolerance=0.01):
    vals, indxs = measure_peaks_without_center(x, num_harmonics)
    main = absolute(freqs[indxs[0]])
    main_loc = indxs[0]
    # print("Main",main)
    harmonics_locs = []
    harmonics_vals = []
    lx = len(x)
    dc_loc = floor(lx / 2)
    for indx in range(1, len(vals)):
        if absolute(indx - dc_loc) < (tolerance * lx):
            print("DC ignored", freqs[indxs[indx]])
            continue
        dif = absolute(freqs[indxs[indx]]) % main
        #dif = int((2*main_loc + lx/2)%lx)
        if dif < main * tolerance:
            harmonics_locs.append(indxs[indx])
            harmonics_vals.append(vals[indx])
            # print("Harmonic",freqs[indxs[indx]])
    return main, main_loc, harmonics_vals, harmonics_locs


def sfdr(x, fs=1, ref=2 ** 15, plot=False):
    amp, freqs = spec_est(x, fs=fs, ref=ref, num_ffts=1, plot=False)
    amp_org = amp
    amp = fftshift(amp)
    peak_indxs, _ = find_peaks(amp, distance=floor(len(x) * 0.05))
    lx = len(x)
    dc_loc = floor(lx/2)
    indxs = argsort(amp[peak_indxs])
    indxs = indxs[::-1]
    peak_indxs = peak_indxs[indxs]
    peak_vals = amp[peak_indxs]

    k=1
    main = peak_vals[0]
    # for indx in peak_indxs:
    #     if absolute(indx - dc_loc) < (0.07 * lx):
    #         #do nothing
    #         k = k+1
    #         print("DC ignored")
    #     else:
    #         next = peak_vals[k]
    next = peak_vals[1]
    
    sfdr = absolute(main - next)

    if plot:
        import matplotlib.pyplot as plt

        plt.subplot(2, 1, 1)
        plt.plot(x, ".-")
        plt.plot(1, 1, "r.")  # first sample of next chunk
        plt.margins(0.1, 0.1)
        plt.xlabel("Time [s]")
        # Plot shifted data on a shifted axis
        plt.subplot(2, 1, 2)
        plt.plot(amp)
        plt.plot(peak_indxs[0:3], amp[peak_indxs[0:3]], "x")
        plt.margins(0.1, 0.1)
        plt.xlabel("Frequency [Hz]")
        plt.tight_layout()
        plt.show()

    return sfdr, amp_org, freqs, peak_vals, peak_indxs, k


def main():

    # import adi

    sdr = adi.ad9361("ip:10.42.0.162")
    sdr.rx_buffer_size = 2 ** 18
    sdr.sample_rate = 10000000
    sdr.dds_single_tone(1000000, 0.1)
    sdr.tx_lo = 1000000000
    sdr.rx_lo = 1000000000
    sdr.gain_control = 'slow_attack'
    sdr.tx_hardwaregain = -10
    sdr.rx_enabled_channels = [0]
    fs = sdr.sample_rate
    for k in range(10):
        a = sdr.rx()

    # Time is from 0 to 1 seconds, but leave off the endpoint, so
    # that 1.0 seconds is the first sample of the *next* chunk
    # fs = 64
    # length = 600  # seconds
    # N = fs * length
    # t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 10  # Hz
    # a = cos(2 * pi * f * t) * 2 ** 15
    # a = exp(1j * 2 * pi * f * t) * 2 ** 15
    print(f"Input shape {a.shape}")

    # fs = sdr.sample_rate

    #amp, freqs = spec_est(a, fs, ref=2 ** 15, plot=True)
    # freqs = np.flip(freqs)
    sfdr(a, fs=fs, ref=2 ** 15, plot=True)
    # _, ml, vals, locs = find_harmonics_from_main(
    #     fftshift(amp), fftshift(freqs), fs, plot=True
    # )

    # freqs_s = fftshift(freqs)
    # amp_s = fftshift(amp)

    tol = 40
    # m = amp_s[ml]
    # print("Main", m, freqs_s[ml])
    # for p in range(len(locs)):
    #     if absolute(m - vals[p]) < tol:
    #         print("Harmonic", p + 1, "too large", vals[p], freqs_s[locs[p]])


if __name__ == "__main__":
    main()
