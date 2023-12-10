import adi
import numpy as np

AD74413R_DAC_MAX_CODE = 8192

dev_uri = "ip:169.254.97.40"

"""
	Possible values:
	- max14906 selected as device: input, output, high_z
	- ad74413r selected as device: high_z, voltage_out, current_out,
				       voltage_in, current_in_ext, current_in_loop,
				       resistance, digital_input, digital_input_loop,
				       current_in_ext_hart, current_in_loop_hart

"""
channel_config = ["voltage_out", "voltage_out", "voltage_out", "resistance"]

# Possible values: 0, 1
channel_enable = [1, 1, 1, 1]

# Possible values: "ad74413r", "max14906"
channel_device = ["ad74413r", "ad74413r", "ad74413r", "ad74413r"]

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

ad74413r = adi.ad74413r(uri=dev_uri)
max14906 = adi.max14906(uri=dev_uri)
adt75 = adi.lm75(uri=dev_uri)
swiot = adi.swiot(uri=dev_uri)

# Rev ID should be 0x8
print("AD74413R rev ID:", ad74413r.reg_read(0x46))

# Channels which may be used to sample data from the AD74413R
print("AD74413R input (ADC) channels:", ad74413r._rx_channel_names)

# Channels which may be used to set DAC values
print("AD74413R output (DAC) channels:", ad74413r._tx_channel_names)

print("ADT75 temperature reading:", adt75() * 62.5)

# Set the sampling rate for the resistance channel to 4800 for faster update 
ad74413r.channel["resistance3"].sampling_frequency = 4800

voltage_dac_scale = ad74413r.channel["voltage0"].scale
voltage_dac_offset = ad74413r.channel["voltage0"].offset

while True:
	# Get the potentiometer's resistance value in Ohms
	resistance = ad74413r.channel["resistance3"].processed / 1000
	red_channel_val = (resistance / 11000) * AD74413R_DAC_MAX_CODE
	ad74413r.channel["voltage0"].raw = red_channel_val

# ad74413r.rx_output_type = "SI"

# The channels from which to sample the data. Should be one of the ADC channels.
# ad74413r.rx_enabled_channels = ["voltage4"]
# The sample rate should be the same as what is set on the device (4800 is the default).

# ad74413r.sample_rate = 4800

# The number of data samples. This may be changed accordingly.
# ad74413r.rx_buffer_size = 4800
# data = ad74413r.rx()

# for _ in range(60 * 24):
# 	data = np.append(data, ad74413r.rx())

# print(data)

# ad74413r.rx_destroy_buffer()
# plt.clf()
# plt.plot(data)
# plt.ylabel("mV")
# plt.show(block=True)
