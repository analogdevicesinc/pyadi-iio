# Copyright (C) 2022 Analog Devices, Inc.
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


import sys

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

device_name = "ltc2387"
vref = 4.096

# Optionally passs URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = adi.ltc2387(uri=my_uri)
my_adc.rx_buffer_size = 4096
my_adc.sampling_frequency = 10000000

print("Sample Rate: ", my_adc.sampling_frequency)

data = my_adc.rx()

x = np.arange(0, len(data))
voltage = data * 2.0 * vref / (2 ** 18)
dc = np.average(voltage)  # Extract DC component
ac = voltage - dc  # Extract AC component

plt.figure(1)
plt.clf()
plt.title("LTC2387 Time Domain Data")
plt.plot(x, voltage)
plt.xlabel("Data Point")
plt.ylabel("Voltage (V)")
plt.show()

# Flat top window preserves tone amplitude, blackman is better for SNR, THD measurements
f, Pxx_spec = signal.periodogram(
    ac, my_adc.sampling_frequency, window="flattop", scaling="spectrum"
)
Pxx_abs = np.sqrt(Pxx_spec)

plt.figure(2)
plt.clf()
plt.title("LTC2387 Spectrum (Volts absolute)")
plt.semilogy(f, Pxx_abs)
plt.ylim([1e-6, 4])
plt.xlabel("frequency [Hz]")
plt.ylabel("Voltage (V)")
plt.draw()
plt.pause(0.05)

del my_adc
