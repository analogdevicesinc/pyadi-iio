# Copyright (C) 2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
from datetime import datetime

import adi
import matplotlib.pyplot as plt
import numpy as np
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


def measure_phase(chan0, chan1):
    assert len(chan0) == len(chan1)
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error


def sub_phases(x, y):
    return [e1 - e2 for (e1, e2) in zip(x, y)]


def measure_and_adjust_phase_offset(chan0, chan1, phase_correction):
    assert len(chan0) == len(chan1)
    (p, s) = measure_phase_and_delay(chan0, chan1)
    # print("Across Chips Sample delay: ",s)
    # print("Phase delay: ",p,"(Degrees)")
    # print(phase_correction)
    return (sub_phases(phase_correction, [int(p * 1000)] * 4), s)


dev = adi.QuadMxFE("ip:10.44.3.52", calibration_board_attached=True)

# Number of MxFE Devices
D = len(dev.rx_test_mode)

# Total number of channels
N_RX = len(dev.rx_channel_nco_frequencies["axi-ad9081-rx-3"]) * D
N_TX = len(dev.tx_channel_nco_frequencies["axi-ad9081-rx-3"]) * D

# Total number of CDDCs/CDUCs
NM_RX = len(dev.rx_main_nco_frequencies["axi-ad9081-rx-3"]) * D
NM_TX = len(dev.tx_main_nco_frequencies["axi-ad9081-rx-3"]) * D

# Enable the first RX of each MxFE
RX_CHAN_EN = []
for i in range(N_RX):
    if i % (N_RX / D) == 0:
        RX_CHAN_EN = RX_CHAN_EN + [i]

# In case the channelizers are not used (bypassed) compensate phase offsets using the main NCOs
channelizer_bypass = (
    dev._rxadc.find_channel("voltage0_i").attrs["channel_nco_frequency_available"].value
)
if channelizer_bypass == "[0 1 0]":
    COMPENSATE_MAIN_PHASES = True
else:
    COMPENSATE_MAIN_PHASES = False

# Configure properties
print("--Setting up chip")

# Loop Combined Tx Channels Back Into Combined Rx Path
dev.gpio_ctrl_ind = 1
dev.gpio_5045_v1 = 1
dev.gpio_5045_v2 = 1
dev.gpio_ctrl_rx_combined = 0

# Zero attenuation
dev.rx_dsa_gain = 0

# Set NCOs
dev.rx_channel_nco_frequencies = [0] * N_RX
dev.tx_channel_nco_frequencies = [0] * N_TX

dev.rx_main_nco_frequencies = [1000000000] * NM_RX
dev.tx_main_nco_frequencies = [3000000000] * NM_TX

dev.rx_enabled_channels = RX_CHAN_EN
dev.tx_enabled_channels = [1] * N_TX
dev.rx_nyquist_zone = ["even"] * NM_TX

dev.rx_buffer_size = 2 ** 12
dev.tx_cyclic_buffer = True

fs = int(dev.tx_sample_rate["axi-ad9081-rx-3"])

# Set single DDS tone for TX on one transmitter
dev.dds_single_tone(fs / 50, 0.9, channel=0)

phases_a = []
phases_b = []
phases_c = []
phases_d = []

so_a = []
so_b = []
so_c = []
so_d = []

run_plot = True

for i in range(10):
    dev._rxadc.attrs["multichip_sync"].value = "10"
    if COMPENSATE_MAIN_PHASES:
        dev.rx_main_nco_phases = [0] * NM_RX
        rx_nco_phases = dev.rx_main_nco_phases
    else:
        dev.rx_channel_nco_phases = [0] * N_RX
        rx_nco_phases = dev.rx_channel_nco_phases

    for r in range(2):
        # Collect data
        x = dev.rx()
        rx_nco_phases["axi-ad9081-rx-1"], s_b = measure_and_adjust_phase_offset(
            x[0], x[1], rx_nco_phases["axi-ad9081-rx-1"]
        )
        rx_nco_phases["axi-ad9081-rx-2"], s_c = measure_and_adjust_phase_offset(
            x[0], x[2], rx_nco_phases["axi-ad9081-rx-2"]
        )
        rx_nco_phases["axi-ad9081-rx-3"], s_d = measure_and_adjust_phase_offset(
            x[0], x[3], rx_nco_phases["axi-ad9081-rx-3"]
        )
        phase_b = str(rx_nco_phases["axi-ad9081-rx-1"][0] / 1000) + "\t" + str(int(s_b))
        phase_c = str(rx_nco_phases["axi-ad9081-rx-2"][0] / 1000) + "\t" + str(int(s_c))
        phase_d = str(rx_nco_phases["axi-ad9081-rx-3"][0] / 1000) + "\t" + str(int(s_d))
        phases_a.insert(i, rx_nco_phases["axi-ad9081-rx-0"][0] / 1000)
        phases_b.insert(i, rx_nco_phases["axi-ad9081-rx-1"][0] / 1000)
        phases_c.insert(i, rx_nco_phases["axi-ad9081-rx-2"][0] / 1000)
        phases_d.insert(i, rx_nco_phases["axi-ad9081-rx-3"][0] / 1000)
        so_a.insert(i, 0)
        so_b.insert(i, s_b)
        so_c.insert(i, s_c)
        so_d.insert(i, s_d)
        result = (
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "\t"
            + phase_b
            + "\t\t"
            + phase_c
            + "\t\t"
            + phase_d
            + "\n"
        )
        print(result)

        with open("test.txt", "a") as myfile:
            myfile.write(result)

        if run_plot == True & r == 1:
            plt.xlim(0, 100)
            plt.plot(np.real(x[0]), label="(1) reference", alpha=0.7)
            plt.plot(np.real(x[1]), label="(2) phase " + phase_b, alpha=0.7)
            plt.plot(np.real(x[2]), label="(3) phase " + phase_c, alpha=0.7)
            plt.plot(np.real(x[3]), label="(4) phase " + phase_d, alpha=0.7)
            plt.legend()
            plt.title("Quad MxFE Phase Sync @ " + str(fs / 1000000) + " MSPS")
            plt.show()
            print("FYI: Close figure to do next capture")

        dev.rx_destroy_buffer()
        if COMPENSATE_MAIN_PHASES:
            dev.rx_main_nco_phases = rx_nco_phases
        else:
            dev.rx_channel_nco_phases = rx_nco_phases

if True:
    plt.xlim(0, 24)
    plt.plot(phases_a, label="(1) MxFE0 phase", alpha=0.7)
    plt.plot(phases_b, label="(2) MxFE1 phase", alpha=0.7)
    plt.plot(phases_c, label="(3) MxFE2 phase", alpha=0.7)
    plt.plot(phases_d, label="(4) MxFE3 phase", alpha=0.7)
    plt.plot(so_a, label="(1) MxFE0 Samp. Offset", alpha=0.7)
    plt.plot(so_b, label="(2) MxFE1 Samp. Offset", alpha=0.7)
    plt.plot(so_c, label="(3) MxFE2 Samp. Offset", alpha=0.7)
    plt.plot(so_d, label="(4) MxFE3 Samp. Offset", alpha=0.7)
    plt.legend()
    plt.title("Quad MxFE Phase Sync @ " + str(fs / 1000000) + " MSPS")
    plt.show()
    print("FYI: Close figure to do next capture")

input("Press Enter to exit...")
