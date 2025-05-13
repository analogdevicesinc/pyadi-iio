"""
This python example computes and plots Direction of Arrival (DOA) measurements.
"""

import sys
import os
import numpy as np
import adi.adrv9002_multi as adrv9002_multi
import matplotlib.pyplot as plt
import time
from jupiter_calibration_utils import adjust_gain
from jupiter_calibration_utils import adjust_phase
from jupiter_calibration_utils import calibrate_boresight
from jupiter_init_from_config import jupiter_init
import jupiter_config as config

try:
    print("Attempting to connect to jupiter via ip:localhost...")
    sdrs = adrv9002_multi(
        primary_uri=config.jupiter_ips[0],
        secondary_uris=config.jupiter_ips[1:],
        sync_uri=config.synchrona_ip,
        enable_ssh=True,
        sshargs={"username": "root", "password": "analog"},
        profile_path=os.path.join(
            os.path.dirname(__file__), "MCS_30_72_CLK_AND_RATE.json"
        ),
    )
    print("Devices found")
except:
    print("Devices not found")

time.sleep(0.5)

cal_filepath = os.path.join(os.path.dirname(__file__), "phase_cal_val.pkl")
calibrate_boresight(sdrs)
sdrs.load_phase_cal()
sdrs.load_gain_cal()

# Initialize jupiter
jupiter_init(sdrs)

# Print Phase calibration coefficients
for i in range(len(sdrs.pcal)):
    print("PhCh0 - " + "PhCh" + str(i) + ": " + str(sdrs.pcal[i]))

# Print Gain calibraiton coefficients
for i in range(len(sdrs.gcal)):
    print("Gain coeff ch: " + str(i) + ": " + str(sdrs.gcal[i]))

if config.onboard_tx1_used == True:
    # Calculate time values
    t = np.arange(config.num_samps) / config.sample_rate
    # Generate sinusoidal waveform
    phase_shift = -np.pi / 2  # Shift by -90 degrees
    tx_samples = config.amplitude_discrete * (
        np.cos(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift)
        + 1j * np.sin(2 * np.pi * config.tx_sine_baseband_freq * t + phase_shift)
    )
    # Transmit sinusoid
    sdrs.primary.tx(tx_samples)
else:
    sdrs.tx_destroy_buffer()

elem_spacing = (3e8 / (config.lo_freq + config.tx_sine_baseband_freq)) / (
    config.lambda_over_d_spacing
)
print("Element spacing of: " + str(elem_spacing) + " meters")
print("Number of elements: " + str(sdrs.num_rx_elements))
signal_freq = config.lo_freq

figure_drawn = False
running = True


def on_close(event):
    global running
    running = False


try:
    while running:
        powers = []  # main DOA result
        angle_of_arrivals = []
        # Receive samples
        receive_samples = sdrs.rx()

        for phase in np.arange(
            -360 / config.lambda_over_d_spacing, 360 / config.lambda_over_d_spacing, 2
        ):  # sweep over angle
            rx_samples = list(
                receive_samples
            )  # use list() to copy content and not the address
            # Apply Gain coefficients
            rx_samples = adjust_gain(
                sdrs, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
            )
            # Apply Phase coefficients
            rx_samples = adjust_phase(
                sdrs, phase, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
            )
            steer_angle = np.degrees(
                np.arcsin(
                    max(
                        min(
                            1,
                            (3e8 * np.radians(phase))
                            / (2 * np.pi * signal_freq * elem_spacing),
                        ),
                        -1,
                    )
                )
            )  # arcsin argument must be between 1 and -1, or numpy will throw a warning
            # If you're looking at the array side of Phaser (32 squares) then add a *-1 to steer_angle
            angle_of_arrivals.append(steer_angle)
            data_sum = (
                rx_samples[0] + rx_samples[1] + rx_samples[2] + rx_samples[3]
            )  # sum the two subarrays (within each subarray the 4 channels have already been summed)
            power_dB = 10 * np.log10(np.sum(np.abs(data_sum) ** 2))
            powers.append(power_dB)
        powers -= np.max(powers)  # normalize so max is at 0 dB

        if not figure_drawn:
            fig, ax = plt.subplots()
            # Full screen plot
            manager = plt.get_current_fig_manager()
            try:
                manager.window.attributes("-zoomed", True)
            except AttributeError:
                try:
                    manager.window.showMaximized()
                except:
                    print("Fullscreen not supported")
            (line,) = ax.plot(angle_of_arrivals, powers, ".-")
            plt.ion()
            major_ticks = np.arange(angle_of_arrivals[0], angle_of_arrivals[-1], 10)
            minor_ticks = np.arange(angle_of_arrivals[0], angle_of_arrivals[-1], 2)
            ax.set_xticks(major_ticks)
            ax.set_xticks(minor_ticks, minor=True)
            ax.grid(which="both")
            ax.grid(which="minor", alpha=0.2)
            ax.grid(which="major", alpha=0.5)
            plt.xlabel("Angle of Arrival")
            plt.ylabel("Magnitude [dB]")
            plt.grid(True)
            fig.canvas.mpl_connect("close_event", on_close)
            plt.show()
            figure_drawn = True
        else:
            line.set_ydata(powers)
            fig.canvas.draw_idle()
            plt.pause(0.001)
except KeyboardInterrupt:
    sys.exit()
