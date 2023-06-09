# Copyright (C) 2020-2021 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

# type: ignore

import csv
import os
import time

import adi
import matplotlib.pyplot as plt
import numpy as np
import scipy.io as sio
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


# Create radio
primary = "ip:10.44.3.39"
secondary = "ip:10.44.3.61"

# Set to False when used without FMCOMMS8
has_fmcomms8 = True

lo_freq = 1000000000
dds_freq = 7000000

primary_jesd = adi.jesd(primary)
secondary_jesd = adi.jesd(secondary)

print("--Connecting to devices")
multi = adi.adrv9009_zu11eg_multi(
    primary, [secondary], primary_jesd, [secondary_jesd], fmcomms8=has_fmcomms8
)

multi._dma_show_arming = False
multi._jesd_show_status = True
multi._jesd_fsm_show_status = True
multi._clk_chip_show_cap_bank_sel = True
multi._resync_tx = True
multi.rx_buffer_size = 2 ** 10

multi.hmc7044_ext_output_delay(0, 1, 0)
multi.hmc7044_ext_output_delay(2, 5, 0)

multi.hmc7044_car_output_delay(2, 2, 0)
multi.hmc7044_car_output_delay(3, 2, 0)

# multi.hmc7044_set_cap_sel([14, 14, 14, 13, 13, 14, 13])

if has_fmcomms8:
    enabled_channels = [0, 2, 4, 6]
    dds_single_tone_channel = 4
else:
    enabled_channels = [0, 1, 2, 3]
    dds_single_tone_channel = 0


multi.primary.rx_enabled_channels = enabled_channels

for secondary in multi.secondaries:
    secondary.rx_enabled_channels = enabled_channels
    secondary.dds_single_tone(dds_freq, 0.2, dds_single_tone_channel)

multi.set_trx_lo_frequency(lo_freq)
multi.primary.dds_single_tone(dds_freq, 0.8)

log = [[], [], [], [], []]

N = 8
C = 5
R = 400

plot_time = True

rx = np.zeros([C, N])
rx_m = np.zeros([C, R])
rx_v = np.zeros([C, R])

if has_fmcomms8:
    chan_desc = [
        "Across Chip (A)",
        "Across FMC8 (A)",
        "Across Chip (B)",
        "Across FMC8 (B)",
        "Across SoM (AB)",
    ]
else:
    chan_desc = [
        "Same Chip (A)",
        "Across Chip (A)",
        "Same Chip (B)",
        "Across Chip (B)",
        "Across SoM (AB)",
    ]

for r in range(R):
    print("\n\nIteration#", r)
    multi._rx_initialized = False

    plot_time = True
    offset = 400

    # [0, 2, 4, 6][0, 2, 4, 6]
    # [0, 1, 2 ,3, 4, 5, 6, 7]
    for i in range(N):
        x = multi.rx()
        rx[0][i] = measure_phase(x[0][offset:], x[1][offset:])
        rx[1][i] = measure_phase(x[0][offset:], x[2][offset:])
        rx[2][i] = measure_phase(x[4][offset:], x[5][offset:])
        rx[3][i] = measure_phase(x[4][offset:], x[6][offset:])
        rx[4][i] = measure_phase(x[0][offset:], x[4][offset:])

    for i in range(C):
        rx_m[i][r] = np.mean(rx[i])
        rx_v[i][r] = np.var(rx[i])
        log[i].append(rx_m[i])

    print("###########")
    for i in range(C):
        print("%s:\t %f" % (chan_desc[i], rx_m[i][r]))
    print("###########")

    if plot_time:
        plt.clf()
        if has_fmcomms8:
            plt.plot(x[0][:1000].real, label="Chan0 SOM A")
            plt.plot(x[1][:1000].real, label="Chan2 SOM A")
            plt.plot(x[2][:1000].real, label="Chan4 SOM A FMC8")
            plt.plot(x[4][:1000].real, label="Chan0 SOM B")
            plt.plot(x[6][:1000].real, label="Chan4 SOM B FMC8")
        else:
            plt.plot(x[0][:1000].real, label="Chan0 SOM A")
            plt.plot(x[1][:1000].real, label="Chan1 SOM A")
            plt.plot(x[2][:1000].real, label="Chan2 SOM A")
            plt.plot(x[4][:1000].real, label="Chan0 SOM B")
            plt.plot(x[6][:1000].real, label="Chan2 SOM B")
        plt.legend()
        plt.draw()
        plt.pause(2)

    plt.clf()
    x = np.array(range(0, r + 1))

    for i in range(C):
        plt.errorbar(x, rx_m[i][x], yerr=rx_v[i][x], label=chan_desc[i])
        # plt.errorbar(x, rx_m[i][x], yerr=0, label=chan_desc[i])
    plt.xlim([-1, x[-1] + 1])
    plt.xlabel("Measurement Index")
    plt.ylabel("Phase Difference (Degrees)")
    plt.legend()
    plt.draw()
    plt.pause(1)

print(log)
fields = []
for i in range(C):
    fields.append(np.sum(log[i]) / len(log[i]))
    fields.append(np.min(log[i]))
    fields.append(np.max(log[i]))
with open(r"log.csv", "a") as f:
    writer = csv.writer(f)
    writer.writerow(fields)
plt.show(block=False)
plt.pause(2)
plt.close()
