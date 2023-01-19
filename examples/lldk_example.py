import sys

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Optionally passs URI as command line argument,
# else use default ip:analog.local

ltc_vref = 2.048
ltc_gain = 0.37 / 4.07
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))



class ltc2387_x4(adi.ltc2387):
      _rx_channel_names = ["voltage0","voltage1","voltage2","voltage3"]
      _rx_data_type = np.int16


# device connections 

ltc2387_adc = ltc2387_x4(my_uri)
ad3552r_0 = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r-0")
ad3552r_1 = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r-1")
voltage_monitor = adi.ad7291(uri=my_uri)
gpio_controller = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")


# gpio values setup

gpio_controller.gpio_pad_adc3 = 1 
gpio_controller.gpio_pad_adc2 = 1 
gpio_controller.gpio_pad_adc1 = 1 
gpio_controller.gpio_pad_adc0 = 1 

gpio_controller.gpio_gpio0_vio = 1 
gpio_controller.gpio_gpio1_vio = 1 
gpio_controller.gpio_gpio2_vio = 1 
gpio_controller.gpio_gpio3_vio = 1 

gpio_controller.gpio_gpio6_vio = 1
gpio_controller.gpio_gpio7_vio = 1


print("GPIO4_VIO state is:",gpio_controller.gpio_gpio4_vio)
print("GPIO5_VIO state is:",gpio_controller.gpio_gpio5_vio)


# voltage measurements

print("Voltage monitor values:")
for i in range(0, len(voltage_monitor.channel)):
    print(
        "Channel : ", voltage_monitor.channel[i].name,
        ": ", voltage_monitor.channel[i].raw * voltage_monitor.channel[i].scale / 1000.0,
        ("Deg. C" if voltage_monitor.channel[i].name == "temp0" else "V"),
    )

# device configurations 

ltc2387_adc.rx_buffer_size = 4096
ltc2387_adc.sampling_frequency = 12000000

ad3552r_0.tx_enabled_channels = [0, 1]
ad3552r_1.tx_enabled_channels = [0, 1]
ad3552r_0.tx_cyclic_buffer = True
ad3552r_1.tx_cyclic_buffer = True

# signal generation

# Sample rate
fs = int(ad3552r_0.sample_rate)
# Signal frequency
fc = 2000
# Number of samples
N = int(fs / fc)
# Period
ts = 1 / float(fs)
# Time array
t = np.arange(0, N * ts, ts)
# Sine generation
samples = np.sin(2 * np.pi * t * fc)
# Get the signal into the positive range because the loopback is single ended 
samples +=1
# Amplitude (full_scale / 2)
samples *= (2 ** 14) - 1

# tx 

ad3552r_0.tx([samples,samples])
ad3552r_1.tx([samples,samples])

# rx 

data = ltc2387_adc.rx()

# plot setup 

x = np.arange(0, ltc2387_adc.rx_buffer_size)
voltage_0 = ( data[0]  * -ltc_vref )  / (ltc_gain * 2 ** 16)
fig, (ch1, ch2, ch3, ch4) = plt.subplots(4, 1)
print("Maximum measured voltage:",voltage_0.max())
print("Minimum measured voltage:",voltage_0.min())
fig.suptitle('LTC 2387 Channels')
ch1.plot(x,voltage_0[0:ltc2387_adc.rx_buffer_size])
ch2.plot(x,voltage_0[ltc2387_adc.rx_buffer_size:  2*ltc2387_adc.rx_buffer_size])
ch3.plot(x,voltage_0[2*ltc2387_adc.rx_buffer_size:3*ltc2387_adc.rx_buffer_size])
ch4.plot(x,voltage_0[3*ltc2387_adc.rx_buffer_size:4*ltc2387_adc.rx_buffer_size])
ch1.set_ylabel('Channel 1 voltage [V]')
ch2.set_ylabel('Channel 2 voltage [V]')
ch3.set_ylabel('Channel 3 voltage [V]')
ch4.set_ylabel('Channel 4 voltage [V]')
ch4.set_xlabel('Samples')
plt.show()