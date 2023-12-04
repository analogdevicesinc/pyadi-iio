# Copyright (C) 2023 Analog Devices, Inc.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#     - Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     - Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in
#       the documentation and/or other materials provided with the
#       distribution.
#     - Neither the name of Analog Devices, Inc. nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#     - The use of this software may or may not infringe the patent rights
#       of one or more patent holders.  This license does not release you
#       from the requirement that you obtain separate licenses from these
#       patent holders to use this software.
#     - Use of the software either in source or binary form, must be run
#       on or directly connected to an Analog Devices Inc. component.
#
# THIS SOFTWARE IS PROVIDED BY ANALOG DEVICES "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, NON-INFRINGEMENT, MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE ARE DISCLAIMED.
#
# IN NO EVENT SHALL ANALOG DEVICES BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, INTELLECTUAL PROPERTY
# RIGHTS, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF
# THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import sys
import adi
import numpy as np
import matplotlib.pyplot as plt
from scipy import fft


my_uri = sys.argv[1] if len(sys.argv) >= 2 else None
plot_en = sys.argv[2] if len(sys.argv) >= 3 else 0

# the device name can be: spi_clasic_ad7984 or spi_engine_ad7984

my_device_name = "spi_engine_ad7984"

my_ad7984 = adi.ad7689(uri=my_uri,device_name=my_device_name)
my_ad7984.rx_enabled_channels = [0]

if my_device_name == "spi_engine_ad7984":
    my_ad7984.rx_buffer_size = 42561
else:
    my_ad7984.rx_buffer_size = 8161

data = my_ad7984.rx()
data = np.delete(data,0)

print("Writing the captured samples into the samples_data_buffer.txt file!")
with open('samples_data_buffer.txt', 'w') as f:
    for samples in data:
        f.write(str(samples))
        f.write('\n')
    f.close()

if plot_en !=0 :
    t = np.arange(0, my_ad7984.rx_buffer_size-1, 1)
    plt.suptitle("AD7984 Samples data")
    plt.plot(t, data)
    plt.xlabel("Samples")
    plt.show()

my_ad7984.rx_destroy_buffer()
print("The samples are in the pyadi-iio/samples_data_buffer.txt file!")






