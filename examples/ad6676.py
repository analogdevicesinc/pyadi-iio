# Copyright (C) 2023 Analog Devices, Inc.
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
import numpy as np
from scipy import signal


def noise_analysis(samples):
    x = []

    while len(x) < samples:
        xn = sdr.rx()
        x = np.append(x, xn)

    print("type x=", type(x), len(x), "type x[0]=", type(x[0]))
    print("Record length (s)", len(x) / fsr)
    mag = np.absolute(x)
    max = np.max(mag)
    print("max =", max)
    print("min =", np.min(mag))
    print("mean =", np.mean(mag))
    rms_of_mag = np.sqrt(np.mean(mag ** 2))
    print("RMS(mag) =", rms_of_mag)
    print("Peak-to-RMS =", 20 * np.log10(max / rms_of_mag), "dB")
    print("")

    plt.hist(mag, 500, density=True, facecolor="g", alpha=0.75)
    plt.title("Histogram of MAG")
    plt.show()


# Create radio
sdr = adi.ad6676("ip:analog.local")

# Configure properties
sdr.rx_enabled_channels = [0]
sdr.rx_buffer_size = 32738

fsr = int(sdr.sampling_frequency)

print("adc_frequency =", int(sdr.adc_frequency) / 1000000, "MHz")
print("sampling_frequency =", fsr / 1000000, "MHz")
print("intermediate_frequency =", int(sdr.intermediate_frequency) / 1000000, "MHz")
print("bandwidth =", int(sdr.bandwidth) / 1000000, "MHz")
print("bw_margin_high =", sdr.bw_margin_high)
print("bw_margin_if =", sdr.bw_margin_if)
print("bw_margin_low =", sdr.bw_margin_low)
print("hardwaregain =", sdr.hardwaregain)
print("scale =", sdr.scale)
print("shuffler_control =", sdr.shuffler_control)
print("shuffler_thresh =", sdr.shuffler_thresh)
print()

if True:
    sdr._rxadc.set_kernel_buffers_count(1)
    sdr.rx_buffer_size = 4194304
    sdr._ctrl.reg_write(0x340, 3)
    print("Enable: slow shuffler", "REG 0x340 =", sdr._ctrl.reg_read(0x340))
    noise_analysis(fsr / 2)  # Collect 0.5 seconds

    sdr._ctrl.reg_write(0x340, 1)
    print("Disable: slow shuffler", "REG 0x340 =", sdr._ctrl.reg_read(0x340))
    noise_analysis(fsr / 2)  # Collect 0.5 seconds

# Collect data
for r in range(20):
    x = sdr.rx()
    f, Pxx_den = signal.periodogram(x, fsr)
    plt.clf()
    plt.semilogy(f, Pxx_den)
    plt.ylim([1e-7, 1e4])
    plt.xlabel("frequency [Hz]")
    plt.ylabel("PSD [V**2/Hz]")
    plt.draw()
    plt.pause(0.05)
    time.sleep(0.1)

plt.show()
