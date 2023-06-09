# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
from time import sleep

import matplotlib.pyplot as plt
from adi import ad7768

# Optionally pass URI as command line argument,
# else use default ip:analog.local
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = ad7768(uri=my_uri)
my_adc.rx_buffer_size = 1024

# Set Sample Rate. Options are 1ksps to 256ksps, 1k* power of 2.
# Note that sample rate and power mode are not orthogonal - refer
# to datasheet.
my_adc.sampling_frequency = 8000

# Choose a power mode:
my_adc.power_mode = "FAST_MODE"
# my_adc.power_mode = "MEDIAN_MODE"
# my_adc.power_mode = "LOW_POWER_MODE"

# Choose a filter type:
my_adc.filter_type = "WIDEBAND"
# my_adc.filter_type = "SINC5"

# Choose output format:
# my_adc.rx_output_type = "raw"
my_adc.rx_output_type = "SI"

# Verify settings:
print("Power Mode: ", my_adc.power_mode)
print("Sampling Frequency: ", my_adc.sampling_frequency)
print("Filter Type: ", my_adc.filter_type)
print("Enabled Channels: ", my_adc.rx_enabled_channels)


plt.clf()
sleep(0.5)
data = my_adc.rx()
for ch in my_adc.rx_enabled_channels:
    plt.plot(range(0, len(data[0])), data[ch], label="voltage" + str(ch))
plt.xlabel("Data Point")
if my_adc.rx_output_type == "SI":
    plt.ylabel("Millivolts")
else:
    plt.ylabel("ADC counts")
plt.legend(
    bbox_to_anchor=(0.0, 1.02, 1.0, 0.102),
    loc="lower left",
    ncol=4,
    mode="expand",
    borderaxespad=0.0,
)
plt.pause(0.01)

del my_adc
