# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import inspect
import os
import sys

import matplotlib.pyplot as plt
import numpy as np
from adi import cn0579

# Lets try to reuse the ./examples/ad4630/sin_params.py file instead of having
# our own copy. Add path prior to importing sin_params
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
ad4630_dir = os.path.join(parentdir, "ad4630")
sys.path.insert(0, ad4630_dir)

import sin_params  # isort:skip

# from save_for_pscope import save_for_pscope

# Optionally pass URI as command line argument,
# else use default ip:analog.local
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

my_adc = cn0579(uri=my_uri)
my_adc.rx_buffer_size = 1024

# Set Sample Rate. Options are 1ksps to 256ksps, 1k* power of 2.
# Note that sample rate and power mode are not orthogonal - refer
# to datasheet.
my_adc.sampling_frequency = 256000

# Choose a power mode:
# my_adc.power_mode_avail = 'LOW_POWER_MODE MEDIAN_MODE FAST_MODE'
my_adc.power_mode = "FAST_MODE"

# Choose a filter type:
# my_adc.filter_type_avail = 'WIDEBAND SINC5'
my_adc.filter_type = "WIDEBAND"

# Choose output format:
# my_adc.rx_output_type = "raw"
my_adc.rx_output_type = "SI"

# Set Shift Voltage:
vshift = 43355
my_adc.shift_voltage0 = vshift
my_adc.shift_voltage1 = vshift
my_adc.shift_voltage2 = vshift
my_adc.shift_voltage3 = vshift

# Current Source for each channel:
my_adc.CC_CH0 = 1
my_adc.CC_CH1 = 1
my_adc.CC_CH2 = 0
my_adc.CC_CH3 = 0

# Verify settings:
print("Power Mode: ", my_adc.power_mode)
print("Sampling Frequency: ", my_adc.sampling_frequency)
print("Filter Type: ", my_adc.filter_type)
print("Enabled Channels: ", my_adc.rx_enabled_channels)
print("Ch0 Shift Voltage: ", my_adc.shift_voltage0)
print("Ch1 Shift Voltage: ", my_adc.shift_voltage1)
print("Ch2 Shift Voltage: ", my_adc.shift_voltage2)
print("Ch3 Shift Voltage: ", my_adc.shift_voltage3)


plt.clf()
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

for ch in my_adc.rx_enabled_channels:
    parameters = sin_params.sin_params(data[ch])
    snr = parameters[1]
    thd = parameters[2]
    sinad = parameters[3]
    enob = parameters[4]
    sfdr = parameters[5]
    floor = parameters[6]
    print("\nChannel " + str(ch))
    print("SNR = " + str(snr))
    print("THD = " + str(thd))
    print("SINAD = " + str(sinad))
    print("ENOB = " + str(enob))
    print("SFDR = " + str(sfdr))
    print("FLOOR = " + str(floor))

plt.show()

# save_for_pscope("Vshift=" + str(my_adc.shift_voltage2) + "_" + str(my_adc.sampling_frequency) + "_cn0579_data.adc" , 24, True, len(data), "DC0000", "LTC1111", data, data, )
