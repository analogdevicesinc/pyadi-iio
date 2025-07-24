import adi
from adi import swiot
import time
import numpy as np
import matplotlib.pyplot as plt

AD74413R_DAC_MAX_CODE = 8192

dev_uri1 = "ip:192.168.97.41"
"""
	Possible values:
	- max14906 selected as device: input, output, high_z
	- ad74413r selected as device: high_z, voltage_out, current_out,
				       voltage_in, current_in_ext, current_in_loop,
				       resistance, digital_input, digital_input_loop,
				       current_in_ext_hart, current_in_loop_hart

"""

# Setup first SWIOT board
channel_config_1 = ["voltage_in", "voltage_in", "voltage_in", "voltage_in"]

# Possible values: 0, 1
channel_enable_1 = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device_1 = ["ad74413r", "ad74413r", "ad74413r", "ad74413r"]

swiot1 = adi.swiot(uri=dev_uri1)
swiot1.mode = "config"
swiot1 = adi.swiot(uri=dev_uri1)

swiot1.ch0_device   = channel_device_1[0]
swiot1.ch0_function = channel_config_1[0]
swiot1.ch0_enable   = channel_enable_1[0]
swiot1.ch1_device   = channel_device_1[1]
swiot1.ch1_function = channel_config_1[1]
swiot1.ch1_enable   = channel_enable_1[1]
swiot1.ch2_device   = channel_device_1[2]
swiot1.ch2_function = channel_config_1[2]
swiot1.ch2_enable   = channel_enable_1[2]
swiot1.ch3_device   = channel_device_1[3]
swiot1.ch3_function = channel_config_1[3]
swiot1.ch3_enable   = channel_enable_1[3]
swiot1.mode = "runtime"

ad74413r_1 = adi.ad74413r(uri=dev_uri1)
max14906_1 = adi.max14906(uri=dev_uri1)
adt75_1    = adi.lm75(uri=dev_uri1)
swiot1     = adi.swiot(uri=dev_uri1)
swiot1.mode = "runtime"

# Print debug info
print("AD74413R rev ID: ", ad74413r_1.reg_read(0x46))

print("AD74413R input (ADC) channels: ", ad74413r_1._rx_channel_names)

print("AD74413R output (ADC) channels: ", ad74413r_1._tx_channel_names)

# Read loop
try:
    while True:
        voltage_raw = ad74413r_1.channel["voltage3"].raw * ad74413r_1.channel["voltage3"].scale + ad74413r_1.channel["voltage3"].offset
        print(voltage_raw)
        temperature_c  = voltage_raw / 5 - 273.15

        print(f"CH3: {voltage_raw:.1f} mV -> {temperature_c:.2f} C")
        
        print("-" * 40)
        time.sleep(1)
except KeyboardInterrupt:
    print("Stopped.")

