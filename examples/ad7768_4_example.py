# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
from time import sleep

import adi
import matplotlib.pyplot as plt


def display_settings(power_mode, sampling_frequency, filter_type, rx_enabled_channels):
    print("Power Mode: ", power_mode)
    print("Sampling Frequency: ", sampling_frequency)
    print("Filter Type: ", filter_type)
    print("Enabled Channels: ", rx_enabled_channels)


# Optionally pass URI as command line argument,
# else use default ip:analog.local
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = adi.ad7768_4(uri=my_uri, device_name="ad7768-4")
my_adc.rx_buffer_size = 1024

# Set Sample Rate. Options are 1ksps to 256ksps, 1k* power of 2.
# Note that sample rate and power mode are not orthogonal - refer
# to datasheet.
my_adc.sampling_frequency = 8000

# Choose a power mode:
# my_adc.power_mode_avail = [LOW_POWER_MODE, MEDIAN_MODE, FAST_MODE]
my_adc.power_mode = "FAST_MODE"

# Choose a filter type:
# my_adc.filter_type_avail = [WIDEBAND, SINC5]
my_adc.filter_type = "WIDEBAND"

# Choose output format:
my_adc.rx_output_type = "SI"

# Verify settings:
display_settings(
    my_adc.power_mode,
    my_adc.sampling_frequency,
    my_adc.filter_type,
    my_adc.rx_enabled_channels,
)

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
