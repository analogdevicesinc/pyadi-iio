"""
This python example compuntes and plots (using PyQt) the angle of arrival of a complex sinusoid 
source.

Additional dependencies:
- PyQt5
- pyqtgraph
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
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtWidgets import QApplication
from jupiter_init_from_config import jupiter_init

try:
    import jupiter_config_custom as config

    print("Found custom config file")
except:
    print("Didn't find custom config, looking for default.")
    try:
        import jupiter_config as config
    except:
        print("Make sure config.py is in this directory")
        sys.exit(0)

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

powers = []  # main DOA result
angle_of_arrivals = []
phase_angles = []
tracking_length = 1000

# Receive samples
receive_samples = sdrs.rx()

for phase in np.arange(
    -360 / config.lambda_over_d_spacing, 360 / config.lambda_over_d_spacing, 2
):  # sweep over angle
    rx_samples = list(receive_samples)  # use list() to copy content and not the address
    # Apply Gain coefficients
    arrays_adjusted = adjust_gain(
        sdrs, rx_samples[0], rx_samples[1], rx_samples[2], rx_samples[3]
    )
    for i in range(sdrs.num_rx_elements):
        rx_samples[i] = arrays_adjusted[i]

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
    angle_of_arrivals.append(steer_angle)
    phase_angles.append(phase)
    data_sum = (
        rx_samples[0] + rx_samples[1] + rx_samples[2] + rx_samples[3]
    )  # sum the four subarrays
    power_dB = 10 * np.log10(np.sum(np.abs(data_sum) ** 2))
    powers.append(power_dB)

powers -= np.max(powers)  # normalize so max is at 0 dB
current_phase = phase_angles[np.argmax(powers)]
max_angle = angle_of_arrivals[np.argmax(powers)]
phase_log = []
error_log = []

"""Setup Plot Window"""
win = pg.GraphicsLayoutWidget()
win.showMaximized()
p1 = win.addPlot()
p1.setXRange(-80, 80)
p1.setYRange(0, tracking_length)
p1.setLabel("bottom", "Steering Angle", "deg", **{"color": "#FFF", "size": "14pt"})
p1.showAxis("left", show=False)
p1.showGrid(x=True, alpha=1)
p1.setTitle("Monopulse Tracking:  Angle vs Time", **{"color": "#FFF", "size": "14pt"})
fn = QtGui.QFont()
fn.setPointSize(15)
p1.getAxis("bottom").setTickFont(fn)

delay = max_angle  # Initial maximum angle of arrival
tracking_angles = np.ones(tracking_length) * 180
tracking_angles[:-1] = -180  # line across the plot when tracking begins

curve1 = p1.plot(tracking_angles)


def update_tracker():
    global tracking_angles, delay
    global current_phase

    receive_samples = sdrs.rx()  # receive a buffer of data
    data = list(receive_samples)

    # Apply Gain coefficients
    data = adjust_gain(sdrs, data[0], data[1], data[2], data[3])
    # Apply Phase coefficients
    data = adjust_phase(sdrs, current_phase, data[0], data[1], data[2], data[3])
    sum_beam = data[0] + data[1] + data[2] + data[3]
    delta_beam = (data[0] + data[1]) - (data[2] + data[3])
    sum_delta_correlation = np.correlate(sum_beam, delta_beam, "valid")
    error = np.angle(sum_delta_correlation)
    error_log.append(error)

    phase_step = 1
    if np.sign(error) > 0:
        current_phase = current_phase - phase_step
    else:
        current_phase = current_phase + phase_step
    # Update estimated angle of arrival based on error
    steer_angle = np.degrees(
        np.arcsin(
            max(
                min(
                    1,
                    (3e8 * np.radians(current_phase))
                    / (2 * np.pi * signal_freq * elem_spacing),
                ),
                -1,
            )
        )
    )
    phase_log.append(
        steer_angle
    )  # looks nicer to plot steer angle instead of straight phase

    delay = steer_angle
    tracking_angles = np.append(tracking_angles, delay)
    tracking_angles = tracking_angles[1:]
    curve1.setData(tracking_angles, np.arange(tracking_length))


timer = pg.QtCore.QTimer()
timer.timeout.connect(update_tracker)
timer.start(0)

# Start Qt event loop.
if __name__ == "__main__":
    import sys

    if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
        QApplication.instance().exec_()
