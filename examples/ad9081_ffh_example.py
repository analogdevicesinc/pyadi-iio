# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


# This example configures and the Rx/Tx frequency hopping NCOs.
# Later these configurations are selected either via SPI registers or by using external GPIO select.

import sys
import time

import adi
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from adi.gen_mux import genmux
from adi.one_bit_adc_dac import one_bit_adc_dac
from scipy import signal


def measure_phase_and_delay(chan0, chan1, window=None):
    assert len(chan0) == len(chan1)
    if window == None:
        window = len(chan0)
    phases = []
    delays = []
    indx = 0
    sections = len(chan0) // window
    for sec in range(sections):
        chan0_tmp = chan0[indx : indx + window]
        chan1_tmp = chan1[indx : indx + window]
        indx = indx + window + 1
        cor = np.correlate(chan0_tmp, chan1_tmp, "full")
        # plt.plot(np.real(cor))
        # plt.plot(np.imag(cor))
        # plt.plot(np.abs(cor))
        # plt.show()
        i = np.argmax(np.abs(cor))
        m = cor[i]
        sample_delay = len(chan0_tmp) - i - 1
        phases.append(np.angle(m) * 180 / np.pi)
        delays.append(sample_delay)
    return (np.mean(phases), np.mean(delays))


uri = "ip:10.44.3.53"

dev = adi.ad9081(uri)
mux_txffh = genmux(uri, device_name="mux-txffh")
mux_rxffh = genmux(uri, device_name="mux-rxffh")
mux_rxnco = genmux(uri, device_name="mux-rxnco")
mux_txnco = genmux(uri, device_name="mux-txnco")

N_NCOS = 16

# Total number of CDDCs/CDUCs
NM_RX = len(dev.rx_main_nco_frequencies)
NM_TX = len(dev.tx_main_nco_frequencies)

dev.tx_main_nco_frequencies = [500000000] * 4

dev.tx_main_ffh_gpio_mode_enable = 0
dev.tx_main_ffh_mode = ["phase_coherent"] * NM_TX

dev.rx_main_ffh_mode = ["instantaneous_update"] * NM_RX
dev.rx_main_ffh_trig_hop_en = [0] * NM_RX

for i in range(N_NCOS):
    dev.rx_main_nco_ffh_index = [i] * NM_RX
    dev.rx_main_nco_frequencies = [500000000 + i * 1000000] * NM_RX

for i in range(31):
    dev.tx_main_ffh_index = [i] * NM_TX
    dev.tx_main_ffh_frequency = [500000000 + i * 1000000] * NM_TX

# Select Rx/Tx NCO channels via register control
if False:
    for _ in range(1000):
        for i in range(N_NCOS):
            dev.rx_main_nco_ffh_select = [i] * NM_RX
            dev.tx_main_nco_ffh_select = [i] * NM_TX
            time.sleep(1)

mux_txnco.select = 0
mux_rxnco.select = 0

# Select Tx FFH NCOs using Tx GPIOs (DAC_NCO_FFHx, DAC_NCO_FFH_STROBE)
if False:
    # select NCO0
    mux_txnco.select = 0
    mux_rxnco.select = 0
    dev.tx_main_ffh_gpio_mode_enable = 1
    dev.rx_main_ffh_gpio_mode_enable = [1] * NM_RX
    for _ in range(1000):
        for i in range(N_NCOS):
            # Tx NCO
            mux_txffh.select = i + 1
            mux_rxffh.select = i
            time.sleep(1)

dev.rx_enabled_channels = [0, 1]
dev.tx_enabled_channels = [0]
dev.rx_nyquist_zone = ["odd"] * NM_RX

dev.rx_buffer_size = 2 ** 12
dev.tx_cyclic_buffer = True

fs = int(dev.tx_sample_rate)

# Set single DDS tone for TX on one transmitter
# dev.dds_single_tone(fs / 100, 0.5, channel=0)

dev.dds_enabled = [1] * 32
dev.dds_frequencies = [fs / 100] * 32
dev.dds_scales = [0.5] * 32

# Loop through 16 Tx/Rx corresponding NCO configuration,
# make sure the spectral peak doesn’t move

dev.tx_main_ffh_gpio_mode_enable = 0
dev.rx_main_ffh_gpio_mode_enable = [0] * NM_RX

N_RUNS = 16

so = [[] * N_RUNS for _ in range(N_NCOS)]
po = [[] * N_RUNS for _ in range(N_NCOS)]

dev._rxadc.set_kernel_buffers_count(1)

for i in range(N_RUNS):
    for r in range(N_NCOS):
        dev.rx_main_nco_ffh_select = [r] * NM_RX
        dev.tx_main_nco_ffh_select = [r] * NM_TX
        x = dev.rx()
        x = dev.rx()

        (p, s) = measure_phase_and_delay(x[0], x[1])
        print("Run#", r, "Sample Delay", int(s), "Phase", f"{p:.2f}")
        so[r].append(s)
        po[r].append(p)

for i in range(N_NCOS):
    print("\nPhase Offsets NCO: ", i)
    print(pd.DataFrame(po[i]).describe())
