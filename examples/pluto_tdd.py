# Copyright (C) 2019 Analog Devices, Inc.
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

import faulthandler

faulthandler.enable()

# Create radio
sdr = adi.Pluto()

# Configure properties
sdr.rx_rf_bandwidth = 30000000
sdr.rx_lo = 6000000000
sdr.tx_lo = 6000000000
sdr.tx_cyclic_buffer = False
sdr.tx_hardwaregain_chan0 = -30
sdr.gain_control_mode_chan0 = "slow_attack"

# Read properties
print("RX LO %s" % (sdr.rx_lo))


tdd = adi.tdd("ip:192.168.95.1")
tdd.frame_length_ms = 3
tdd.burst_count = 20
tdd.rx_rf_ms = [1, 1.01, 0, 0]
tdd.secondary = False

tdd.en = True

buffer_size = int(2 * 1024*1024)
print("buffer_size:", buffer_size)

# Create a sinewave waveform
fs = int(sdr.sample_rate)
print("sample_rate:", fs)
N = buffer_size
fc = int(3000000 / (fs / N)) * (fs / N)
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 0.01 * (i + 1j * q)
# Send data

sdr.rx_buffer_size = buffer_size

sdr._ctx.set_timeout(30000)

# Collect data
for r in range(20):
    sdr.tx(iq)
    x = sdr.rx()
    plt.clf()
    plt.specgram(x)
    plt.draw()
    plt.pause(0.05)

plt.show()
