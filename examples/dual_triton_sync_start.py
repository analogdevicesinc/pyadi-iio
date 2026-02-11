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
PRIMARY_URI = "ip:10.132.12.174"
SECONDARY_URI = "ip:10.132.14.134"


NUM_RUNS = 100
BUFFER_SIZE = 2 ** 12
PLOT_RESULTS = True
USE_DMA = True
USE_AION_TRIGGER = True
TX_MAIN_NCO_FREQ = 10000000000
RX_MAIN_NCO_FREQ = -2800000000

# TX_MAIN_NCO_FREQ = 8400000000
# RX_MAIN_NCO_FREQ = -4400000000

CHANNEL_NCO_FREQ = 0
TONE_FS_RATIO = 20
ADJUST_GAIN = True

# Phases in millidegree
# SECOND_RX_MAIN_NCO_PHASE = -35260
SECOND_RX_MAIN_NCO_PHASE = 0


def measure_phase_and_delay(
    sig1: np.ndarray, sig2: np.ndarray, window: int = None, step: int = None
) -> Tuple[float, float]:
    """
    Calculate the average phase offset (in degrees) and sample delay between two signals.

    Uses cross-correlation in sliding windows on the analytic signal to estimate
    phase and delay.

    Args:
        sig1 (np.ndarray): First input signal (real or complex).
        sig2 (np.ndarray): Second input signal (real or complex), same length as sig1.
        window (int, optional): Size of the analysis window. Defaults to full signal length.
        step (int, optional): Step size between windows. Defaults to non-overlapping.

    Returns:
        Tuple[float, float]: (mean_phase_deg, mean_delay)
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


def adjust_gain(signals, reference_index=0):
    """Normalize a list of signals so their peak amplitudes match the reference.

    Args:
        signals: List of numpy arrays to normalize.
        reference_index: Index of the signal to use as the amplitude reference.

    Returns:
        float: The peak amplitude of the reference signal.
    """
    ref_max = np.amax(np.abs(signals[reference_index]))
    for i in range(len(signals)):
        sig_max = np.amax(np.abs(signals[i]))
        if sig_max != 0:
            signals[i] *= ref_max / sig_max

    return ref_max


def remove_dc_offset(samples: np.ndarray) -> Tuple[np.ndarray, float]:
    """Remove the DC offset from a numpy array of samples."""
    dc_offset = np.mean(samples)
    adjusted_samples = samples - dc_offset
    return adjusted_samples, dc_offset


def generate_tone(freq: float, sample_rate: float, num_samples: int) -> np.ndarray:
    """Generate a complex sinusoidal tone for a given frequency, sample rate, and number of samples."""
    N = num_samples // 8
    freq = int(freq / (sample_rate / N)) * (sample_rate / N)
    ts = 1 / float(sample_rate)
    t = np.arange(0, N * ts, ts)
    i = np.cos(2 * np.pi * t * freq) * 2 ** 15
    q = np.sin(2 * np.pi * t * freq) * 2 ** 15
    Xn = i + 1j * q
    Xn = np.pad(Xn, (0, int(num_samples - N)), "constant")
    return Xn


def get_nco_channel_counts(dev):
    """Query the Triton device to determine NCO channel counts.

    Returns:
        Tuple of (n_rx_fine, n_rx_coarse, n_tx_fine, n_tx_coarse)
    """
    rx_fine = sum(len(v) for v in dev.rx_channel_nco_frequencies.values())
    rx_coarse = sum(len(v) for v in dev.rx_main_nco_frequencies.values())
    tx_fine = sum(len(v) for v in dev.tx_channel_nco_frequencies.values())
    tx_coarse = sum(len(v) for v in dev.tx_main_nco_frequencies.values())
    return rx_fine, rx_coarse, tx_fine, tx_coarse


def main():
    """
    Dual Triton synchronization and phase measurement.

    Synchronizes two Triton (quad AD9084 MxFE) boards using the primary board's
    axi_aion_trig to issue a coordinated sync start trigger to both boards.
    The primary board transmits a DMA waveform, and the phase/sample offset
    between the primary RX and secondary RX captures is measured across
    multiple runs.

    Flow:
    1. Initialize primary and secondary Triton devices.
    2. Configure the axi_aion_trig and adf4030 PLL on the primary.
    3. Resume JESD204 FSM on both boards if paused.
    4. Configure NCOs, enabled channels, and buffer sizes on both boards.
    5. Measurement loop:
       - Arm sync start on both boards (TX and RX).
       - Load TX waveform on primary.
       - Fire trigger from primary's axi_aion_trig.
       - Verify sync disarm on both boards.
       - Capture RX from both boards.
       - Measure phase and sample delay.
    6. Print statistics and optionally plot results.
    """
    # --- Device handles ---
    print("Connecting to primary Triton:", PRIMARY_URI)
    primary = adi.Triton(PRIMARY_URI, calibration_board_attached=False)

    print("Connecting to secondary Triton:", SECONDARY_URI)
    secondary = adi.Triton(SECONDARY_URI, calibration_board_attached=False)

    # The primary board owns the axi_aion_trig and adf4030
    aion_trigger = adi.axi_aion_trig(PRIMARY_URI)

    primary.rx_dsa0_gain = 0
    primary.rx_dsa1_gain = 0
    primary.rx_dsa2_gain = 0
    primary.rx_dsa3_gain = 0

    primary.hpf_ctrl = 7
    primary.lpf_ctrl = 12

    secondary.rx_dsa0_gain = 0
    secondary.rx_dsa1_gain = 0
    secondary.rx_dsa2_gain = 0
    secondary.rx_dsa3_gain = 0

    secondary.hpf_ctrl = 7
    secondary.lpf_ctrl = 12

    # Optional: HMC7044 on a synchrona board for SYSREF distribution
    # hmc7044_synchrona = adi.hmc7044(SYNCHRONA_URI)

    # --- Trigger and PLL configuration ---
    # print("--Setting up trigger and PLL--")
    # aion_trigger.trig1_phase = 10
    # aion_trigger.trig0_phase = 0xFFF8

    # aion_pll.BSYNC2_DEBUG_P19_reference_channel = 0
    # delay_ps = aion_pll.BSYNC2_DEBUG_P19_phase / 1000
    # print(f"Delay Primary <-> Secondary: {delay_ps} ps")

    # --- JESD204 FSM resume (if paused after boot) ---
    MAX_FSM_RESUME_ATTEMPTS = 4
    for attempt in range(MAX_FSM_RESUME_ATTEMPTS):
        p_paused = primary.jesd204_fsm_paused
        s_paused = secondary.jesd204_fsm_paused
        if p_paused == 0 and s_paused == 0:
            print("JESD204 FSM running on both boards")
            break
        print(
            f"JESD204 FSM resume attempt {attempt + 1}/{MAX_FSM_RESUME_ATTEMPTS} "
            f"(primary paused={p_paused}, secondary paused={s_paused})"
        )
        primary._ctx.set_timeout(5000)
        secondary._ctx.set_timeout(5000)
        if s_paused:
            print("  Resuming JESD204 FSM on secondary...")
            secondary.jesd204_fsm_resume = 1
        if p_paused:
            print("  Resuming JESD204 FSM on primary...")
            primary.jesd204_fsm_resume = 1
        time.sleep(2)
    else:
        raise Exception(
            f"JESD204 FSM failed to resume after {MAX_FSM_RESUME_ATTEMPTS} attempts "
            f"(primary paused={primary.jesd204_fsm_paused}, "
            f"secondary paused={secondary.jesd204_fsm_paused})"
        )

    primary.adf4030.J46_J47_UFL_background_serial_alignment_en = 1
    secondary.adf4030.J46_J47_UFL_background_serial_alignment_en = 1

    # --- Post-sync delay measurement ---
    # aion_pll.BSYNC2_DEBUG_P19_reference_channel = 0
    # delay_ps = aion_pll.BSYNC2_DEBUG_P19_phase / 1000
    # print(f"Post-sync delay Primary <-> Secondary: {delay_ps} ps")

    # aion_pll.BSYNC2_DEBUG_P19_reference_channel = 2
    # delay_ps = aion_pll.BSYNC2_DEBUG_P19_phase / 1000
    # print(f"SYSREF delay Primary <-> Secondary:    {delay_ps} ps")

    # --- Configure timeouts ---
    primary._ctx.set_timeout(5000)
    secondary._ctx.set_timeout(5000)

    primary.rx_sync_start = "disarm"
    primary.tx_sync_start = "disarm"
    secondary.rx_sync_start = "disarm"

    # --- Query channel counts from each board ---
    p_rx_fine, p_rx_coarse, p_tx_fine, p_tx_coarse = get_nco_channel_counts(primary)
    s_rx_fine, s_rx_coarse, s_tx_fine, s_tx_coarse = get_nco_channel_counts(secondary)

    print(
        f"Primary:   RX fine={p_rx_fine}, RX coarse={p_rx_coarse}, "
        f"TX fine={p_tx_fine}, TX coarse={p_tx_coarse}"
    )
    print(
        f"Secondary: RX fine={s_rx_fine}, RX coarse={s_rx_coarse}, "
        f"TX fine={s_tx_fine}, TX coarse={s_tx_coarse}"
    )

    # --- Configure NCOs ---
    primary.rx_main_nco_frequencies = [RX_MAIN_NCO_FREQ] * p_rx_coarse
    primary.tx_main_nco_frequencies = [TX_MAIN_NCO_FREQ] * p_tx_coarse
    primary.rx_channel_nco_frequencies = [CHANNEL_NCO_FREQ] * p_rx_fine
    primary.tx_channel_nco_frequencies = [CHANNEL_NCO_FREQ] * p_tx_fine

    secondary.rx_main_nco_frequencies = [RX_MAIN_NCO_FREQ] * s_rx_coarse
    secondary.tx_main_nco_frequencies = [TX_MAIN_NCO_FREQ] * s_tx_coarse
    secondary.rx_channel_nco_frequencies = [CHANNEL_NCO_FREQ] * s_rx_fine
    secondary.tx_channel_nco_frequencies = [CHANNEL_NCO_FREQ] * s_tx_fine

    secondary.rx_main_nco_phases = [SECOND_RX_MAIN_NCO_PHASE] * s_rx_coarse

    # --- Configure DMA kernel buffers ---
    primary._rxadc.set_kernel_buffers_count(1)
    primary._txdac.set_kernel_buffers_count(2)
    secondary._rxadc.set_kernel_buffers_count(1)

    # --- Enable channels ---
    # Enable first RX channel on each board for phase comparison
    primary.rx_enabled_channels = [0]
    primary.tx_enabled_channels = [0]
    secondary.rx_enabled_channels = [0]

    # --- Nyquist zone and gain ---
    primary.rx_nyquist_zone = ["even"] * p_rx_coarse
    # primary.rx_main_tb1_6db_digital_gain_en = [1] * p_rx_coarse
    secondary.rx_nyquist_zone = ["even"] * s_rx_coarse
    # secondary.rx_main_tb1_6db_digital_gain_en = [1] * s_rx_coarse

    # --- Buffer sizes ---
    primary.rx_buffer_size = BUFFER_SIZE
    primary.tx_cyclic_buffer = False
    secondary.rx_buffer_size = BUFFER_SIZE
    secondary.tx_cyclic_buffer = False

    # --- DDR offload ---
    # primary.tx_ddr_offload["axi-ad9084-tx-hpc"] = 0

    # --- TX waveform ---
    fs = int(primary.tx_sample_rate["axi-ad9084-rx-hpc"])
    print(f"TX sample rate: {fs / 1e6} MSPS")

    if USE_DMA:
        tx_wave = generate_tone(fs / TONE_FS_RATIO, fs, BUFFER_SIZE)
    else:
        primary.dds_single_tone(fs / TONE_FS_RATIO, 0.5, channel=0)

    # --- Configure AION trigger ---
    if USE_AION_TRIGGER:
        aion_trigger.trig4_en = 1
        aion_trigger.trig4_trigger_select_gpio_enable = 0

    # --- Print sync start availability ---
    print("\n--- Sync Start Availability ---")
    print("Primary  TX:", primary.tx_sync_start_available)
    print("Primary  RX:", primary.rx_sync_start_available)
    print("Secondary TX:", secondary.tx_sync_start_available)
    print("Secondary RX:", secondary.rx_sync_start_available)

    # --- Freeze background tracking calibration on all MxFEs ---
    # for ctrl in primary._ctrls:
    #     ctrl.attrs["mcs_bg_tacking_cal_freeze"].value = "y"
    # for ctrl in secondary._ctrls:
    #     ctrl.attrs["mcs_bg_tacking_cal_freeze"].value = "y"

    # --- Measurement results ---
    sample_offsets_primary = []
    phase_offsets_primary = []
    sample_offsets_secondary = []
    phase_offsets_secondary = []
    sample_offsets_diff = []
    phase_offsets_diff = []

    print(f"\n--- Starting {NUM_RUNS} sync start measurement runs ---\n")

    try:
        for run_idx in range(NUM_RUNS):

            # Step 1: Destroy old buffers
            primary.tx_destroy_buffer()
            primary.rx_destroy_buffer()
            secondary.rx_destroy_buffer()

            # Step 2: Arm sync start on both boards
            primary.rx_sync_start = "arm"
            primary.tx_sync_start = "arm"
            if not ("arm" == primary.tx_sync_start == primary.rx_sync_start):
                raise Exception(
                    f"Primary unexpected SYNC status: "
                    f"TX={primary.tx_sync_start} RX={primary.rx_sync_start}"
                )

            secondary.rx_sync_start = "arm"
            secondary.tx_sync_start = "arm"
            if not ("arm" == secondary.tx_sync_start == secondary.rx_sync_start):
                raise Exception(
                    f"Secondary unexpected SYNC status: "
                    f"TX={secondary.tx_sync_start} RX={secondary.rx_sync_start}"
                )

            # Allow hardware to settle after sync arm before creating buffers
            time.sleep(2)

            # Step 3: Reinitialize RX buffers and transmit
            primary._rx_init_channels()
            secondary._rx_init_channels()

            if USE_DMA:
                primary.tx(tx_wave)

            # Step 4: Fire trigger
            if USE_AION_TRIGGER:
                aion_trigger.trig1_trigger_now = 1
            else:
                primary.tx_sync_start = "trigger_manual"

            # Step 5: Verify sync disarm on both boards
            if not ("disarm" == primary.tx_sync_start == primary.rx_sync_start):
                raise Exception(
                    f"Primary post-trigger SYNC not disarmed: "
                    f"TX={primary.tx_sync_start} RX={primary.rx_sync_start}"
                )
            if not ("disarm" == secondary.tx_sync_start == secondary.rx_sync_start):
                raise Exception(
                    f"Secondary post-trigger SYNC not disarmed: "
                    f"TX={secondary.tx_sync_start} RX={secondary.rx_sync_start}"
                )

            # Step 6: Capture RX data from both boards
            try:
                rx_primary = primary.rx()
                # rx_primary, _ = remove_dc_offset(rx_primary)

                rx_secondary = secondary.rx()
                # rx_secondary, _ = remove_dc_offset(rx_secondary)
            except Exception as e:
                print(f"Run# {run_idx} ----------------------------- FAILED: {e}")
                continue

            # Step 6b: Optionally normalize amplitudes
            if ADJUST_GAIN:
                adjust_gain([rx_primary, rx_secondary])

            # Step 7: Measure phase and sample delay
            if USE_DMA:
                phase_p, sample_p = measure_phase_and_delay(tx_wave, rx_primary)
                phase_s, sample_s = measure_phase_and_delay(tx_wave, rx_secondary)
                phase_diff, sample_diff = measure_phase_and_delay(
                    rx_primary, rx_secondary
                )

                if sample_diff == -64:
                    print(
                        f"Run# {run_idx} ----------------------------- WARNING: Sample offset at buffer boundary, may be inaccurate"
                    )
                    continue

                sample_offsets_primary.append(sample_p)
                phase_offsets_primary.append(phase_p)
                sample_offsets_secondary.append(sample_s)
                phase_offsets_secondary.append(phase_s)
                sample_offsets_diff.append(sample_diff)
                phase_offsets_diff.append(phase_diff)

                print(
                    f"Run# {run_idx:2d}  "
                    f"Primary: delay={int(sample_p):4d} phase={phase_p:7.2f}  "
                    f"Secondary: delay={int(sample_s):4d} phase={phase_s:7.2f}  "
                    f"Diff: delay={int(sample_diff):4d} phase={phase_diff:7.2f}"
                )

                # Align and re-measure for time delta
                # max_offset = max(sample_p, sample_s)
                # rolled_p = np.roll(rx_primary.real, int(-max_offset))
                # rolled_s = np.roll(rx_secondary.real, int(-max_offset))
                # phase_aligned, sample_aligned = measure_phase_and_delay(
                #     rolled_p[100:1100], rolled_s[100:1100]
                # )
                # time_delta = 1e12 * phase_aligned / 360.0 / (fs / TONE_FS_RATIO)
                # print(
                #     f"         Aligned: delay={int(sample_aligned)} "
                #     f"phase={phase_aligned:.2f} time={time_delta:.2f} ps"
                # )

            # Step 8: Plot (before compensation)
            if PLOT_RESULTS:
                plt.xlim(0, 1500)
                plt.plot(
                    np.real(rx_primary),
                    label=f"Primary #{run_idx} {phase_p:.1f}\u00b0;{sample_p:.0f}",
                    alpha=0.7,
                )
                plt.plot(
                    np.real(rx_secondary),
                    label=f"Secondary #{run_idx} {phase_s:.1f}\u00b0;{sample_s:.0f}",
                    alpha=0.7,
                )
                plt.legend()
                plt.title(f"Dual Triton Phase Sync @ {fs / 1e6} MSPS")
                plt.draw()
                plt.pause(0.05)
                time.sleep(0.1)

            time.sleep(1)

    finally:
        # Cleanup
        primary.tx_destroy_buffer()
        primary.rx_destroy_buffer()
        secondary.rx_destroy_buffer()

        # Unfreeze background tracking calibration
        # for ctrl in primary._ctrls:
        #     ctrl.attrs["mcs_bg_tacking_cal_freeze"].value = "n"
        # for ctrl in secondary._ctrls:
        #     ctrl.attrs["mcs_bg_tacking_cal_freeze"].value = "n"

    # --- Statistics ---
    if USE_DMA:
        print("\n=== Measurement Statistics ===\n")

        print("Primary Sample Offsets:")
        print(pd.DataFrame(sample_offsets_primary).describe())
        print("\nPrimary Phase Offsets:")
        print(pd.DataFrame(phase_offsets_primary).describe())

        print("\nSecondary Sample Offsets:")
        print(pd.DataFrame(sample_offsets_secondary).describe())
        print("\nSecondary Phase Offsets:")
        print(pd.DataFrame(phase_offsets_secondary).describe())

        print("\nPrimary-Secondary Sample Offsets:")
        print(pd.DataFrame(sample_offsets_diff).describe())
        print("\nPrimary-Secondary Phase Offsets:")
        print(pd.DataFrame(phase_offsets_diff).describe())

    if PLOT_RESULTS:
        if USE_DMA:
            plt.plot(2 ** 11 / 2 ** 15 * np.real(tx_wave), label="TX wave", alpha=0.1)
        plt.legend()
        plt.show()


if __name__ == "__main__":
    main()
