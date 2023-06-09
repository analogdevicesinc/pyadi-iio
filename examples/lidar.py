# Copyright (C) 2019 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD


# This example creates a GUI for configuring, controlling and capturing samples
# from a Lidar board. You can select the pulse width, trigger level, apd bias
# and tilt voltage, among others. The Start buttons starts the capturing of
# samples witch are displayed on the top of the GUI.

# The channel 0 (reference signal) and channel 1 (return signal) are enabled and
# used to determine the distance with a correlation method. The distance is
# displayed in the bottom half of the GUI. Because displaying the distance
# measurement in real time would mean updating the plot much to often to be
# useful to the eyes, a method is used to only display the average measured
# distance of the last 10 samples.

import csv
import tkinter as tk
from tkinter import filedialog, ttk

import iio

import matplotlib.pyplot as plt
import numpy as np
from adi.fmclidar1 import fmclidar1
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy.signal import firwin

lidar = None  # Lidar context
snapshot_path = ""  # If set to non-empty, save the rx samples to that path
reference_signal = []  # type: ignore Synthetic signal used for distance correlation
NSAMPLES = 10
# Keep count of distance measurements for each sample and for all channels.
# One channel is used for the reference signal.
all_channels_samples = [[] for i in range(16)]  # type: ignore
distances = [[] for i in range(16)]  # type: ignore
meas_distance_mean = [0 for i in range(16)]
mean_samples_count = [NSAMPLES for i in range(16)]
mean_samples_sum = [0 for i in range(16)]


def close_app():
    global running
    running = False
    root.destroy()


def cont_capt():
    """Continuously request samples after Start is pressed."""
    global laser_enabled
    if button_txt.get() == "Start" and laser_enabled.get() == 1:
        button_txt.set("Stop")
    else:
        button_txt.set("Start")
    while button_txt.get() == "Stop" and laser_enabled.get() == 1:
        single_capt()


def single_capt():
    """Display info about a single capture."""
    global snapshot_path
    samples = lidar.rx()
    if snapshot_path != "":  # Requested to save a snapshot
        with open(snapshot_path, "w") as result_file:
            wr = csv.writer(result_file, dialect="excel")
            for s in samples:  # add all samples to file specified in path
                if len(s) > 0:  # not empty
                    wr.writerow(s.tolist())
        snapshot_path = ""  # wait for the next request

    ref = [x * 120 for x in reference_signal]  # Reference signal

    for i, s in enumerate(samples, start=0):
        if len(s) == 0:
            continue
        global meas_distance_mean
        global mean_samples_count
        global mean_samples_sum

        corr_lidar = np.correlate(ref, s, mode="full")
        lag_lidar = corr_lidar.argmax() - (len(s) - 1)
        # Adjust for system offset
        lag_lidar -= 8
        meas_distance = abs(lag_lidar * 15) - distance_offset.get()
        if mean_samples_count[i] > 0:
            mean_samples_sum[i] += meas_distance
            mean_samples_count[i] -= 1
        else:
            distance_plot.cla()
            distance_plot.grid(True)
            distance_plot.set_title("Distance Approximation")
            distance_plot.set_xlabel("Sample number")
            distance_plot.set_ylabel("Distance (cm)")
            distance_plot.bar(range(MAX_SAMPLES), [0] * MAX_SAMPLES)
            dist = round(mean_samples_sum[i] / NSAMPLES, 2)
            distances[i].append(dist)
            for j, d in enumerate(distances, start=0):
                if len(d) == 0:
                    continue
                distance_plot.plot(d, label=str(d[-1]))
            distance_plot.legend()
            mean_samples_sum[i] = 0
            mean_samples_count[i] = NSAMPLES

    # Readjust the axes after a certain number of measurements so that
    # MAX_SAMPLES measurements are always visible on the plot
    samples_taken = len(distances[0])
    if samples_taken > MAX_SAMPLES - 5:
        distance_plot.set_xlim([samples_taken - MAX_SAMPLES + 5, samples_taken + 5])

    # Plot data
    signal_plot.cla()
    signal_plot.set_title("Pulse Shape")
    signal_plot.set_xlabel("Time (ns)")
    signal_plot.set_ylabel("ADC Codes")
    signal_plot.set_ylim([-30, 130])
    signal_plot.grid(True)

    for i, s in enumerate(samples, start=0):
        if len(s) == 0:
            continue
        signal_plot.plot(s, label="Channel" + str(i))
    signal_plot.plot(ref, label="Reference")

    try:
        a.plot(top_edge, x[top_edge], "X")
        a.plot(bottom_edge, x[bottom_edge], "X")
        a.axvline(x=TIME_OFFSET, color="green", label="Cal Offset")
        a.axvline(x=mid_point, color="red", label="Mid point")
    except:
        pass
    signal_plot.legend()
    canvas.draw()

    root.update_idletasks()
    root.update()


def config_board():
    global lidar
    global distances
    global reference_signal
    global meas_distance_mean
    global mean_samples_count
    global mean_samples_sum
    if lidar == None:
        try:
            lidar = fmclidar1(uri="ip:" + ip_addr.get())
            msg_log_txt.insert(tk.END, "Device Connected.\n")
            lidar.rx_buffer_size = 1024
            lidar.laser_enable()
        except:
            msg_log_txt.insert(tk.END, "No device found.\n")
            return
    lidar.laser_pulse_width = int(pw.get())
    lidar.sequencer_pulse_delay = int(pulse_delay.get())
    lidar.laser_frequency = int(pulse_freq.get())
    lidar.apdbias = float(apd_voltage.get())
    lidar.tiltvoltage = float(tilt_voltage.get())
    lidar.channel_sequencer_opmode = seq_mode.get()
    lidar.channel_sequencer_order_manual_mode = manual_mode_order.get()

    # Clear the distance measurement and display
    distances = [[] for i in range(16)]
    meas_distance_mean = [0 for i in range(16)]
    mean_samples_count = [NSAMPLES for i in range(16)]
    mean_samples_sum = [0 for i in range(16)]

    # Generate the signal used for distance correlation based on user settings
    leading_gap = 100
    square_signal = (
        [0 for i in range(leading_gap)]
        + [1 for i in range(lidar.laser_pulse_width)]
        + [
            0
            for i in range(lidar.rx_buffer_size - lidar.laser_pulse_width - leading_gap)
        ]
    )
    fir_filter = firwin(filter_numtaps.get(), filter_cutoff.get())
    reference_signal = np.convolve(square_signal, fir_filter)


root = tk.Tk()
root.title("AD-FMCLIDAR1-EBZ")
global running
running = True
root.protocol("WM_DELETE_WINDOW", close_app)
DEFAULT_IP = "10.48.65.124"
DEFAULT_PULSE_WIDTH = "20"
DEFAULT_FREQUENCY = "1000"
DEFAULT_TRIG_LEVEL = "-10"
DEFAULT_APD_VOLTAGE = "-160.0"
DEFAULT_TILT_VOLTAGE = "1.0"
DEFAULT_PULSE_DELAY = "248"
# Length of filter for synthetic signal generation
DEFAULT_FILTER_NUMTAPS = 64
# Cuttof frequency of filter for synthetic signal generation
DEFAULT_FILTER_CUTOFF = 0.05
# Measured distance offset for the synthetic signal (for 64 and 0.05)
DEFAULT_DISTANCE_OFFSET = 745

TIME_OFFSET = 167.033333
RUN_DUMMY_DATA = 0
MAX_SAMPLES = 30  # Number of distance measurement samples shown in plot
TIMEOUT_SAMPLES = 0.5

# Config attributes
ip_addr = tk.StringVar()
ip_addr.set(DEFAULT_IP)

pw = tk.StringVar()
pw.set(DEFAULT_PULSE_WIDTH)

pulse_freq = tk.StringVar()
pulse_freq.set(DEFAULT_FREQUENCY)

trig_level = tk.StringVar()
trig_level.set(DEFAULT_TRIG_LEVEL)

apd_voltage = tk.StringVar()
apd_voltage.set(DEFAULT_APD_VOLTAGE)

tilt_voltage = tk.StringVar()
tilt_voltage.set(DEFAULT_TILT_VOLTAGE)

pulse_delay = tk.StringVar()
pulse_delay.set(DEFAULT_PULSE_DELAY)

fr1 = tk.Frame(root)
fr1.pack(side=tk.LEFT, anchor="n", pady=30, padx=30)

fr2 = tk.Frame(fr1)
fr2.grid(row=0, column=0, pady=10)

laser_settings_label = tk.Label(fr2, text="AD-FMCLIDAR1-EBZ")
laser_settings_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
laser_settings_label.configure(font="Verdana 19 bold underline")

label1 = tk.Label(fr2, text="IP Addressss: ")
label1.grid(row=1, column=0)

entry1 = tk.Entry(fr2, textvariable=ip_addr)
entry1.grid(row=1, column=1)

laser_settings_label = tk.Label(fr2, text="Laser Settings")
laser_settings_label.grid(row=2, column=0, columnspan=2, pady=(30, 10))
laser_settings_label.configure(font="Verdana 16")

msg_log_label = tk.Label(fr2, text="Pulse Width (ns): ")
msg_log_label.grid(row=3, column=0)

entry2 = tk.Entry(fr2, textvariable=pw)
entry2.grid(row=3, column=1)

label3 = tk.Label(fr2, text="Rep Rate (Hz): ")
label3.grid(row=4, column=0)

entry3 = tk.Entry(fr2, textvariable=pulse_freq)
entry3.grid(row=4, column=1)

laser_enabled = tk.IntVar(value=1)


def enable_disable_laser():
    """Enable/disable the laser."""
    global laser_enabled
    if laser_enabled == 0:
        lidar.laser_disable()
    else:
        lidar.laser_enable()
        cont_capt()


en_laser = tk.Checkbutton(
    fr2, text="Enable Laser", variable=laser_enabled, command=enable_disable_laser
)
en_laser.grid(row=5, column=0)

afe_settings_label = tk.Label(fr2, text="AFE Settings")
afe_settings_label.grid(row=6, column=0, columnspan=2, pady=(30, 10))
afe_settings_label.configure(font="Verdana 16")

apd_bias_label = tk.Label(fr2, text="APD Bias (V): ")
apd_bias_label.grid(row=7, column=0)

apd_bias_entry = tk.Entry(fr2, textvariable=apd_voltage)
apd_bias_entry.grid(row=7, column=1)

tilt_voltage_label = tk.Label(fr2, text="Tilt Voltage (V): ")
tilt_voltage_label.grid(row=8, column=0)

tilt_voltage_entry = tk.Entry(fr2, textvariable=tilt_voltage)
tilt_voltage_entry.grid(row=8, column=1)

sequencer_settings_label = tk.Label(fr2, text="Sequencer Settings")
sequencer_settings_label.grid(row=9, column=0, columnspan=2, pady=(30, 10))
sequencer_settings_label.configure(font="Verdana 16")

seq_mode = tk.StringVar(root)
seq_mode.set("manual")
tk.OptionMenu(fr2, seq_mode, "manual", "auto").grid(row=10, column=0)

manual_mode_order = tk.StringVar(root)
manual_mode_order.set("0 0 0 0")
tk.Entry(fr2, textvariable=manual_mode_order).grid(row=10, column=1)

pulse_delay_label = tk.Label(fr2, text="Pulse Delay (ns)")
pulse_delay_label.grid(row=11, column=0)

pulse_delay_entry = tk.Entry(fr2, textvariable=pulse_delay)
pulse_delay_entry.grid(row=11, column=1)

ref_signal_label = tk.Label(fr2, text="Reference Signal Parameters")
ref_signal_label.grid(row=12, column=0, columnspan=2, pady=(30, 10))
ref_signal_label.configure(font="Verdana 16")

filter_numtaps_label = tk.Label(fr2, text="Filter Length: ")
filter_numtaps_label.grid(row=13, column=0)

filter_numtaps = tk.IntVar(value=DEFAULT_FILTER_NUMTAPS)
filter_numtaps_entry = tk.Entry(fr2, textvariable=filter_numtaps)
filter_numtaps_entry.grid(row=13, column=1)

filter_cutoff_label = tk.Label(fr2, text="Filter Cutoff: ")
filter_cutoff_label.grid(row=14, column=0)

filter_cutoff = tk.DoubleVar(value=DEFAULT_FILTER_CUTOFF)
filter_cutoff_entry = tk.Entry(fr2, textvariable=filter_cutoff)
filter_cutoff_entry.grid(row=14, column=1)

distance_offset_label = tk.Label(fr2, text="Distance Offset (cm): ")
distance_offset_label.grid(row=15, column=0)

distance_offset = tk.DoubleVar(value=DEFAULT_DISTANCE_OFFSET)
distance_offset_entry = tk.Entry(fr2, textvariable=distance_offset)
distance_offset_entry.grid(row=15, column=1)

button_txt = tk.StringVar()
button = tk.Button(fr2, textvariable=button_txt, command=cont_capt)
button_txt.set("Start")
button.config(width=20, height=1)
button.grid(row=16, column=0, columnspan=2, pady=(60, 5))

config_button = tk.Button(fr2, text="Config Board", command=config_board)
config_button.config(width=20, height=1)
config_button.grid(row=17, column=0, columnspan=2, pady=5)


def save_snapshot():
    """Request a snapshot save to the user selected file."""
    global snapshot_path
    snapshot_path = filedialog.asksaveasfilename(
        initialdir=".",
        title="Save as",
        filetypes=(("CSV", "*.csv"), ("all files", "*.*")),
    )


save_csv = tk.Button(fr2, text="Save Snapshot", command=save_snapshot)
save_csv.config(width=20, height=1)
save_csv.grid(row=18, column=0, columnspan=2, pady=10)

fr3 = tk.Frame(fr1)
fr3.grid(row=3, column=0)

msg_log_label = tk.Label(fr3, text="Message Log: ")
msg_log_label.grid(row=0, column=0)

msg_log_txt = tk.Text(fr3, width=40, height=5)
msg_log_txt.grid(row=4, column=0)

fig = plt.figure(figsize=(15, 20))
signal_plot = fig.add_subplot(211)
distance_plot = fig.add_subplot(212)

canvas = FigureCanvasTkAgg(fig, master=root)
canvas.get_tk_widget().pack(side=tk.RIGHT, anchor="n")
canvas.draw()
root.update_idletasks()

config_board()
while running:
    root.update()
