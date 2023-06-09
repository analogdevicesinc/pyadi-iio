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
        # plt.plot(chan0_tmp)
        # plt.plot(chan0)
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


def measure_and_adjust_phase_offset(
    chan0, chan1, phase_correction, skip=None, window=None
):
    assert len(chan0) == len(chan1)
    if skip == None:
        skip = 0

    (p, s) = measure_phase_and_delay(chan0[skip:], chan1[skip:], window)
    p = round(p, 2)
    # print("Across Chips Sample delay: ",s)
    # print("Phase delay: ",p,"(Degrees)")
    # print(phase_correction)
    return (sub_phases(phase_correction, [int(p * 1000)] * 4), s)


def adjust_gain(x, skip=None):
    if skip == None:
        skip = 0
    c0 = np.amax(x[0][skip:])
    for i in range(len(x)):
        c1 = np.amax(x[i][skip:])
        x[i] = x[i] * c0.real / c1.real
    return c0.real


primary = "ip:10.44.3.52"
secondary = "ip:10.44.3.55"

primary_jesd = (None,)
secondary_jesd = ([None],)

print("--Connecting to devices")
multi = adi.QuadMxFE_multi(primary, [secondary], primary_jesd, [secondary_jesd])

multi._dma_show_arming = False
multi._jesd_show_status = False
multi._jesd_fsm_show_status = False
multi._resync_tx = True
run_plot = False

round_trip_delay_samples = 450
captures = 40
np_corr_window = 256

multi.hmc7044_ext_output_delay(7, 1, 0)
multi.hmc7044_ext_output_delay(10, 1, 0)


multi.hmc7044_car_output_delay(9, 1, 0)

for dev in multi.secondaries + [multi.primary]:

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
        dev._rxadc.find_channel("voltage0_i")
        .attrs["channel_nco_frequency_available"]
        .value
    )
    if channelizer_bypass == "[0 1 0]":
        COMPENSATE_MAIN_PHASES = True
    else:
        COMPENSATE_MAIN_PHASES = False

    # Configure properties
    print("--Setting up " + dev.uri)

    # Loop Combined Tx Channels Back Into Combined Rx Path
    dev.gpio_ctrl_ind = 1
    dev.gpio_5045_v1 = 1
    dev.gpio_5045_v2 = 1
    dev.gpio_ctrl_rx_combined = 0

    # -12dB attenuation
    dev.rx_dsa_gain = -12

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
    dev.dds_single_tone(fs / 6, 0.5, channel=0)

phases_a = []
phases_b = []
phases_c = []
phases_d = []
phases_e = []
phases_f = []
phases_g = []
phases_h = []

so_a = []
so_b = []
so_c = []
so_d = []
so_e = []
so_f = []
so_g = []
so_h = []

for i in range(captures):
    multi._rx_initialized = False

    if True:
        if COMPENSATE_MAIN_PHASES:
            multi.primary.rx_main_nco_phases = [0] * NM_RX
            rx_nco_phases_p = multi.primary.rx_main_nco_phases
            multi.secondaries[0].rx_main_nco_phases = [0] * NM_RX
            rx_nco_phases_s = multi.secondaries[0].rx_main_nco_phases
        else:
            multi.primary.rx_channel_nco_phases = [0] * N_RX
            rx_nco_phases_p = multi.primary.rx_channel_nco_phases
            multi.secondaries[0].rx_channel_nco_phases = [0] * N_RX
            rx_nco_phases_s = multi.secondaries[0].rx_channel_nco_phases

    for r in range(2):
        # Collect data
        x = multi.rx()
        if r == 1:
            max = adjust_gain(x, round_trip_delay_samples)

            if max < 1000:
                print("Continue!")
                continue

        rx_nco_phases_p["axi-ad9081-rx-1"], s_b = measure_and_adjust_phase_offset(
            x[0],
            x[1],
            rx_nco_phases_p["axi-ad9081-rx-1"],
            round_trip_delay_samples,
            np_corr_window,
        )
        rx_nco_phases_p["axi-ad9081-rx-2"], s_c = measure_and_adjust_phase_offset(
            x[0],
            x[2],
            rx_nco_phases_p["axi-ad9081-rx-2"],
            round_trip_delay_samples,
            np_corr_window,
        )
        rx_nco_phases_p["axi-ad9081-rx-3"], s_d = measure_and_adjust_phase_offset(
            x[0],
            x[3],
            rx_nco_phases_p["axi-ad9081-rx-3"],
            round_trip_delay_samples,
            np_corr_window,
        )

        rx_nco_phases_s["axi-ad9081-rx-0"], s_e = measure_and_adjust_phase_offset(
            x[0],
            x[4],
            rx_nco_phases_s["axi-ad9081-rx-0"],
            round_trip_delay_samples,
            np_corr_window,
        )
        rx_nco_phases_s["axi-ad9081-rx-1"], s_f = measure_and_adjust_phase_offset(
            x[0],
            x[5],
            rx_nco_phases_s["axi-ad9081-rx-1"],
            round_trip_delay_samples,
            np_corr_window,
        )
        rx_nco_phases_s["axi-ad9081-rx-2"], s_g = measure_and_adjust_phase_offset(
            x[0],
            x[6],
            rx_nco_phases_s["axi-ad9081-rx-2"],
            round_trip_delay_samples,
            np_corr_window,
        )
        rx_nco_phases_s["axi-ad9081-rx-3"], s_h = measure_and_adjust_phase_offset(
            x[0],
            x[7],
            rx_nco_phases_s["axi-ad9081-rx-3"],
            round_trip_delay_samples,
            np_corr_window,
        )

        phase_b = (
            str(rx_nco_phases_p["axi-ad9081-rx-1"][0] / 1000) + ":" + str(int(s_b))
        )
        phase_c = (
            str(rx_nco_phases_p["axi-ad9081-rx-2"][0] / 1000) + ":" + str(int(s_c))
        )
        phase_d = (
            str(rx_nco_phases_p["axi-ad9081-rx-3"][0] / 1000) + ":" + str(int(s_d))
        )

        phase_e = (
            str(rx_nco_phases_s["axi-ad9081-rx-0"][0] / 1000) + ":" + str(int(s_e))
        )
        phase_f = (
            str(rx_nco_phases_s["axi-ad9081-rx-1"][0] / 1000) + ":" + str(int(s_f))
        )
        phase_g = (
            str(rx_nco_phases_s["axi-ad9081-rx-2"][0] / 1000) + ":" + str(int(s_g))
        )
        phase_h = (
            str(rx_nco_phases_s["axi-ad9081-rx-3"][0] / 1000) + ":" + str(int(s_h))
        )

        phases_a.insert(i, rx_nco_phases_p["axi-ad9081-rx-0"][0] / 1000)
        phases_b.insert(i, rx_nco_phases_p["axi-ad9081-rx-1"][0] / 1000)
        phases_c.insert(i, rx_nco_phases_p["axi-ad9081-rx-2"][0] / 1000)
        phases_d.insert(i, rx_nco_phases_p["axi-ad9081-rx-3"][0] / 1000)

        phases_e.insert(i, rx_nco_phases_s["axi-ad9081-rx-0"][0] / 1000)
        phases_f.insert(i, rx_nco_phases_s["axi-ad9081-rx-1"][0] / 1000)
        phases_g.insert(i, rx_nco_phases_s["axi-ad9081-rx-2"][0] / 1000)
        phases_h.insert(i, rx_nco_phases_s["axi-ad9081-rx-3"][0] / 1000)

        so_a.insert(i, 0)
        so_b.insert(i, s_b)
        so_c.insert(i, s_c)
        so_d.insert(i, s_d)

        so_e.insert(i, s_e)
        so_f.insert(i, s_f)
        so_g.insert(i, s_g)
        so_h.insert(i, s_h)

        result = (
            str(i)
            + "/"
            + str(captures)
            + ": "
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + "\t"
            + phase_b
            + "\t"
            + phase_c
            + "\t"
            + phase_d
            + "\t"
            + phase_e
            + "\t"
            + phase_f
            + "\t"
            + phase_g
            + "\t"
            + phase_h
            + "\n"
        )
        print(result)

        with open("test.txt", "a") as myfile:
            myfile.write(result)

        if run_plot == True:
            plt.xlim(400, 600)
            plt.plot(np.real(x[0]), label="(1) reference", alpha=0.7)
            plt.plot(np.real(x[1]), label="(2) phase " + phase_b, alpha=0.7)
            plt.plot(np.real(x[2]), label="(3) phase " + phase_c, alpha=0.7)
            plt.plot(np.real(x[3]), label="(4) phase " + phase_d, alpha=0.7)

            plt.plot(np.real(x[4]), label="(5) phase " + phase_e, alpha=0.7)
            plt.plot(np.real(x[5]), label="(6) phase " + phase_f, alpha=0.7)
            plt.plot(np.real(x[6]), label="(7) phase " + phase_g, alpha=0.7)
            plt.plot(np.real(x[7]), label="(8) phase " + phase_h, alpha=0.7)

            plt.legend()
            plt.title("Dual QuadMxFE Phase Sync @ " + str(fs / 1000000) + " MSPS")
            plt.show()
            print("FYI: Close figure to do next capture")

        if True:
            if COMPENSATE_MAIN_PHASES:
                multi.primary.rx_main_nco_phases = rx_nco_phases_p
                multi.secondaries[0].rx_main_nco_phases = rx_nco_phases_s
            else:
                multi.primary.rx_channel_nco_phases = rx_nco_phases_p
                multi.secondaries[0].rx_channel_nco_phases = rx_nco_phases_s

if True:

    i = 0
    fig, axs = plt.subplots(2, 4)

    for phases in (
        phases_a,
        phases_b,
        phases_c,
        phases_d,
        phases_e,
        phases_f,
        phases_g,
        phases_h,
    ):
        phases_rounded = [round(num, 1) for num in phases]
        axs[i // 4, i % 4].hist(phases_rounded, 50, facecolor="green", alpha=0.75)
        axs[i // 4, i % 4].set_title("MxFE" + str(i))
        i = i + 1

    plt.tight_layout()
    plt.show()

    plt.xlim(0, captures)
    plt.plot(phases_a, label="(1) MxFE0 phase", alpha=0.7)
    plt.plot(phases_b, label="(2) MxFE1 phase", alpha=0.7)
    plt.plot(phases_c, label="(3) MxFE2 phase", alpha=0.7)
    plt.plot(phases_d, label="(4) MxFE3 phase", alpha=0.7)

    plt.plot(phases_e, label="(5) MxFE0 phase", alpha=0.7)
    plt.plot(phases_f, label="(6) MxFE1 phase", alpha=0.7)
    plt.plot(phases_g, label="(7) MxFE2 phase", alpha=0.7)
    plt.plot(phases_h, label="(8) MxFE3 phase", alpha=0.7)
    if False:
        plt.plot(so_a, label="(1) MxFE0 Samp. Offset", alpha=0.7)
        plt.plot(so_b, label="(2) MxFE1 Samp. Offset", alpha=0.7)
        plt.plot(so_c, label="(3) MxFE2 Samp. Offset", alpha=0.7)
        plt.plot(so_d, label="(4) MxFE3 Samp. Offset", alpha=0.7)

        plt.plot(so_e, label="(5) MxFE0 Samp. Offset", alpha=0.7)
        plt.plot(so_f, label="(6) MxFE1 Samp. Offset", alpha=0.7)
        plt.plot(so_g, label="(7) MxFE2 Samp. Offset", alpha=0.7)
        plt.plot(so_h, label="(8) MxFE3 Samp. Offset", alpha=0.7)

    plt.legend()
    plt.title("Dual QuadMxFE Phase Sync @ " + str(fs / 1000000) + " MSPS")
    plt.show()
    print("FYI: Close figure to do next capture")

input("Press Enter to exit...")
