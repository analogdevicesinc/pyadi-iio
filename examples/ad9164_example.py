# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
import sys
import adi
import math
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal

url = "local:" if len(sys.argv) == 1 else sys.argv[1]
tx = adi.ad9162(url)
gpio_controller = adi.one_bit_adc_dac(uri=url, name="one-bit-adc-dac")
ssh = adi.sshfs(address=url, username="root", password="analog")

gpio_controller.gpio_dac_ctrl_0 = 1
gpio_controller.gpio_dac_ctrl_1 = 1
gpio_controller.gpio_dac_ctrl_2 = 1
gpio_controller.gpio_dac_ctrl_3 = 1
gpio_controller.gpio_dac_ctrl_4 = 0

tx.tx_cyclic_buffer = True
tx.tx_enabled_channels = [0]
dds_or_dma_signal = 1

#Signal generation

Amp  = 0.5 * 2**16  # -6 dBFS
Freq = 1e9

fs = int(tx.sample_rate)
print(fs)
N_tx = int(fs/Freq)*8
T = N_tx / fs
t = np.linspace(0, T, N_tx)
tx_sig = Amp * np.sin(2 * math.pi * Freq * t)

if dds_or_dma_signal :
    tx.dds_enabled = [1]
    tx.dds_single_tone(Freq,0.5)
else:
    tx.tx(tx_sig)

plt.plot(tx_sig)
plt.show()

if dds_or_dma_signal == 0:
    tx.tx_destroy_buffer()

stdout, stderr = ssh._run(f"busybox devmem 0x{0x84a04000 + 0x0418:02x} 32 0x3")
