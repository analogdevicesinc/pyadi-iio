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


my_uri = sys.argv[1] if len(sys.argv) >= 2 else "ip:192.168.1.15"
print("uri: " + str(my_uri))

# Create contexts
ad9213_transport = adi.ad9213(uri=my_uri,device_name="axi-adrv9213-rx-hpc")
ad9213_phy       = adi.ad9213(uri=my_uri,device_name="ad9213")
ad4080_dev       = adi.ad4080(uri=my_uri)
gpio_controller  = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")
ltc2664_dev      = adi.ltc2664(uri=my_uri)

ad9213_transport.rx_buffer_size = 2 ** 17
ad4080_dev.rx_buffer_size       = 2 ** 10

# Control the GPIO's

CHIP_SCRATCH = ad4080_dev.ad4080_register_read(0xA)
print("CHIP_SCRATCH phy is:", CHIP_SCRATCH)
if CHIP_SCRATCH !="0xAB":
    gpio_controller.gpio_capture_synced_ctrl  = 0

    gpio_controller.gpio_ltc2664_clr    = 1
    gpio_controller.gpio_ltc2664_ldac   = 0
    gpio_controller.gpio_ltc2664_tgp    = 0

    gpio_controller.gpio_adrf5203_ctrl0 = 1
    gpio_controller.gpio_adrf5203_ctrl1 = 0
    gpio_controller.gpio_adrf5203_ctrl2 = 0

    ad9213_phy.ad9213_register_write(0x1617,0x01)
    ad9213_phy.ad9213_register_write(0x1601,0x01)

    # Configure the LTC2664 device

    ltc2664_dev.voltage0.raw = 32768
    ltc2664_dev.voltage1.raw = 49152
    ltc2664_dev.voltage2.raw = 36045

    gpio_controller.gpio_ada4945_disable  = 1
    gpio_controller.gpio_adg5419_ctrl     = 1

    gpio_controller.gpio_hmc7044_sync_req = 0
    print("AD4080 needs to be synced")
    time.sleep(1)
    ad4080_dev.lvds_sync = "enable"
    ad4080_dev.ad4080_register_write(0xA,0xAB)
else:
    print("AD4080 is already synced")

plt.figure()

data1 = ad9213_transport.rx()
data2 = ad4080_dev.rx()

plt.subplot(2, 1, 1)
plt.plot(data1, label="AD9213")
plt.subplot(2, 1, 2)
plt.plot(data2, label="AD4080")

plt.show()

ad9213_transport.rx_destroy_buffer()
ad4080_dev.rx_destroy_buffer()