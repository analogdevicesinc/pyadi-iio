# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import sys

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

device_name = "ltc2387"
vref = 4.096

# Optionally pass URI as command line argument,
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
