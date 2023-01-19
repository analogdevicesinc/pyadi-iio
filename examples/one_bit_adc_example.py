import sys

import adi
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

# Optionally passs URI as command line argument,
# else use default ip:analog.local

vref = 4.096

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:analog.local"
print("uri: " + str(my_uri))

gpio_controller = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")

gpio_controller.gpio_pad_adc3 = 1 
gpio_controller.gpio_pad_adc2 = 1 
gpio_controller.gpio_pad_adc1 = 1 
gpio_controller.gpio_pad_adc0 = 1 



gpio_controller.gpio_gpio0_vio = 1 
gpio_controller.gpio_gpio1_vio = 1 
gpio_controller.gpio_gpio2_vio = 1 
gpio_controller.gpio_gpio3_vio = 1 

print("gpio_value gpio_gpio0_vio",gpio_controller.gpio_gpio0_vio) 
print("gpio_value gpio_gpio1_vio ",gpio_controller.gpio_gpio1_vio) 
print("gpio_value gpio_gpio2_vio ",gpio_controller.gpio_gpio2_vio) 
print("gpio_value gpio_gpio3_vio ",gpio_controller.gpio_gpio3_vio) 