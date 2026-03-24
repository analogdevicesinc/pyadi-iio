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
URI = "ip:10.44.3.70"

NUM_RUNS = 20
BUFFER_SIZE = 2 ** 12
PLOT_RESULTS = True
USE_DMA = True
USE_AION_TRIGGER = False
TX_MAIN_NCO_FREQ = 10000000000
RX_MAIN_NCO_FREQ = -2800000000

CHANNEL_NCO_FREQ = 0
TONE_FS_RATIO = 20
ADJUST_GAIN = True


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
    Single Triton synchronization and phase measurement.

    Uses the axi_aion_trig on a Triton (quad AD9084 MxFE) board to issue a
    coordinated sync start trigger for TX and RX. The board transmits a DMA
    waveform, and the phase/sample offset between TX and RX is measured
    across multiple runs.

    Flow:
    1. Initialize the Triton device.
    2. Configure the axi_aion_trig.
    3. Resume JESD204 FSM if paused.
    4. Configure NCOs, enabled channels, and buffer sizes.
    5. Measurement loop:
       - Arm sync start (TX and RX).
       - Load TX waveform.
       - Fire trigger from axi_aion_trig.
       - Verify sync disarm.
       - Capture RX data.
       - Measure phase and sample delay between TX and RX.
    6. Print statistics and optionally plot results.
    """
    # --- Device handles ---
    print("Connecting to Triton:", URI)
    dev = adi.Triton(URI, calibration_board_attached=False)

    aion_trigger = adi.axi_aion_trig(URI)

    dev.rx_dsa0_gain = 0
    dev.rx_dsa1_gain = 0
    dev.rx_dsa2_gain = 0
    dev.rx_dsa3_gain = 0

    dev.hpf_ctrl = 7
    dev.lpf_ctrl = 12

    # --- JESD204 FSM resume (if paused after boot) ---
    MAX_FSM_RESUME_ATTEMPTS = 4
    for attempt in range(MAX_FSM_RESUME_ATTEMPTS):
        paused = dev.jesd204_fsm_paused
        if paused == 0:
            print("JESD204 FSM running")
            break
        print(
            f"JESD204 FSM resume attempt {attempt + 1}/{MAX_FSM_RESUME_ATTEMPTS} "
            f"(paused={paused})"
        )
        dev._ctx.set_timeout(5000)
        print("  Resuming JESD204 FSM...")
        dev.jesd204_fsm_resume = 1
        time.sleep(2)
    else:
        raise Exception(
            f"JESD204 FSM failed to resume after {MAX_FSM_RESUME_ATTEMPTS} attempts "
            f"(paused={dev.jesd204_fsm_paused})"
        )

    # dev.adf4030.J46_J47_UFL_background_serial_alignment_en = 0

    # --- Configure timeouts ---
    dev._ctx.set_timeout(5000)

    dev.rx_sync_start = "disarm"
    dev.tx_sync_start = "disarm"

    # --- Query channel counts ---
    # Number of MxFE devices
    D = len(dev.rx_test_mode)
    rx_fine, rx_coarse, tx_fine, tx_coarse = get_nco_channel_counts(dev)

    print(
        f"NCO counts: RX fine={rx_fine}, RX coarse={rx_coarse}, "
        f"TX fine={tx_fine}, TX coarse={tx_coarse}"
    )

    # --- Configure NCOs ---
    dev.rx_main_nco_frequencies = [RX_MAIN_NCO_FREQ] * rx_coarse
    dev.tx_main_nco_frequencies = [TX_MAIN_NCO_FREQ] * tx_coarse
    dev.rx_channel_nco_frequencies = [CHANNEL_NCO_FREQ] * rx_fine
    dev.tx_channel_nco_frequencies = [CHANNEL_NCO_FREQ] * tx_fine

    # --- Configure DMA kernel buffers ---
    dev._rxadc.set_kernel_buffers_count(1)
    dev._txdac.set_kernel_buffers_count(2)

    # --- Enable the first RX of each MxFE ---
    rx_chan_en = []
    for i in range(rx_fine):
        if i % (rx_fine / D) == 0:
            rx_chan_en.append(i)
    dev.rx_enabled_channels = rx_chan_en
    dev.tx_enabled_channels = [0]

    # --- Nyquist zone ---
    dev.rx_nyquist_zone = ["even"] * rx_coarse

    # --- Buffer sizes ---
    dev.rx_buffer_size = BUFFER_SIZE
    dev.tx_cyclic_buffer = False

    # --- TX waveform ---
    fs = int(dev.tx_sample_rate["axi-ad9084-rx-hpc"])
    print(f"TX sample rate: {fs / 1e6} MSPS")

    if USE_DMA:
        tx_wave = generate_tone(fs / TONE_FS_RATIO, fs, BUFFER_SIZE)
    else:
        dev.dds_single_tone(fs / TONE_FS_RATIO, 0.5, channel=0)

    # --- Configure AION trigger ---
    if USE_AION_TRIGGER:
        aion_trigger.trig4_en = 1
        aion_trigger.trig4_trigger_select_gpio_enable = 0

    # --- Print sync start availability ---
    print("\n--- Sync Start Availability ---")
    print("TX:", dev.tx_sync_start_available)
    print("RX:", dev.rx_sync_start_available)

    # --- Measurement results (per MxFE vs TX waveform) ---
    num_rx = len(rx_chan_en)
    num_plls = len(dev.adf4382)
    sample_offsets = [[] for _ in range(num_rx)]
    phase_offsets = [[] for _ in range(num_rx)]
    fine_currents = [[] for _ in range(num_plls)]
    ltc6953_out6_phases = []

    print(
        f"\n--- Starting {NUM_RUNS} sync start measurement runs ({num_rx} MxFE channels) ---\n"
    )

    try:
        for run_idx in range(NUM_RUNS):
            # dev.adf4030.J46_J47_UFL_background_serial_alignment_en = 1
            # Step 1: Destroy old buffers
            dev.tx_destroy_buffer()
            dev.rx_destroy_buffer()
            time.sleep(2)
            # Step 2: Arm sync start
            dev.rx_sync_start = "arm"
            dev.tx_sync_start = "arm"
            if not ("arm" == dev.tx_sync_start == dev.rx_sync_start):
                raise Exception(
                    f"Unexpected SYNC status: "
                    f"TX={dev.tx_sync_start} RX={dev.rx_sync_start}"
                )

            # Allow hardware to settle after sync arm before creating buffers
            time.sleep(2)

            # Step 3: Reinitialize RX buffers and transmit
            dev._rx_init_channels()

            time.sleep(2)
            # dev.adf4030.J46_J47_UFL_background_serial_alignment_en = 0
            if USE_DMA:
                dev.tx(tx_wave)

            # Step 4: Fire trigger
            if USE_AION_TRIGGER:
                aion_trigger.trig1_trigger_now = 1
            else:
                dev.tx_sync_start = "trigger_manual"

            # Step 5: Verify sync disarm
            if not ("disarm" == dev.tx_sync_start == dev.rx_sync_start):
                raise Exception(
                    f"Post-trigger SYNC not disarmed: "
                    f"TX={dev.tx_sync_start} RX={dev.rx_sync_start}"
                )

            # Step 6: Capture RX data
            try:
                x = dev.rx()
            except Exception as e:
                print(f"Run# {run_idx} ----------------------------- FAILED: {e}")
                continue

            # Ensure x is a list of channels
            if num_rx == 1:
                x = [x]

            # Step 6b: Optionally normalize amplitudes
            if ADJUST_GAIN:
                adjust_gain(x)

            # Step 7: Measure phase and sample delay of each MxFE vs TX waveform
            phases = []
            delays = []
            for ch in range(num_rx):
                phase, sample_delay = measure_phase_and_delay(tx_wave, x[ch])
                sample_offsets[ch].append(sample_delay)
                phase_offsets[ch].append(phase)
                phases.append(phase)
                delays.append(sample_delay)

            # Step 7b: Read fine_current from each adf4382
            fc = []
            for pll_idx in range(num_plls):
                val = int(dev.adf4382[pll_idx].debug_attrs["fine_current"].value)
                fine_currents[pll_idx].append(val)
                fc.append(val)

            # Step 7c: Read LTC6953_OUT_6 phase from adf4030 (convert fs to ps)
            # ltc6953_phase = dev.adf4030.LTC6953_OUT_6_phase / 1000
            ltc6953_phase = 0
            ltc6953_out6_phases.append(ltc6953_phase)

            phase_parts = "  ".join(
                f"MxFE{ch}: delay={int(delays[ch]):4d} phase={phases[ch]:7.2f}"
                for ch in range(num_rx)
            )
            fc_parts = "  ".join(f"PLL{i}: {fc[i]}" for i in range(num_plls))
            print(
                f"Run# {run_idx:2d}  {phase_parts}  "
                f"fine_current: {fc_parts}  "
                f"LTC6953_OUT_6: {ltc6953_phase:.3f} ps"
            )

            # Step 8: Plot
            if PLOT_RESULTS:
                plt.xlim(0, 1500)
                for ch in range(num_rx):
                    plt.plot(
                        np.real(x[ch]),
                        label=f"MxFE{ch} #{run_idx} {phases[ch]:.1f}\u00b0;{delays[ch]:.0f}",
                        alpha=0.7,
                    )
                plt.legend()
                plt.title(f"Triton Phase Sync @ {fs / 1e6} MSPS")
                plt.draw()
                plt.pause(0.05)
                time.sleep(0.1)

            time.sleep(1)

    finally:
        # Cleanup
        dev.tx_destroy_buffer()
        dev.rx_destroy_buffer()

    # --- Statistics ---
    print("\n=== Measurement Statistics ===\n")

    for ch in range(num_rx):
        print(f"MxFE{ch} vs TX Sample Offsets:")
        print(pd.DataFrame(sample_offsets[ch]).describe())
        print(f"\nMxFE{ch} vs TX Phase Offsets:")
        print(pd.DataFrame(phase_offsets[ch]).describe())
        print()

    for pll_idx in range(num_plls):
        print(f"adf4382_{pll_idx} fine_current:")
        print(pd.DataFrame(fine_currents[pll_idx]).describe())
        print()

    print("LTC6953_OUT_6 phase:")
    print(pd.DataFrame(ltc6953_out6_phases).describe())
    print()

    if PLOT_RESULTS:
        if USE_DMA:
            plt.plot(2 ** 11 / 2 ** 15 * np.real(tx_wave), label="TX wave", alpha=0.1)
        plt.legend()
        plt.show()

        # --- Final plot: phase offsets, fine_current, and LTC6953 phase over runs ---
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True)

        for ch in range(num_rx):
            ax1.plot(phase_offsets[ch], label=f"MxFE{ch} phase", alpha=0.7)
        ax1.set_ylabel("Phase (degrees)")
        ax1.set_title(
            f"Phase Offsets, fine_current & LTC6953_OUT_6 over {len(phase_offsets[0])} runs"
        )
        ax1.legend()

        for pll_idx in range(num_plls):
            ax2.plot(fine_currents[pll_idx], label=f"adf4382_{pll_idx}", alpha=0.7)
        ax2.set_ylabel("fine_current")
        ax2.legend()

        ax3.plot(ltc6953_out6_phases, label="LTC6953_OUT_6", alpha=0.7)
        ax3.set_ylabel("Phase (ps)")
        ax3.set_xlabel("Run")
        ax3.legend()

        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    main()
