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

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "local:"
print("uri: " + str(my_uri))

# Create contexts

ad9213_transport = adi.ad9213(uri=my_uri,device_name="axi-adrv9213-rx-hpc")
ad9213_phy       = adi.ad9213(uri=my_uri,device_name="ad9213") 
ad4080_dev       = adi.ad4080(uri=my_uri)
gpio_controller  = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")
ltc2664_dev      = adi.ltc2664(uri=my_uri)

# Control the GPIO's

gpio_controller.gpio_ltc2664_clr  = 1
gpio_controller.gpio_ltc2664_ldac = 0
gpio_controller.gpio_ltc2664_tgp  = 0

gpio_controller.gpio_ada4945_disable  = 1
gpio_controller.gpio_adg5419_ctrl     = 1
gpio_controller.gpio_hmc7044_sync_req = 0

gpio_controller.gpio_adrf5203_ctrl0 = 1
gpio_controller.gpio_adrf5203_ctrl1 = 0
gpio_controller.gpio_adrf5203_ctrl2 = 0

# Configure the AD9213 device

ad9213_transport.rx_buffer_size = 8192
ad9213_phy.ad9213_register_write(0x1617,0x01)
ad9213_phy.ad9213_register_write(0x1601,0x01)

# Configure the AD4080 device 

ad4080_dev.rx_buffer_size = 8192

# ad4080_dev.lvds_sync = "enable"

# Configure the LTC2664 device 

ltc2664_dev.voltage0.raw = 32768  

ltc2664_dev.voltage1.raw = 49152 
print(f"ltc2664_dev.voltage1 is {ltc2664_dev.voltage1.volt}")
ltc2664_dev.voltage2.raw = 36045
print(f"ltc2664_dev.voltage2 is {ltc2664_dev.voltage2.volt}")
# rx data 

data_ad9213 = ad9213_transport.rx()
data_ad4080 = ad4080_dev.rx()

# plot setup

t1 = np.arange(0, ad9213_transport.rx_buffer_size)
t2 = np.arange(0, ad4080_dev.rx_buffer_size)
fig, (ch1,ch2) = plt.subplots(1, 2)

fig.suptitle("AD9213 INSTRUMENTATION Data")
ch1.plot(t1, data_ad9213)
ch1.set_ylabel("AD9213 amplitude")
ch2.plot(t2, data_ad4080)
ch2.set_ylabel("AD4080 amplitude")
ch2.set_xlabel("Samples")
plt.show()

ad9213_transport.rx_destroy_buffer()
ad4080_dev.rx_destroy_buffer()