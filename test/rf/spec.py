from __future__ import division

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


def spec_est(x, fs, ref=2 ** 15, plot=False):

    N = len(x)

    # Apply window
    window = signal.kaiser(N, beta=38)
    # x = multiply(x, window)

    # Use FFT to get the amplitude of the spectrum
    ampl = 1 / N * absolute(fft(x))
    ampl = 20 * log10(ampl / ref + 10 ** -20)

    # FFT frequency bins
    freqs = fftfreq(N, 1 / fs)

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
        plt.plot(fftshift(freqs), fftshift(ampl))
        plt.margins(0.1, 0.1)
        plt.xlabel("Frequency [Hz]")
        plt.tight_layout()
        plt.show()

    return ampl, freqs


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


def sfdr(x, fs=1, ref=2 ** 15, plot=False):
    amp, freqs = spec_est(x, fs=fs, ref=ref, plot=plot)
    amp = fftshift(amp)
    peak_indxs, _ = find_peaks(amp, distance=floor(len(x) * 0.1))

    # Sort peaks
    indxs = argsort(amp[peak_indxs])
    indxs = indxs[::-1]
    peak_indxs = peak_indxs[indxs]
    peak_vals = amp[peak_indxs]

    main = peak_vals[0]
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

    return sfdr


def main():

    # import adi
    # sdr = adi.ad9361()
    # sdr.rx_buffer_size = 2**18
    # sdr.sample_rate = 10000000
    # sdr.dds_single_tone(1000000, 0.1)
    # sdr.tx_lo = 1000000000
    # sdr.rx_lo = 1000000000
    # sdr.gain_control = 'slow_attack'
    # sdr.tx_hardwaregain = -10
    # fs = sdr.sample_rate
    # for k in range(10):
    #     a = sdr.rx()[0]

    # Time is from 0 to 1 seconds, but leave off the endpoint, so
    # that 1.0 seconds is the first sample of the *next* chunk
    fs = 64
    length = 600  # seconds
    N = fs * length
    t = linspace(0, length, num=N, endpoint=False)

    # Generate a sinusoid at frequency f
    f = 10  # Hz
    # a = cos(2 * pi * f * t) * 2 ** 15
    a = exp(1j * 2 * pi * f * t) * 2 ** 15

    amp, freqs = spec_est(a, fs, ref=2 ** 15, plot=True)
    _, ml, vals, locs = find_harmonics(fftshift(amp), fftshift(freqs))
    freqs_s = fftshift(freqs)
    amp_s = fftshift(amp)

    tol = 40
    m = amp_s[ml]
    print("Main", m, freqs_s[ml])
    for p in range(len(locs)):
        if absolute(m - vals[p]) < tol:
            print("Harmonic", p + 1, "too large", vals[p], freqs_s[locs[p]])


if __name__ == "__main__":
    main()
