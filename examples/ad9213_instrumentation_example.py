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
from scipy.signal import resample, find_peaks

my_uri = sys.argv[1] if len(sys.argv) >= 2 else "local:"
print("uri: " + str(my_uri))

# Create contexts

primary          = my_uri
ad9213_phy       = adi.ad9213(uri=my_uri,device_name="ad9213")
ad4080_dev       = adi.ad4080(uri=my_uri)
ssh              = adi.sshfs(address=my_uri, username="root", password="analog")
gpio_controller  = adi.one_bit_adc_dac(uri=my_uri, name="one-bit-adc-dac")
ltc2664_dev      = adi.ltc2664(uri=my_uri)
primary_jesd     = adi.jesd(primary)
multi = adi.ad9213_instr(primary, [], primary_jesd, [])


multi._dma_show_arming = False
multi._jesd_show_status = True
multi._jesd_fsm_show_status = True
multi.rx_buffer_size = 2 ** 15

# Control the GPIO's
stdout, stderr = ssh._run(f"busybox devmem 0x44A00068 32 ")
print(stdout)
if stdout == "0x00000000":
    gpio_controller.gpio_ad4080_sync_n  = 1

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
    ad4080_dev.lvds_sync = "enable"
else:
    print("AD4080 is already synced")


data = np.array(multi.rx())

ad4080_interpolated = np.interp(
    np.arange(0, len(data[1]) * 320, 1),
    np.arange(0, len(data[1]) * 320, 320),
    -data[1]
)
ad4080_interpolated = ad4080_interpolated[:32768]
# Upscale ad4080_interpolated to match data[0] amplitude and offset
ad4080_interpolated = ad4080_interpolated * (np.max(data[0]) / np.max(ad4080_interpolated))
ad4080_interpolated = ad4080_interpolated + (np.mean(data[0]) - np.mean(ad4080_interpolated))

cross_corr = np.correlate(data[0], ad4080_interpolated, mode='full')
#
coarse_phase_shift = np.argmax(cross_corr) - (len(ad4080_interpolated) - 1)
print(f"Coarse phase shift: {coarse_phase_shift}")
#
# # Fine-tune the coarse phase shift
fine_tuned_shift = coarse_phase_shift
max_corr_value = cross_corr[coarse_phase_shift + len(ad4080_interpolated) - 1]

for shift in range(coarse_phase_shift - 320, coarse_phase_shift + 321):
    if 0 <= shift < len(cross_corr):
        if cross_corr[shift + len(ad4080_interpolated) - 1] > max_corr_value:
            max_corr_value = cross_corr[shift + len(ad4080_interpolated) - 1]
            fine_tuned_shift = shift

print(f"Fine-tuned phase shift: {fine_tuned_shift}")

plt.figure()
plt.subplot(2, 1, 1)
plt.plot(data[0], label="AD9213")
plt.plot(ad4080_interpolated, label="AD4080")
plt.legend()

plt.subplot(2, 1, 2)
plt.plot(cross_corr, label="Cross corelated signal")
plt.legend()

plt.show()

multi.rx_destroy_buffer()
