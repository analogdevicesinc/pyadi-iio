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

# Create radio
ad9213_transport = adi.ad9213(uri=my_uri,device_name="axi-adrv9213-rx-hpc")
ad9213_phy       = adi.ad9213(uri=my_uri,device_name="ad9213") 

ad9213_transport.rx_buffer_size = 2048

print("CHIP_ID_LSB  phy is:", ad9213_phy.ad9213_register_read(0x4))
print("CHIP_SCRATCH phy is:", ad9213_phy.ad9213_register_read(0xA))
print("Writing 0xAB to 0xA scratch register")
ad9213_phy.ad9213_register_write(0xA,0xAB)
print("CHIP_SCRATCH phy is:", ad9213_phy.ad9213_register_read(0xA))

# rx data 

data = ad9213_transport.rx()

# plot setup

x = np.arange(0, ad9213_transport.rx_buffer_size)

fig, (ch1) = plt.subplots(1, 1)

fig.suptitle("AD9213 Data")
ch1.plot(x, data)
ch1.set_ylabel("Channel 1 amplitude")
ch1.set_xlabel("Samples")
plt.show()

ad9213_transport.rx_destroy_buffer()
