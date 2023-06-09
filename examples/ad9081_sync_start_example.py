# Copyright (C) 2022 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time

import adi
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import signal

dev = adi.ad9081("ip:analog.local")


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


def gen_tone(fc, fs, NN):
    N = NN / 8
    fc = int(fc / (fs / N)) * (fs / N)
    ts = 1 / float(fs)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * fc) * 2 ** 15
    q = np.sin(2 * np.pi * t * fc) * 2 ** 15
    Xn = i + 1j * q
    # Xn = np.pad(Xn, int(NN - N))
    Xn = np.pad(Xn, (0, int(NN - N)), "constant")
    return Xn


# Configure properties
print("--Setting up chip")

dev.powerdown = 0

# Total number of channels
N_RX = len(dev.rx_channel_nco_frequencies)
N_TX = len(dev.tx_channel_nco_frequencies)

# Total number of CDDCs/CDUCs
NM_RX = len(dev.rx_main_nco_frequencies)
NM_TX = len(dev.tx_main_nco_frequencies)

dev._ctx.set_timeout(3000)
dev._rxadc.set_kernel_buffers_count(1)
dev._txdac.set_kernel_buffers_count(2)

# Set NCOs
dev.rx_channel_nco_frequencies = [0] * N_RX
dev.tx_channel_nco_frequencies = [0] * N_TX

dev.rx_main_nco_frequencies = [1000000000] * NM_RX
dev.tx_main_nco_frequencies = [1000000000] * NM_TX

dev.jesd204_fsm_ctrl = "1"  # This will resync the NCOs and all links

dev.rx_main_6dB_digital_gains = [1] * NM_RX
dev.tx_main_6dB_digital_gains = [1] * NM_TX

dev.rx_channel_6dB_digital_gains = [1] * N_RX
dev.tx_channel_6dB_digital_gains = [1] * N_TX

dev.rx_enabled_channels = [0]
dev.tx_enabled_channels = [0]
dev.rx_nyquist_zone = ["odd"] * N_RX

run_plot = False
tx_use_dma = True
do_powerdowns = False

RUNS = 5000
N = 2 ** 12

dev.rx_buffer_size = N
dev.tx_cyclic_buffer = False

fs = int(dev.tx_sample_rate)

dev.dds_single_tone(fs / 10, 0.0, channel=0)

if tx_use_dma:
    iq1 = gen_tone(fs / 20, fs, N)
else:
    # Set single DDS tone for TX on one transmitter
    dev.dds_single_tone(fs / 10, 0.5, channel=0)

# Disable BRAM offload in FPGA
dev.tx_ddr_offload = 0

print("CHIP Version:", dev.chip_version)
print("API  Version:", dev.api_version)

print("TX SYNC START AVAILABLE:", dev.tx_sync_start_available)
print("RX SYNC START AVAILABLE:", dev.rx_sync_start_available)

# dev._rxadc.reg_write(0x4a3, 25)

so = []
po = []

# Collect data
for r in range(RUNS):

    if do_powerdowns:
        dev.powerdown = 1
        dev.powerdown = 0
    else:
        dev.jesd204_fsm_ctrl = "1"

    if dev.jesd204_device_status_check:
        print(dev.jesd204_device_status)

    dev.rx_sync_start = "arm"
    dev.tx_sync_start = "arm"

    if not ("arm" == dev.tx_sync_start == dev.rx_sync_start):
        raise Exception(
            "Unexpected SYNC status: TX "
            + dev.tx_sync_start
            + " RX: "
            + dev.rx_sync_start
        )

    dev.tx_destroy_buffer()
    dev.rx_destroy_buffer()
    dev._rx_init_channels()

    if tx_use_dma:
        dev.tx(iq1)

    dev.tx_sync_start = "trigger_manual"

    if not ("disarm" == dev.tx_sync_start == dev.rx_sync_start):
        raise Exception(
            "Unexpected SYNC status: TX "
            + dev.tx_sync_start
            + " RX: "
            + dev.rx_sync_start
        )

    try:
        x = dev.rx()
    except Exception as e:
        print("Run#", r, " ----------------------------- FAILED:", e)
        continue

    if tx_use_dma:
        (p, s) = measure_phase_and_delay(iq1, x)
        print("Run#", r, "Sample Delay", int(s), "Phase", f"{p:.2f}")
        so.append(s)
        po.append(p)

    if run_plot == True:
        # plt.xlim(350, 450)
        plt.plot(np.real(x), label=str(r), alpha=0.7)
        plt.legend()
        plt.title("MxFE Phase Sync @ " + str(fs / 1000000) + " MSPS")
        plt.draw()
        plt.pause(0.05)
        time.sleep(0.1)

if tx_use_dma and run_plot == True:
    plt.plot(np.real(iq1), label="TX wave", alpha=0.5)
    plt.legend()
    plt.draw()

if tx_use_dma:
    print("\nSample Offsets")
    print(pd.DataFrame(so).describe())
    print("\nPhase Offsets\n")
    print(pd.DataFrame(po).describe())

if run_plot == True:
    plt.show()
