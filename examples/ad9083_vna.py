# Copyright (C) 2021 Analog Devices, Inc.
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
from numpy import (
    absolute,
    argmax,
    argsort,
    average,
    cos,
    exp,
    floor,
    linspace,
    log10,
    mean,
    multiply,
    pi,
)
from numpy.fft import fft, fftfreq, fftshift
from scipy import signal
from scipy.signal import find_peaks


def spec_est(x, fs, ref=2 ** 15, plot=False, title=""):

    N = len(x)

    # Apply window
    # window = signal.kaiser(N, beta=38)
    # x = multiply(x, window)

    # Use FFT to get the amplitude of the spectrum
    ampl = 1 / N * absolute(fft(x))
    ampl = 20 * log10(ampl / ref + 10 ** -20)

    # FFT frequency bins
    freqs = fftfreq(N, 1 / fs)

    if plot:
        # Plot signal, showing how endpoints wrap from one chunk to the next
        plt.figure(title)
        plt.subplot(2, 1, 1)
        plt.plot(x.real, color="green", label="RE", linewidth=1, alpha=0.5)
        plt.plot(x.imag, color="red", label="IM", linewidth=1, alpha=0.5)
        i_avg = average(x.imag)
        r_avg = average(x.real)
        plt.axhline(y=r_avg, linewidth=1, color="g")
        plt.axhline(y=i_avg, linewidth=1, color="r")
        print(r_avg, i_avg)
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

# Capture all 32 channels
vna.rx_enabled_channels = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
vna.rx_buffer_size = 2 ** 12
fs = int(vna.rx_sample_rate)

# ADRF5720
vna.lo_attenuator.attenuation = 6
vna.rfin_attenuator.attenuation = 6

vna.lo_mux.select = "bypass"
vna.rfin_mux.select = "d1"
vna.lo.frequency = 3e9

# push shifted DC the out of spectrum
if_frequency = fs

vna.nco0_frequency = if_frequency

for i in range(0, 8):
    vna.frontend[i].lo_mode = "x1"
    vna.frontend[i].offset_mode = "/4"
    vna.frontend[i].if_frequency = if_frequency
    vna.frontend[i].forward_gain = 6
    vna.frontend[i].reflected_gain = 6
    vna.frontend[i].if_filter_cutoff = vna.frontend[i].if_frequency
    print("ADL5960-", i, "Temperature", vna.frontend[i].temperature, "°C")
    print("ADL5960-", i, "REG 0x25 =", vna.frontend[i].reg_read(0x25))


print("AMV8818 modes available:", vna.lo_bpf.mode_available)
print("AMV8818 current mode:", vna.lo_bpf.mode)

vna.lo_bpf.band_pass_bandwidth_3db_frequency = 200
vna.rfin_bpf.band_pass_bandwidth_3db_frequency = 200

vna.gpio_adl5960x_sync = 1
vna.gpio_adl5960x_sync = 0

print("AD9083    NCO0", vna.nco0_frequency, "Hz")
print("ADL5960-1 IF frequency", vna.frontend[0].if_frequency, "Hz")
print("ADL5960-1 OFFSET frequency", vna.frontend[0].offset_frequency, "Hz")
print("ADL5960-1 OFFSET mode", vna.frontend[0].offset_mode)

div = 1

# Collect data
for f in range(int(3e9), int(18e9), int(1000e6)):
    if f > 7e9:
        for i in range(0, 8):
            vna.frontend[i].lo_mode = "x2"
        vna.lo_mux.select = "doubler"
        div = 0.5

    vna.lo.frequency = f * div
    print("ADL5960-", i, "CT2 REG 0x21 =", vna.frontend[0].reg_read(0x21))
    # ADMV8818 should update automatically as long as the LO doubler is not used
    print(
        "LO      HPF",
        vna.lo_bpf.high_pass_3db_frequency,
        "MHz, LPF",
        vna.lo_bpf.low_pass_3db_frequency,
        "MHz",
    )
    print(
        "LO   Center",
        vna.lo_bpf.band_pass_center_frequency,
        "MHz,  BW",
        vna.lo_bpf.band_pass_bandwidth_3db_frequency,
        "MHz",
    )
    print(
        "RFIN    HPF",
        vna.rfin_bpf.high_pass_3db_frequency,
        "MHz, LPF",
        vna.rfin_bpf.low_pass_3db_frequency,
        "MHz",
    )
    print(
        "RFIN Center",
        vna.rfin_bpf.band_pass_center_frequency,
        "MHz,  BW",
        vna.rfin_bpf.band_pass_bandwidth_3db_frequency,
        "MHz",
    )
    for r in range(2):
        i = int(r / 2) + 1
        vna.rfin_mux.select = f"d{i}"
        x = vna.rx()
        if r & 1:
            dir = "Reflected"
        else:
            dir = "Forward"

        spec_est(x[r], fs, plot=True, title=f"{dir} Port-{i} f={f} Hz")
