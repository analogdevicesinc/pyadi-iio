"""
jupiter_reload_profile_sync_syne_example.py

This example script demonstrates how to initialize and synchronize multiple Jupiter SDR devices
using Python. After transmitting a continuous sine wave from the primary device, the system receives
signals using two synchronized Jupiters, capturing data from both Rx channels on each device. The phase
difference between adjacent channels is adjusted to be 10 degrees apart to enchance the visualization 
of phase difference. The script then displays both received time domain signals and the phase difference
between channels continuously. After every 20 Rx captures, the .json profile is reloaded and the devices
are reinitialized showing that the phase difference between each Rx channel is constant. The application level
calibration of gain and phase between each channel is done only once at the start of the script to demonstrate that 
the Multichip Sync functionality gives repeated and similar results after reloading profiles on jupiers.

Main Features:
- Initializes multiple Jupiter SDRs using a profile .json file
- In addition to the multichip sync calibration, the script applies 
application level calibration for phase and gain alignment
- Transmits continuously a baseband complex sinusoid from the primary device Tx1 channel
- Receives continuosly IQ data from all Rx channels on each Jupiter device
- Reloads .json profile after each 20 Rx captures showing how MCS functionality method works after 
reinitialization
- Plots:
    - time-domain waveforms (I channel)
    - phase error between channels across Jupiter devices
"""

import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from adi.adrv9002_multi import adrv9002_multi
from jupiter_calibration_utils import calibrate_boresight
from jupiter_calibration_utils import adjust_phase
from jupiter_calibration_utils import adjust_gain
from time import sleep
import jupiter_config as config
from jupiter_init_from_config import jupiter_init

sw_calibration_done = False


def reload_profile_and_transmit():

    sdrs = adrv9002_multi(
        primary_uri=config.jupiter_ips[0],
        secondary_uris=config.jupiter_ips[1:],
        sync_uri=config.synchrona_ip,
        enable_ssh=False,
        sshargs={"username": "root", "password": "analog"},
        profile_path=os.path.join(
            os.path.dirname(__file__), "MCS_30_72_CLK_AND_RATE.json"
        ),
    )

    jupiter_init(sdrs)

    # Perform Jupiter calibration
    cal_filepath = os.path.join(os.path.dirname(__file__), "phase_cal_val.pkl")
    global sw_calibration_done
    if sw_calibration_done == False:
        calibrate_boresight(sdrs)
        sw_calibration_done = True
    sdrs.load_phase_cal()
    sdrs.load_gain_cal()

    # Calculate time values for Tx1
    t1 = np.arange(config.num_samps) / config.sample_rate
    # Generate sinusoidal waveform
    phase_shift = -np.pi / 2  # Shift by -90 degrees
    tx1_samples = config.amplitude_discrete * (
        np.cos(2 * np.pi * config.tx_sine_baseband_freq * t1 + phase_shift)
        + 1j * np.sin(2 * np.pi * config.tx_sine_baseband_freq * t1 + phase_shift)
    )

    # # Calculate Tx1 spectrum in dBFS
    # tx1_samples_fft = tx1_samples * np.hanning(config.num_samps)
    # ampl_tx = (np.abs(np.fft.fftshift(np.fft.fft(tx1_samples_fft))))
    # fft_tx1_vals_iq_dbFS = 10*np.log10(np.real(ampl_tx)**2 + np.imag(ampl_tx)**2) + 20*np.log10(2/2**(16-1))\
    #                                          - 20*np.log10(len(ampl_tx))
    # f1 = np.linspace(config.sample_rate/-2, config.sample_rate/2, len(fft_tx1_vals_iq_dbFS))

    # Transmit data continuously with first Tx channel of the primary device
    sdrs.primary.tx(tx1_samples)
    sleep(1)
    # Throw 6 buffers
    for i in range(6):
        throw_data = sdrs.rx()

    return sdrs


# Load once the .json profile on Jupiter devices, write configuration attrs and transmit complex sine
sdrs = reload_profile_and_transmit()

# Globals
data = {}
line = {}
running = True
n_ch = 2  # Number of channels per device
x = list(range(config.num_samps))  # x axis points for time plot
num_samples_ph_err = 100  # Number of points on the phase difference plot
ph_err_ch0_minus_ch1_array = [0.0] * num_samples_ph_err
ph_err_ch0_minus_ch2_array = [0.0] * num_samples_ph_err
ph_err_ch0_minus_ch3_array = [0.0] * num_samples_ph_err
ph_err_list_names = [
    "ph_diff_ch0_dev1_minus_ch1_dev1",
    "ph_diff_ch0_dev1_minus_ch0_dev2",
    "ph_diff_ch0_dev1_minus_ch1_dev2",
]
x_ph_err = list(range(num_samples_ph_err))


def on_close(event):
    global running
    running = False
    # sdrs.tx_destroy_buffer()
    print("Plot closed, stopping capture.")


# Create the figure and axes
fig, (ax, ax2) = plt.subplots(nrows=2, sharex=False, figsize=(10, 8))
fig.canvas.mpl_connect("close_event", on_close)

# Full screen plot
manager = plt.get_current_fig_manager()
try:
    manager.window.attributes("-zoomed", True)
except AttributeError:
    try:
        manager.window.showMaximized()
    except:
        print("Fullscreen not supported.")

for dev in [sdrs.primary] + sdrs.secondaries:
    for i in range(n_ch):
        (line[(dev.uri, i)],) = ax.plot(
            x, [0] * config.num_samps, label=f"{dev.uri} I ch{i}"
        )

# Configure plot
ax.set_xlabel("No. Sample")
ax.set_ylabel("Amplitude [LSB]")
ax.grid(which="both", alpha=0.5)
ax.grid(which="minor", alpha=0.2)
ax.grid(which="major", alpha=0.5)
ax.legend(loc="upper left")

for list_name in ph_err_list_names:
    (line[list_name],) = ax2.plot(
        x_ph_err, [0] * num_samples_ph_err, label=f"{list_name}"
    )

ax2.set_ylabel("Phase Error [deg]")
ax2.set_xlabel("Measurement Index")
ax2.grid(True)
ax2.legend(loc="upper right")

plt.legend(loc="upper left")
plt.tight_layout()


# Measure phase difference in degrees between two complex sinusoids
def measure_phase_degrees(chan0, chan1):
    errorV = np.angle(chan0 * np.conj(chan1)) * 180 / np.pi
    error = np.mean(errorV)
    return error


index_load_profiles = 0


# FuncAnimation update function
def update(frame):
    global data
    if not running:
        return list(line.values())

    print("Update plots")
    global index_load_profiles
    # Reload profile after each 20 Rx captures
    if index_load_profiles == 20:
        index_load_profiles = 0
        global sdrs
        sdrs.rx_destroy_buffer()
        sdrs.tx_destroy_buffer()
        # Cleanup before creating another adrv9002 multi device
        del sdrs
        sdrs = reload_profile_and_transmit()
    else:
        index_load_profiles += 1

    # Update plots
    iq0iq1_data = sdrs.rx()
    iq0iq1_data = adjust_phase(
        sdrs, 10, iq0iq1_data[0], iq0iq1_data[1], iq0iq1_data[2], iq0iq1_data[3]
    )
    iq0iq1_data = adjust_gain(
        sdrs, iq0iq1_data[0], iq0iq1_data[1], iq0iq1_data[2], iq0iq1_data[3]
    )
    # print(iq0iq1_data) # print received data

    a = 0
    for dev in [sdrs.primary] + sdrs.secondaries:
        for i in range(n_ch):
            line[(dev.uri, i)].set_ydata(np.real(iq0iq1_data[a]))
            a = a + 1
    ax.relim()
    ax.autoscale_view()

    ph_err_ch0_minus_ch1 = measure_phase_degrees(iq0iq1_data[0], iq0iq1_data[1])
    ph_err_ch0_minus_ch2 = measure_phase_degrees(iq0iq1_data[0], iq0iq1_data[2])
    ph_err_ch0_minus_ch3 = measure_phase_degrees(iq0iq1_data[0], iq0iq1_data[3])

    ph_err_ch0_minus_ch1_array.insert(
        0, ph_err_ch0_minus_ch1
    )  # add element at the beggining of array
    ph_err_ch0_minus_ch2_array.insert(0, ph_err_ch0_minus_ch2)
    ph_err_ch0_minus_ch3_array.insert(0, ph_err_ch0_minus_ch3)
    if len(ph_err_ch0_minus_ch1_array) >= num_samples_ph_err:
        ph_err_ch0_minus_ch1_array.pop()
        ph_err_ch0_minus_ch2_array.pop()
        ph_err_ch0_minus_ch3_array.pop()

    line["ph_diff_ch0_dev1_minus_ch1_dev1"].set_ydata(ph_err_ch0_minus_ch1_array)
    line["ph_diff_ch0_dev1_minus_ch0_dev2"].set_ydata(ph_err_ch0_minus_ch2_array)
    line["ph_diff_ch0_dev1_minus_ch1_dev2"].set_ydata(ph_err_ch0_minus_ch3_array)

    ax2.relim()
    ax2.autoscale_view()

    if index_load_profiles == 20:
        sdrs.rx_destroy_buffer()
        sdrs.tx_destroy_buffer()

    return list(line.values())


# Create animation (update every 2 seconds)
ani = animation.FuncAnimation(fig, update, interval=500, blit=False)

# Show plot
plt.show()
