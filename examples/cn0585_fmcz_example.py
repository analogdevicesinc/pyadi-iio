import sys
import time
from test.eeprom import read_fru_eeprom

import adi
import matplotlib.pyplot as plt
import numpy as np

# Optionally pass URI as command line argument,
# else use default ip:analog.local

adaq23876_vref = 2.048
adaq23876_gain = 0.37 / 4.07
my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:10.48.65.187"
print("uri: " + str(my_uri))


class adaq23876(adi.ltc2387):
    _rx_channel_names = ["voltage0", "voltage1", "voltage2", "voltage3"]
    _rx_data_type = np.int16


# device connections

adaq23876_adc = adaq23876(my_uri)
ad3552r_0 = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r-0")
ad3552r_1 = adi.ad3552r(uri=my_uri, device_name="axi-ad3552r-1")
voltage_monitor = adi.ad7291(uri=my_uri)
gpio_controller = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")

# reading data from eeprom

print("############# EEPROM INFORMATION ############")
read_fru_eeprom(my_uri)
print("#############################################")

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

print("GPIO4_VIO state is:", gpio_controller.gpio_gpio4_vio)
print("GPIO5_VIO state is:", gpio_controller.gpio_gpio5_vio)

# voltage measurements

print("Voltage monitor values:")
print("Temperature: ", voltage_monitor.temp0(), " C")
print("Channel 0: ", voltage_monitor.voltage0(), " millivolts")
print("Channel 1: ", voltage_monitor.voltage1(), " millivolts")
print("Channel 2: ", voltage_monitor.voltage2(), " millivolts")
print("Channel 3: ", voltage_monitor.voltage3(), " millivolts")
print("Channel 4: ", voltage_monitor.voltage4(), " millivolts")
print("Channel 5: ", voltage_monitor.voltage5(), " millivolts")
print("Channel 6: ", voltage_monitor.voltage6(), " millivolts")
print("Channel 7: ", voltage_monitor.voltage7(), " millivolts")

# device configurations

# ####################     AXI REGISTERS READ/WRITE ############################

hdl_dut_write_channel = adi.mwpicore(uri=my_uri, device_name="mwipcore0:mmwr-channel0")
hdl_dut_read_channel = adi.mwpicore(uri=my_uri, device_name="mwipcore0:mmrd-channel1")

if hdl_dut_write_channel.check_matlab_ip() :
    hdl_dut_write_channel.axi4_lite_register_write(0x100, 0x1)
 

if hdl_dut_write_channel.check_matlab_ip():
    reg_value = hdl_dut_read_channel.axi4_lite_register_read(0x108)
    print("AXI4-Lite 0x104 register value:", reg_value)

    
##############################################################################

adaq23876_adc.rx_buffer_size = 1000
adaq23876_adc.sampling_frequency = 15000000

ad3552r_0.tx_enabled_channels = [0, 1]
ad3552r_1.tx_enabled_channels = [0, 1]
ad3552r_0.tx_cyclic_buffer = True
ad3552r_1.tx_cyclic_buffer = True

# signal generation
fs = int(ad3552r_0.sample_rate)
# Signal frequency
fc = 80000
# Number of samples
N = int(fs / fc)
# Period
ts = 1 / float(fs)
# Time array
t = np.arange(0, N * ts, ts)
# Sine generation
samples = np.sin(2 * np.pi * t * fc)
# Amplitude (full_scale / 2)
samples *= (2 ** 15) - 1
# Offset (full_scale / 2)
samples += 2 ** 15
# conversion to unsigned int and offset binary
samples = np.uint16(samples)
samples = np.bitwise_xor(32768, samples)
# tx
print("Sampling rate is:", ad3552r_0.sample_rate)

# available options: "0/2.5V", "0/5V", "0/10V", "-5/+5V", "-10/+10V"

ad3552r_0.output_range = "-10/+10V"
ad3552r_1.output_range = "-10/+10V"


# available options:"adc_input", "dma_input", "ramp_input"

ad3552r_0.input_source = "adc_input"
ad3552r_1.input_source = "adc_input"

print("input_source:dac0:", ad3552r_0.input_source)
print("input_source:dac1:", ad3552r_1.input_source)

# DAC 1 has to be updated and started first and then DAC0 in order to have
# synchronized data between devices

ad3552r_1.tx([samples, samples])
ad3552r_0.tx([samples, samples])

# available options:"start_stream_synced", "start_stream", "stop_stream"

ad3552r_1.stream_status = "start_stream_synced"
ad3552r_0.stream_status = "start_stream_synced"

# rx data

data = adaq23876_adc.rx()

# plot setup

x = np.arange(0, adaq23876_adc.rx_buffer_size)

voltage_0 = (data[0] * -adaq23876_vref) / (adaq23876_gain * 2 ** 16)
fig, (ch1) = plt.subplots(1, 1)

fig.suptitle("ADAQ23876 Channel 1")
ch1.plot(x, voltage_0[0 : adaq23876_adc.rx_buffer_size])
ch1.set_ylabel("Channel 1 voltage [V]")
ch1.set_xlabel("Samples")
plt.show()

ad3552r_1.stream_status = "stop_stream"
ad3552r_0.stream_status = "stop_stream"

ad3552r_1.tx_destroy_buffer()
ad3552r_0.tx_destroy_buffer()
adaq23876_adc.rx_destroy_buffer()


print("An infinite loop which increase the gain from 1 to 10 will start untill you press enter")
gain = 0
while True:
    if gain <=10 :
        gain = gain + 1
    else :
        gain =1
    if hdl_dut_write_channel.check_matlab_ip() :
        hdl_dut_write_channel.axi4_lite_register_write(0x100, gain)
    if hdl_dut_write_channel.check_matlab_ip() :
        reg_value = hdl_dut_read_channel.axi4_lite_register_read(0x108)
        print("Gain value is", reg_value)

    ad3552r_1.tx([samples,samples])
    ad3552r_0.tx([samples,samples])
    ad3552r_1.stream_status = "start_stream_synced"
    ad3552r_0.stream_status = "start_stream_synced"

    user_input = input("Enter 'exit' to quit the loop: ")
    print("You entered:", user_input)
    if user_input.lower() == 'exit':
        ad3552r_1.stream_status = "stop_stream"
        ad3552r_0.stream_status = "stop_stream"
        ad3552r_1.tx_destroy_buffer()
        ad3552r_0.tx_destroy_buffer()
        break 

    ad3552r_1.stream_status = "stop_stream"
    ad3552r_0.stream_status = "stop_stream"
    ad3552r_1.tx_destroy_buffer()
    ad3552r_0.tx_destroy_buffer()



  


