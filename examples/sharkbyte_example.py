# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
import fft_analysis
from collections import namedtuple

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.2.1"
print("uri: " + str(my_uri))


hmcad15xx_dev1 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc1_hmcad15xx")
hmcad15xx_dev2 = adi.hmcad15xx(uri=my_uri,device_name="axi_adc2_hmcad15xx")
ad5696_dev     = adi.ad5686(uri=my_uri)
gpio_controller  = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")

gpio_controller.gpio_clk_sel = 0

## DAC2O RFIN1 A1IP4
ad5696_dev.channel[1].volts = 0.0

## DAC3O RFIN4 A2IP1
ad5696_dev.channel[2].volts = 0.0

## DAC4O RFIN2 A2IP4
ad5696_dev.channel[3].volts = 0.0

custom_pattern       = 0x7fff
fixed_test_pattern   = 0x10
ramp_pattern         = 0x40
pattern_disabled     = 0x00

hmcad15xx_dev1.rx_buffer_size = 2**20
hmcad15xx_dev2.rx_buffer_size = 2**20

hmcad15xx_dev1.rx_enabled_channels = [0,1,2,3]
hmcad15xx_dev2.rx_enabled_channels = [0,1,2,3]

print("RX1 rx_enabled_channels: " + str(hmcad15xx_dev1.rx_enabled_channels))
print("RX2 rx_enabled_channels: " + str(hmcad15xx_dev2.rx_enabled_channels))

hmcad15xx_dev1.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
hmcad15xx_dev2.hmcad15xx_register_write(0x42, 0x0000)  # Phase DDR
hmcad15xx_dev1.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev2.hmcad15xx_register_write(0x26, custom_pattern)
hmcad15xx_dev1.hmcad15xx_register_write(0x25, pattern_disabled)
hmcad15xx_dev2.hmcad15xx_register_write(0x25, pattern_disabled)

#input_select_available value: IP1_IN1 IP2_IN2 IP3_IN3

hmcad15xx_dev1.channel[0].input_select = "IP1_IN1"
hmcad15xx_dev1.channel[1].input_select = "IP2_IN2"
hmcad15xx_dev1.channel[2].input_select = "IP3_IN3"
hmcad15xx_dev1.channel[3].input_select = "IP4_IN4"

hmcad15xx_dev2.channel[0].input_select = "IP1_IN1"
hmcad15xx_dev2.channel[1].input_select = "IP2_IN2"
hmcad15xx_dev2.channel[2].input_select = "IP3_IN3"
hmcad15xx_dev2.channel[3].input_select = "IP4_IN4"

capture_data   = hmcad15xx_dev1.rx()
capture_data1  = hmcad15xx_dev2.rx()



fft_results = fft_analysis.perform_fft_analysis(capture_data1[3], hmcad15xx_dev2.sampling_rate, 14)

print(f"Sampling rate being used: {hmcad15xx_dev2.sampling_rate}")
print(f"Data length: {len(capture_data1[3])}")

# Calculate performance metrics
metrics = fft_analysis.calculate_performance_metrics(fft_results)

# Create analysis plot
fig, filename = fft_analysis.create_analysis_plot(capture_data1[3], fft_results, metrics, "hmcad15xx_dev2")

plt.show()

plt.close()  # Close the figure to free memory

# Print results
print(f"FFT analysis saved as: {filename}")
print(f"SNR: {metrics['snr']:.3f} dB, THD: {metrics['thd']:.3f} dBc, SFDR:{metrics['sfdr']:.2f} dBc")



hmcad15xx_dev1.rx_destroy_buffer()
hmcad15xx_dev2.rx_destroy_buffer()