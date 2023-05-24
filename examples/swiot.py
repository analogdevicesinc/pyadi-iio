import adi
import matplotlib.pyplot as plt
import numpy as np

dev_uri = "ip:swiot.local"

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
max14906.channel["voltage3"].raw = 0

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

# Plot the data. The Y scale is in mV.
plt.clf()
# plt.plot(data)
# plt.ylabel("mV")
# plt.show(block=True)

counts, bins = np.histogram(data)
plt.stairs(counts, bins)
plt.show(block=True)

