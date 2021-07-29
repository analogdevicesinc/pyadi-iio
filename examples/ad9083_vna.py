# Copyright (C) 2020 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import time

import adi
import matplotlib.pyplot as plt
from scipy import signal
from numpy.fft import fft, fftfreq, fftshift
from scipy.signal import find_peaks

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
    mean,
    average,
)

def spec_est(x, fs, ref=2 ** 15, plot=False, title=""):

    N = len(x)

    # Apply window
    #window = signal.kaiser(N, beta=38)
    #x = multiply(x, window)

    # Use FFT to get the amplitude of the spectrum
    ampl = 1 / N * absolute(fft(x))
    ampl = 20 * log10(ampl / ref + 10 ** -20)

    # FFT frequency bins
    freqs = fftfreq(N, 1 / fs)

    if plot:
        # Plot signal, showing how endpoints wrap from one chunk to the next
        plt.figure(title)
        plt.subplot(2, 1, 1)
        plt.plot(x.real,  color='green', label='RE', linewidth=1, alpha=0.5)
        plt.plot(x.imag,  color='red', label='IM', linewidth=1, alpha=0.5)
        i_avg = average(x.imag)
        r_avg = average(x.real)
        plt.axhline(y=r_avg, linewidth=1, color='g')
        plt.axhline(y=i_avg, linewidth=1, color='r')
        print (r_avg, i_avg)
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

vna = adi.fmcvna("ip:analog.local")

# Configure properties
print("--Setting up chip")

# ADRF5720
vna.lo_attenuator.attenuation = 6
vna.rfin_attenuator.attenuation = 6

vna.lo_mux.select = 'bypass'
vna.rfin_mux.select = 'd1'
vna.lo.frequency = 3e9

for i in range (0, 8):
    vna.frontend[i].lo_mode = 'x1'
    vna.frontend[i].offset_mode = 'x1'
    vna.frontend[i].forward_gain = 6
    vna.frontend[i].reflected_gain = 6
    vna.frontend[i].if_filter_cutoff = vna.frontend[i].offset_frequency
    print ("ADL5960-", i, "Temperature", vna.frontend[i].temperature, "°C")
    print ("ADL5960-", i, "REG 0x25 =", vna.frontend[i].reg_read(0x25))

#Capture all 32 channels
vna.rx_enabled_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
vna.rx_buffer_size = 2 ** 12
fs = int(vna.rx_sample_rate)

# Collect data
for f in range (int(3e9), int(8e9), int(100e6)):
    vna.lo.frequency = f
    # ADMV8818 should update automatically as long as the LO doubler is not used
    print ("LO   HPF", vna.lo_bpf.high_pass_3db_frequency, "MHz, LPF", vna.lo_bpf.low_pass_3db_frequency, "MHz")
    print ("RFIN HPF", vna.rfin_bpf.high_pass_3db_frequency, "MHz, LPF", vna.rfin_bpf.low_pass_3db_frequency, "MHz")
    for r in range(16):
        i = int(r / 2) + 1
        vna.rfin_mux.select = f"d{i}"
        x = vna.rx()
        if r & 1:
            dir = "Reflected"
        else:
            dir = "Forward"

        spec_est(x[r], fs, plot=True, title=f"{dir} Port-{i} f={f} Hz")
