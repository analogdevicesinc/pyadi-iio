import adi
import matplotlib.pyplot as plt
import numpy as np
import time

dev_uri = "ip:swiot.local"

"""
	Possible values:
	- max14906 selected as device: input, output, high_z
	- ad74413r selected as device: high_z, voltage_out, current_out,
				       voltage_in, current_in_ext, current_in_loop,
				       resistance, digital_input, digital_input_loop,
				       current_in_ext_hart, current_in_loop_hart

"""
channel_config = ["voltage_in", "resistance", "input", "output"]

# Possible values: 0, 1
channel_enable = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device = ["ad74413r", "ad74413r", "max14906", "max14906"]

swiot = adi.swiot(uri=dev_uri)
swiot.mode = "config"
swiot = adi.swiot(uri=dev_uri)

swiot.ch0_device = channel_device[0]
swiot.ch0_function = channel_config[0]
swiot.ch0_enable = channel_enable[0]
swiot.ch1_device = channel_device[1]
swiot.ch1_function = channel_config[1]
swiot.ch1_enable = channel_enable[1]
swiot.ch2_device = channel_device[2]
swiot.ch2_function = channel_config[2]
swiot.ch2_enable = channel_enable[2]
swiot.ch3_device = channel_device[3]
swiot.ch3_function = channel_config[3]
swiot.ch3_enable = channel_enable[3]
swiot.mode = "runtime"

time.sleep(3)

swiot = adi.swiot(uri=dev_uri)
ad74413r = adi.ad74413r(uri=dev_uri)
max14906 = adi.max14906(uri=dev_uri)
adt75 = adi.lm75(uri=dev_uri)

# Rev ID should be 0x8
print("AD74413R rev ID:", ad74413r.reg_read(0x46))

print("AD74413R input (ADC) channels:", ad74413r._rx_channel_names)
print("AD74413R output (DAC) channels:", ad74413r._tx_channel_names)

# Write the raw value for a DAC channel. This is the raw code.
# ad74413r.channel["voltage0"].raw = 0

# Reading channel attributes for AD74413R.
print("AD74413R voltage0 raw:", ad74413r.channel["voltage0"].raw)
print("AD74413R voltage0 scale:", ad74413r.channel["voltage0"].scale)
print("AD74413R voltage0 offset:", ad74413r.channel["voltage0"].offset)

print("MAX14906 input channels:", max14906._rx_channel_names)
print("MAX14906 output channels:", max14906._tx_channel_names)

# Setting the output value of MAX14906 channel (0 or 1)
max14906.channel["voltage3"].raw = 1

# Reading the value of a MAX14906 channel. It's the same for either input or output channels.
print("MAX14906 channel 3 value:", max14906.channel["voltage3"].raw)

# Reading temperature data from the ADT75 (degrees Celsius).
print("ADT75 temperature reading:", adt75() * 62.5)

# Signed integer data type. This is valid for any channel (leave this line like that).
ad74413r.rx_output_type = "SI"

# The channels from which to sample the data. Should be one of the ADC channels.
ad74413r.rx_enabled_channels = ["voltage0"]

# The sample rate should be the same as what is set on the device (4800 is the default).
ad74413r.sample_rate = 4800

# The number of data samples. This may be changed accordingly.
ad74413r.rx_buffer_size = 4800

# Start the data sampling. Values stored in this array are converted in mV.
data = ad74413r.rx()
ad74413r.rx_destroy_buffer()

# Plot the data. The Y scale is in mV.
plt.clf()
plt.plot(data)
plt.ylabel("mV")
plt.show(block=True)

# Reconfig
swiot.mode = "config"
swiot = adi.swiot(uri=dev_uri)
channel_config[0] = "voltage_in"
channel_config[3] = "high_z"
if swiot.mode == "config":
	swiot.ch0_device = channel_device[0]
	swiot.ch0_function = channel_config[0]
	swiot.ch0_enable = channel_enable[0]
	swiot.ch1_device = channel_device[1]
	swiot.ch1_function = channel_config[1]
	swiot.ch1_enable = channel_enable[1]
	swiot.ch2_device = channel_device[2]
	swiot.ch2_function = channel_config[2]
	swiot.ch2_enable = channel_enable[2]
	swiot.ch3_device = channel_device[3]
	swiot.ch3_function = channel_config[3]
	swiot.ch3_enable = channel_enable[3]
	swiot.mode = "runtime"

	time.sleep(3)

swiot = adi.swiot(uri=dev_uri)
ad74413r = adi.ad74413r(uri=dev_uri)
max14906 = adi.max14906(uri=dev_uri)
adt75 = adi.lm75(uri=dev_uri)
# max14906.channel["voltage3"].raw = 0

print("AD74413R voltage0 raw:", ad74413r.channel["voltage0"].raw)
print("AD74413R voltage0 scale:", ad74413r.channel["voltage0"].scale)
print("AD74413R voltage0 offset:", ad74413r.channel["voltage0"].offset)
