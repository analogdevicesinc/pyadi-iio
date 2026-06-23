# Copyright (C) 2025 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import time
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.signal import hilbert

import adi

# === Constants ===
AD9084_URI = "ip:10.44.3.52"
AD9082_URI = "ip:10.44.3.54"
SYNCHRONA_URI = "ip:10.44.3.68"
NUM_RUNS = 10
BUFFER_SIZE = 2 ** 14
PLOT_RESULTS = True
USE_DMA = True
USE_AION_TRIGGER = True
APOLLO_SIDE_A = True


def measure_phase_and_delay(
    sig1: np.ndarray, sig2: np.ndarray, window: int = None, step: int = None
) -> Tuple[float, float]:
    """
    Calculate the average phase offset (in degrees) and sample delay between two signals.

    This function computes the analytic signal (via Hilbert transform) if the input is real,
    then uses cross-correlation in sliding windows to estimate the phase and delay between the two signals.

    Args:
        sig1 (np.ndarray): First input signal (real or complex).
        sig2 (np.ndarray): Second input signal (real or complex), must be the same length as sig1.
        window (int, optional): Size of the analysis window. Defaults to full signal length.
        step (int, optional): Step size between windows. Defaults to non-overlapping.

    Returns:
        Tuple[float, float]: (mean_phase_deg, mean_delay) - average phase offset in degrees and average sample delay.
    """
    sig1 = np.asarray(sig1)
    sig2 = np.asarray(sig2)
    assert sig1.shape == sig2.shape, "Signals must be the same length"

    N = len(sig1)
    if window is None:
        window = N
    if step is None:
        step = window

    if not np.iscomplexobj(sig1):
        sig1 = hilbert(sig1)
    if not np.iscomplexobj(sig2):
        sig2 = hilbert(sig2)

    phases = []
    delays = []

    for start in range(0, N - window + 1, step):
        s1 = sig1[start : start + window]
        s2 = sig2[start : start + window]
        cor = np.correlate(s1, s2, mode="full")
        i = np.argmax(np.abs(cor))
        m = cor[i]
        sample_delay = window - i - 1
        phase_deg = np.angle(m, deg=True)
        phases.append(phase_deg)
        delays.append(sample_delay)

    return float(np.mean(phases)), float(np.mean(delays))


def remove_dc_offset(samples: np.ndarray) -> Tuple[np.ndarray, float]:
    """
    Remove the DC offset from a numpy array of samples.

    Args:
        samples (np.ndarray): Input array of samples.

    Returns:
        Tuple[np.ndarray, float]: (adjusted_samples, dc_offset) - samples with DC removed and the computed DC offset.
    """
    dc_offset = np.mean(samples)
    adjusted_samples = samples - dc_offset
    return adjusted_samples, dc_offset


def generate_tone(freq: float, sample_rate: float, num_samples: int) -> np.ndarray:
    """
    Generate a complex sinusoidal tone for a given frequency, sample rate, and number of samples.

    Args:
        freq (float): Desired tone frequency in Hz.
        sample_rate (float): Sample rate in Hz.
        num_samples (int): Number of samples to generate.

    Returns:
        np.ndarray: Complex-valued tone signal.
    """
    N = num_samples // 8
    freq = int(freq / (sample_rate / N)) * (sample_rate / N)
    ts = 1 / float(sample_rate)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * freq) * 2 ** 15
    q = np.sin(2 * np.pi * t * freq) * 2 ** 15
    Xn = i + 1j * q
    Xn = np.pad(Xn, (0, int(num_samples - N)), "constant")
    return Xn


def zero_imag(samples: np.ndarray) -> np.ndarray:
    """
    Zero out the imaginary part of complex samples, preserving only the real part.

    Args:
        samples (np.ndarray): Input array of complex samples.

    Returns:
        np.ndarray: Array with imaginary part set to zero.
    """
    return np.real(samples) + 0j


def main():
    """
    Main synchronization and measurement routine for AD9084/AD9082 devices.

    This function performs the following steps:
    1. Initializes device handles for AD9084, AD9081, HMC7044, ADF4030, and AION trigger modules.
    2. Configures PLL and clocking delays, and prints relevant status information.
    3. Sets up JESD204 FSM state machines and resumes operation if paused.
    4. Configures buffer sizes, NCO frequencies, enabled channels, and Nyquist zones for both AD9084 and AD9081.
    5. Generates or loads a transmit waveform, depending on the DMA usage flag.
    6. Optionally enables and configures the AION trigger.
    7. Prints chip and API version information.
    8. Prints SYNC START availability for both AD9084 and AD9081, depending on the selected Apollo side.
    9. Runs a measurement loop for a specified number of runs:
        - Arms SYNC START on both devices.
        - Destroys and reinitializes RX/TX buffers and channels.
        - Transmits waveform if DMA is used.
        - Triggers synchronization via AION or manual trigger.
        - Checks SYNC status after triggering.
        - Receives data from both devices, removes DC offset, and downsamples AD9081 data.
        - Measures and records phase and sample delays between TX and RX signals.
        - Optionally plots results for each run.
    10. Cleans up device buffers after measurement.
    11. Prints statistical summaries of measured sample and phase offsets if DMA is used.
    12. Optionally plots the transmitted waveform.

    Raises:
        Exception: If unexpected SYNC status is encountered during arming or after triggering.
    """
    # Device handles
    ad9084 = adi.ad9084(AD9084_URI)
    hmc7044_main = adi.hmc7044(AD9084_URI)
    aion_pll = adi.adf4030(AD9084_URI)
    aion_trigger = adi.axi_aion_trig(AD9084_URI)
    hmc7044_ad9082 = adi.hmc7044(AD9082_URI)
    hmc7044_ad9084 = adi.hmc7044(AD9084_URI)
    hmc7044_synchrona = adi.hmc7044(SYNCHRONA_URI)
    ad9081 = adi.ad9081(AD9082_URI)

    print("--Setting up chips--")
    aion_pll.BSYNC2_DEBUG_P19_reference_channel = 0
    delay_ps = aion_pll.BSYNC2_DEBUG_P19_phase / 1000
    print(f"Delay AD9084_HMC7044 <-> AD9082_HMC7044: {delay_ps} ps")

    if ad9084.jesd204_fsm_paused == 1 and ad9081.jesd204_fsm_paused == 1:
        print("\nStatus HMC7044 Synchrona14:")
        print(hmc7044_synchrona.status)
        print("\nStatus HMC7044 AD9082:")
        print(hmc7044_ad9082.status)
        print("\nStatus HMC7044 AD9084:")
        print(hmc7044_ad9084.status)
        print("AD9084 and AD9081 JESD204 FSM is paused, resuming...")
        ad9084._ctx.set_timeout(0)
        ad9081._ctx.set_timeout(30000)
        aion_pll.BSYNC2_reference_channel = 2
        hmc7044_synchrona.sysref_request = 1
        print("HMC7044 Synchrona14 sysref_request set to 1")
        print("Resuming JESD204 FSM on AD9082")
        ad9081.jesd204_fsm_resume = 1
        print("Resuming JESD204 FSM on AD9084")
        ad9084.jesd204_fsm_resume = 1

    aion_pll.BSYNC2_DEBUG_P19_reference_channel = 2
    delay_ps = aion_pll.BSYNC2_DEBUG_P19_phase / 1000
    print(f"Delay AD9084_SYSREF <-> AD9082_SYSREF:   {delay_ps} ps")

    ad9084._ctx.set_timeout(5000)
    ad9081._ctx.set_timeout(5000)

    ad9084._rxadc.set_kernel_buffers_count(1)
    ad9084._txdac.set_kernel_buffers_count(2)
    ad9084.rx_main_nco_frequencies = [0] * 4
    ad9084.tx_main_nco_frequencies = [0] * 4
    ad9084.rx_channel_nco_frequencies = [0] * 4
    ad9084.tx_channel_nco_frequencies = [0] * 4
    ad9084.rx_enabled_channels = [0]
    ad9084.tx_enabled_channels = [0]
    ad9084.rx_nyquist_zone = ["odd"] * 4
    ad9084.rx_main_tb1_6db_digital_gain_en = [1] * 4

    ad9081._rxadc.set_kernel_buffers_count(1)
    ad9081._txdac.set_kernel_buffers_count(1)
    ad9081.rx_enabled_channels = [0]
    ad9081.rx_nyquist_zone = ["odd"]

    ad9084.rx_buffer_size = BUFFER_SIZE
    ad9084.tx_cyclic_buffer = False
    ad9081.rx_buffer_size = 2 * BUFFER_SIZE
    ad9081.tx_cyclic_buffer = False

    fs = int(ad9084.tx_sample_rate)
    ad9084.dds_single_tone(fs / 10, 0.5, channel=0)

    if USE_DMA:
        tx_wave = generate_tone(fs / 19, fs, BUFFER_SIZE)
    else:
        ad9084.dds_single_tone(fs / 10, 0.5, channel=0)

    ad9084.tx_ddr_offload = 0
    ad9084.tx_b_ddr_offload = 0

    if USE_AION_TRIGGER:
        aion_trigger.trig1_en = 1
        aion_trigger.trig1_trigger_select_gpio_enable = 0

    print("CHIP Version:", ad9084.chip_version)
    print("API  Version:", ad9084.api_version)

    if APOLLO_SIDE_A:
        print("AD9084 TX SYNC START AVAILABLE:", ad9084.tx_sync_start_available)
        print("AD9084 RX SYNC START AVAILABLE:", ad9084.rx_sync_start_available)
    else:
        print("AD9084 TX_B SYNC START AVAILABLE:", ad9084.tx_b_sync_start_available)
        print("AD9084 RX_B SYNC START AVAILABLE:", ad9084.rx_b_sync_start_available)

    print("AD9081 TX_B SYNC START AVAILABLE:", ad9081.tx_sync_start_available)
    print("AD9081 RX_B SYNC START AVAILABLE:", ad9081.rx_sync_start_available)

    sample_offsets_9084 = []
    phase_offsets_9084 = []
    sample_offsets_9081 = []
    phase_offsets_9081 = []
    sample_offsets_diff = []
    phase_offsets_diff = []

    try:
        for run_idx in range(NUM_RUNS):
            if APOLLO_SIDE_A:
                ad9084.rx_sync_start = "arm"
                ad9084.tx_sync_start = "arm"
                if not ("arm" == ad9084.tx_sync_start == ad9084.rx_sync_start):
                    raise Exception(
                        f"AD9084 Unexpected SYNC status: TX {ad9084.tx_sync_start} RX: {ad9084.rx_sync_start}"
                    )
            else:
                ad9084.rx_b_sync_start = "arm"
                ad9084.tx_b_sync_start = "arm"
                if not ("arm" == ad9084.tx_b_sync_start == ad9084.rx_b_sync_start):
                    raise Exception(
                        f"AD9084 Unexpected SYNC status: TX_B {ad9084.tx_b_sync_start} RX_B: {ad9084.rx_b_sync_start}"
                    )

            ad9081.rx_sync_start = "arm"
            ad9081.tx_sync_start = "arm"
            if not ("arm" == ad9081.tx_sync_start == ad9081.rx_sync_start):
                raise Exception(
                    f"AD9081 Unexpected SYNC status: TX {ad9081.tx_sync_start} RX: {ad9081.rx_sync_start}"
                )

            ad9084.tx_destroy_buffer()
            ad9084.rx_destroy_buffer()
            ad9084._rx_init_channels()
            ad9081.rx_destroy_buffer()
            ad9081._rx_init_channels()

            if USE_DMA:
                ad9084.tx(tx_wave)

            if USE_AION_TRIGGER:
                aion_trigger.trig1_trigger_now = 1
            else:
                if APOLLO_SIDE_A:
                    ad9084.tx_sync_start = "trigger_manual"
                else:
                    ad9084.tx_b_sync_start = "trigger_manual"

            if APOLLO_SIDE_A:
                if not ("disarm" == ad9084.tx_sync_start == ad9084.rx_sync_start):
                    raise Exception(
                        f"Unexpected SYNC status: TX {ad9084.tx_sync_start} RX: {ad9084.rx_sync_start}"
                    )
            else:
                if not ("disarm" == ad9084.tx_b_sync_start == ad9084.rx_b_sync_start):
                    raise Exception(
                        f"Unexpected SYNC status: TX_B {ad9084.tx_b_sync_start} RX_B: {ad9084.rx_b_sync_start}"
                    )

            if not ("disarm" == ad9081.tx_sync_start == ad9081.rx_sync_start):
                raise Exception(
                    f"AD9081 Unexpected SYNC status: TX {ad9081.tx_sync_start} RX: {ad9081.rx_sync_start}"
                )

            try:
                rx_9084 = ad9084.rx()
                rx_9084, offset_9084 = remove_dc_offset(rx_9084)
                rx_9081 = ad9081.rx()
                rx_9081 = rx_9081[::2]
            except Exception as e:
                print(f"Run# {run_idx} ----------------------------- FAILED: {e}")
                continue

            if USE_DMA:
                phase_9084, sample_9084 = measure_phase_and_delay(
                    tx_wave.real, rx_9084.real
                )
                phase_9081, sample_9081 = measure_phase_and_delay(
                    tx_wave.real, rx_9081.real
                )
                phase_diff, sample_diff = measure_phase_and_delay(
                    rx_9084.real, rx_9081.real
                )
                sample_offsets_9084.append(sample_9084)
                phase_offsets_9084.append(phase_9084)
                sample_offsets_9081.append(sample_9081)
                phase_offsets_9081.append(phase_9081)
                sample_offsets_diff.append(sample_diff)
                phase_offsets_diff.append(phase_diff)
                print(
                    f"Run# {run_idx} AD9084 Sample Delay {int(sample_9084)} Phase {phase_9084:.2f}, "
                    f"AD9081 Sample Delay {int(sample_9081)} Phase {phase_9081:.2f}, "
                    f"AD9084-AD9082 Sample Delay {int(sample_diff)} Phase {phase_diff:.2f}"
                )

            if PLOT_RESULTS:
                plt.xlim(0, 5000)
                plt.plot(
                    np.real(rx_9084),
                    label=f"AD9084 #{run_idx} {phase_9084:.1f}°;{sample_9084:.0f}",
                    alpha=0.7,
                )
                plt.plot(
                    np.real(rx_9081),
                    label=f"AD9081 #{run_idx} {phase_9081:.1f}°;{sample_9081:.0f}",
                    alpha=0.7,
                )
                plt.legend()
                plt.title(f"AD9084/AD9082 Phase Sync @ {fs / 1e6} MSPS")
                plt.draw()
                plt.pause(0.05)
                time.sleep(0.1)
    finally:
        # Ensure device buffers are cleaned up
        ad9084.tx_destroy_buffer()
        ad9084.rx_destroy_buffer()
        ad9081.rx_destroy_buffer()

    if USE_DMA:
        print("\nAD9084 Sample Offsets")
        print(pd.DataFrame(sample_offsets_9084).describe())
        print("\nAD9084 Phase Offsets\n")
        print(pd.DataFrame(phase_offsets_9084).describe())
        print("\nAD9081 Sample Offsets")
        print(pd.DataFrame(sample_offsets_9081).describe())
        print("\nAD9081 Phase Offsets\n")
        print(pd.DataFrame(phase_offsets_9081).describe())
        print("\nAD9084-AD9082 Sample Offsets")
        print(pd.DataFrame(sample_offsets_diff).describe())
        print("\nAD9084-AD9082 Phase Offsets\n")
        print(pd.DataFrame(phase_offsets_diff).describe())

    if PLOT_RESULTS:
        plt.plot(2 ** 11 / 2 ** 15 * np.real(tx_wave), label="TX wave", alpha=0.1)
        plt.legend()
        plt.show()


if __name__ == "__main__":
    main()
