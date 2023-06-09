# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


import sys

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

device_name = "ad4020"
vref = 5.0  # Manually entered, consult eval board manual

# Optionally pass URI as command line argument,
# else use default context manager search
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = adi.ad4020(uri=my_uri)
my_adc.rx_buffer_size = 4096

print("Sample Rate: ", my_adc.sampling_frequency)

data = my_adc.rx()

x = np.arange(0, len(data))
voltage = data * 2.0 * vref / (2 ** 20)
dc = np.average(voltage)  # Extract DC component
ac = voltage - dc  # Extract AC component

plt.figure(1)
plt.clf()
plt.title("AD4020 Time Domain Data")
plt.plot(x, voltage)
plt.xlabel("Data Point")
plt.ylabel("Voltage (V)")
plt.show()

f, Pxx_spec = signal.periodogram(
    ac, my_adc.sampling_frequency, window="flattop", scaling="spectrum"
)
Pxx_abs = np.sqrt(Pxx_spec)

plt.figure(2)
plt.clf()
plt.title("AD4020 Spectrum (Volts absolute)")
plt.semilogy(f, Pxx_abs)
plt.ylim([1e-6, 4])
plt.xlabel("frequency [Hz]")
plt.ylabel("Voltage (V)")
plt.draw()
plt.pause(0.05)

del my_adc
