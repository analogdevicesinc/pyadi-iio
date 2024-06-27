"""Example of using the FFT Sniffer feature of the AD9084 evaluation board."""

import adi
import matplotlib.pyplot as plt
import time

dev = adi.ad9084(uri="ip:192.168.1.215")
fft = dev.fftsniffer_a
fft.sorting_enable = False
fft.fft_mode = "Magnitude"
fft.real_mode = True

bins_freq = fft.get_bins_freq()
bins_freq = [bin / 1e9 for bin in bins_freq]


for _ in range(10):
    bins = fft.capture_fft()

    plt.clf()
    plt.plot(bins_freq, bins)
    plt.ylim([-2, 64])
    plt.grid()
    plt.ylabel("FFT Code")
    plt.xlabel("Frequency [GHz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

print("done")
plt.show()





