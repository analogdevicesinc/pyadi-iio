# Copyright (C) 2023 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

import sys
import time

import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from pyqtgraph.Qt import QtCore, QtGui

import adi

# Instantiate all the Devices
rpi_ip = "ip:phaser.local"  # IP address of the Raspberry Pi
sdr_ip = "ip:192.168.2.1"  # "192.168.2.1, or pluto.local"  # IP address of the Transceiver Block
my_sdr = adi.ad9361(uri=sdr_ip)
my_phaser = adi.CN0566(uri=rpi_ip, sdr=my_sdr)

# Initialize both ADAR1000s, set gains to max, and all phases to 0
my_phaser.configure(device_mode="rx")
my_phaser.load_gain_cal()
my_phaser.load_phase_cal()
for i in range(0, 8):
    my_phaser.set_chan_phase(i, 0)

gain_list = [8, 34, 84, 127, 127, 84, 34, 8]  # Blackman taper
for i in range(0, len(gain_list)):
    my_phaser.set_chan_gain(i, gain_list[i], apply_cal=True)

# Setup Raspberry Pi GPIO states
try:
    my_phaser._gpios.gpio_tx_sw = 0  # 0 = TX_OUT_2, 1 = TX_OUT_1
    my_phaser._gpios.gpio_vctrl_1 = 1  # 1=Use onboard PLL/LO source  (0=disable PLL and VCO, and set switch to use external LO input)
    my_phaser._gpios.gpio_vctrl_2 = (
        1  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
    )
except:
    my_phaser.gpios.gpio_tx_sw = 0  # 0 = TX_OUT_2, 1 = TX_OUT_1
    my_phaser.gpios.gpio_vctrl_1 = 1  # 1=Use onboard PLL/LO source  (0=disable PLL and VCO, and set switch to use external LO input)
    my_phaser.gpios.gpio_vctrl_2 = (
        1  # 1=Send LO to transmit circuitry  (0=disable Tx path, and send LO to LO_OUT)
    )

sample_rate = 0.6e6
center_freq = 2.1e9
signal_freq = 100e3
num_slices = 400
fft_size = 1024 * 4
img_array = np.ones((num_slices, fft_size)) * (-100)

# Configure SDR Rx
my_sdr.sample_rate = int(sample_rate)
my_sdr.rx_lo = int(center_freq)  # set this to output_freq - (the freq of the HB100)
my_sdr.rx_enabled_channels = [0, 1]  # enable Rx1 (voltage0) and Rx2 (voltage1)
my_sdr.rx_buffer_size = int(fft_size)
my_sdr.gain_control_mode_chan0 = "manual"  # manual or slow_attack
my_sdr.gain_control_mode_chan1 = "manual"  # manual or slow_attack
my_sdr.rx_hardwaregain_chan0 = int(30)  # must be between -3 and 70
my_sdr.rx_hardwaregain_chan1 = int(30)  # must be between -3 and 70
# Configure SDR Tx
my_sdr.tx_lo = int(center_freq)
my_sdr.tx_enabled_channels = [0, 1]
my_sdr.tx_cyclic_buffer = True  # must set cyclic buffer to true for the tdd burst mode.  Otherwise Tx will turn on and off randomly
my_sdr.tx_hardwaregain_chan0 = -88  # must be between 0 and -88
my_sdr.tx_hardwaregain_chan1 = -0  # must be between 0 and -88

# Configure the ADF4159 Rampling PLL
output_freq = 12.145e9
BW = 500e6
num_steps = 1000
ramp_time = 1.2e3  # us
ramp_time_s = ramp_time / 1e6
my_phaser.frequency = int(output_freq / 4)  # Output frequency divided by 4
my_phaser.freq_dev_range = int(
    BW / 4
)  # frequency deviation range in Hz.  This is the total freq deviation of the complete freq ramp
my_phaser.freq_dev_step = int(
    (BW / 4) / num_steps
)  # frequency deviation step in Hz.  This is fDEV, in Hz.  Can be positive or negative
my_phaser.freq_dev_time = int(
    ramp_time
)  # total time (in us) of the complete frequency ramp
print("requested freq dev time = ", ramp_time)
print("actual freq dev time = ", my_phaser.freq_dev_time)
my_phaser.delay_word = 4095  # 12 bit delay word.  4095*PFD = 40.95 us.  For sawtooth ramps, this is also the length of the Ramp_complete signal
my_phaser.delay_clk = "PFD"  # can be 'PFD' or 'PFD*CLK1'
my_phaser.delay_start_en = 0  # delay start
my_phaser.ramp_delay_en = 0  # delay between ramps.
my_phaser.trig_delay_en = 0  # triangle delay
my_phaser.ramp_mode = "continuous_triangular"  # ramp_mode can be:  "disabled", "continuous_sawtooth", "continuous_triangular", "single_sawtooth_burst", "single_ramp_burst"
my_phaser.sing_ful_tri = (
    0  # full triangle enable/disable -- this is used with the single_ramp_burst mode
)
my_phaser.tx_trig_en = 0  # start a ramp with TXdata
my_phaser.enable = 0  # 0 = PLL enable.  Write this last to update all the registers

# Print config
print(
    """
CONFIG:
Sample rate: {sample_rate}MHz
Num samples: 2^{Nlog2}
Bandwidth: {BW}MHz
Ramp time: {ramp_time}ms
Output frequency: {output_freq}MHz
IF: {signal_freq}kHz
""".format(
        sample_rate=sample_rate / 1e6,
        Nlog2=int(np.log2(fft_size)),
        BW=BW / 1e6,
        ramp_time=ramp_time / 1e3,
        output_freq=output_freq / 1e6,
        signal_freq=signal_freq / 1e3,
    )
)

# Create a sinewave waveform
fs = int(my_sdr.sample_rate)
print("sample_rate:", fs)
N = int(my_sdr.rx_buffer_size)
fc = int(signal_freq / (fs / N)) * (fs / N)
ts = 1 / float(fs)
t = np.arange(0, N * ts, ts)
i = np.cos(2 * np.pi * t * fc) * 2 ** 14
q = np.sin(2 * np.pi * t * fc) * 2 ** 14
iq = 1 * (i + 1j * q)

# Send data
my_sdr._ctx.set_timeout(0)
my_sdr.tx([iq * 0.5, iq])  # only send data to the 2nd channel (that's all we need)

c = 3e8
default_rf_bw = 500e6
N_frame = fft_size
freq = np.linspace(-fs / 2, fs / 2, int(N_frame))
slope = BW / ramp_time_s
dist = (freq - signal_freq) * c / (4 * slope)

plot_dist = False


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Interactive FFT")
        self.setGeometry(100, 100, 800, 800)  # (x,y, width, height)
        self.setFixedWidth(1600)
        self.num_rows = 12
        self.setWindowFlag(
            QtCore.Qt.WindowCloseButtonHint, False
        )  # remove the window's close button
        self.UiComponents()
        # showing all the widgets
        self.show()

    # method for components
    def UiComponents(self):
        widget = QWidget()

        global layout
        layout = QGridLayout()

        # Control Panel
        control_label = QLabel("PHASER Simple FMCW Radar")
        font = control_label.font()
        font.setPointSize(24)
        control_label.setFont(font)
        font.setPointSize(12)
        control_label.setAlignment(Qt.AlignHCenter)  # | Qt.AlignVCenter)
        layout.addWidget(control_label, 0, 0, 1, 2)

        # Check boxes
        self.x_axis_check = QCheckBox("Toggle Range/Frequency x-axis")
        font = self.x_axis_check.font()
        font.setPointSize(10)
        self.x_axis_check.setFont(font)

        self.x_axis_check.stateChanged.connect(self.change_x_axis)
        layout.addWidget(self.x_axis_check, 2, 0)

        # Range resolution
        # Changes with the RF BW slider
        self.range_res_label = QLabel(
            "B<sub>RF</sub>: %0.2f MHz - R<sub>res</sub>: %0.2f m"
            % (default_rf_bw / 1e6, c / (2 * default_rf_bw))
        )
        font = self.range_res_label.font()
        font.setPointSize(10)
        self.range_res_label.setFont(font)
        self.range_res_label.setAlignment(Qt.AlignLeft)
        self.range_res_label.setMaximumWidth(200)
        self.range_res_label.setMinimumWidth(100)
        layout.addWidget(self.range_res_label, 4, 1)

        # RF bandwidth slider
        self.bw_slider = QSlider(Qt.Horizontal)
        self.bw_slider.setMinimum(100)
        self.bw_slider.setMaximum(500)
        self.bw_slider.setValue(int(default_rf_bw / 1e6))
        self.bw_slider.setTickInterval(50)
        self.bw_slider.setMaximumWidth(200)
        self.bw_slider.setTickPosition(QSlider.TicksBelow)
        self.bw_slider.valueChanged.connect(self.get_range_res)
        layout.addWidget(self.bw_slider, 4, 0)

        self.set_bw = QPushButton("Set RF Bandwidth")
        self.set_bw.setMaximumWidth(200)
        self.set_bw.pressed.connect(self.set_range_res)
        layout.addWidget(self.set_bw, 5, 0, 1, 1)

        self.quit_button = QPushButton("Quit")
        self.quit_button.pressed.connect(self.end_program)
        layout.addWidget(self.quit_button, 30, 0, 4, 4)

        # waterfall level slider
        self.low_slider = QSlider(Qt.Horizontal)
        self.low_slider.setMinimum(-100)
        self.low_slider.setMaximum(0)
        self.low_slider.setValue(-43)
        self.low_slider.setTickInterval(20)
        self.low_slider.setMaximumWidth(200)
        self.low_slider.setTickPosition(QSlider.TicksBelow)
        self.low_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.low_slider, 8, 0)

        self.high_slider = QSlider(Qt.Horizontal)
        self.high_slider.setMinimum(-100)
        self.high_slider.setMaximum(0)
        self.high_slider.setValue(-23)
        self.high_slider.setTickInterval(20)
        self.high_slider.setMaximumWidth(200)
        self.high_slider.setTickPosition(QSlider.TicksBelow)
        self.high_slider.valueChanged.connect(self.get_water_levels)
        layout.addWidget(self.high_slider, 10, 0)

        self.water_label = QLabel("Waterfall Intensity Levels")
        self.water_label.setFont(font)
        self.water_label.setAlignment(Qt.AlignCenter)
        self.water_label.setMinimumWidth(100)
        self.water_label.setMaximumWidth(200)
        layout.addWidget(self.water_label, 7, 0, 1, 1)
        self.low_label = QLabel("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.low_label.setFont(font)
        self.low_label.setAlignment(Qt.AlignLeft)
        self.low_label.setMinimumWidth(100)
        self.low_label.setMaximumWidth(200)
        layout.addWidget(self.low_label, 8, 1)
        self.high_label = QLabel("HIGH LEVEL: %0.0f" % (self.high_slider.value()))
        self.high_label.setFont(font)
        self.high_label.setAlignment(Qt.AlignLeft)
        self.high_label.setMinimumWidth(100)
        self.high_label.setMaximumWidth(200)
        layout.addWidget(self.high_label, 10, 1)

        self.steer_slider = QSlider(Qt.Horizontal)
        self.steer_slider.setMinimum(-80)
        self.steer_slider.setMaximum(80)
        self.steer_slider.setValue(0)
        self.steer_slider.setTickInterval(20)
        self.steer_slider.setMaximumWidth(200)
        self.steer_slider.setTickPosition(QSlider.TicksBelow)
        self.steer_slider.valueChanged.connect(self.get_steer_angle)
        layout.addWidget(self.steer_slider, 14, 0)
        self.steer_title = QLabel("Receive Steering Angle")
        self.steer_title.setFont(font)
        self.steer_title.setAlignment(Qt.AlignCenter)
        self.steer_title.setMinimumWidth(100)
        self.steer_title.setMaximumWidth(200)
        layout.addWidget(self.steer_title, 13, 0)
        self.steer_label = QLabel("%0.0f DEG" % (self.steer_slider.value()))
        self.steer_label.setFont(font)
        self.steer_label.setAlignment(Qt.AlignLeft)
        self.steer_label.setMinimumWidth(100)
        self.steer_label.setMaximumWidth(200)
        layout.addWidget(self.steer_label, 14, 1, 1, 2)

        # FFT plot
        self.fft_plot = pg.plot()
        self.fft_plot.setMinimumWidth(600)
        self.fft_curve = self.fft_plot.plot(freq, pen={"color": "y", "width": 2})
        title_style = {"size": "20pt"}
        label_style = {"color": "#FFF", "font-size": "14pt"}
        self.fft_plot.setLabel("bottom", text="Frequency", units="Hz", **label_style)
        self.fft_plot.setLabel("left", text="Magnitude", units="dB", **label_style)
        self.fft_plot.setTitle("Received Signal - Frequency Spectrum", **title_style)
        layout.addWidget(self.fft_plot, 0, 2, self.num_rows, 1)
        self.fft_plot.setYRange(-60, 0)
        self.fft_plot.setXRange(100e3, 200e3)

        # Waterfall plot
        self.waterfall = pg.PlotWidget()
        self.imageitem = pg.ImageItem()
        self.waterfall.addItem(self.imageitem)
        # Use a viridis colormap
        pos = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
        color = np.array(
            [
                [68, 1, 84, 255],
                [59, 82, 139, 255],
                [33, 145, 140, 255],
                [94, 201, 98, 255],
                [253, 231, 37, 255],
            ],
            dtype=np.ubyte,
        )
        lut = pg.ColorMap(pos, color).getLookupTable(0.0, 1.0, 256)
        self.imageitem.setLookupTable(lut)
        self.imageitem.setLevels([0, 1])
        # self.imageitem.scale(0.35, sample_rate / (N))  # this is deprecated -- we have to use setTransform instead
        tr = QtGui.QTransform()
        tr.translate(0, -sample_rate / 2)
        tr.scale(0.35, sample_rate / (N))
        self.imageitem.setTransform(tr)
        zoom_freq = 20e3
        self.waterfall.setRange(yRange=(signal_freq, signal_freq + zoom_freq))
        self.waterfall.setTitle("Waterfall Spectrum", **title_style)
        self.waterfall.setLabel("left", "Frequency", units="Hz", **label_style)
        self.waterfall.setLabel("bottom", "Time", units="sec", **label_style)
        layout.addWidget(self.waterfall, 0 + self.num_rows + 1, 2, self.num_rows, 1)
        self.img_array = np.ones((num_slices, fft_size)) * (-100)

        widget.setLayout(layout)
        # setting this widget as central widget of the main window
        self.setCentralWidget(widget)

    def get_range_res(self):
        """ Updates the slider bar label with RF bandwidth and range resolution
		Returns:
			None
		"""
        bw = self.bw_slider.value() * 1e6
        range_res = c / (2 * bw)
        self.range_res_label.setText(
            "B<sub>RF</sub>: %0.2f MHz - R<sub>res</sub>: %0.2f m"
            % (bw / 1e6, c / (2 * bw))
        )

    def get_water_levels(self):
        """ Updates the waterfall intensity levels
		Returns:
			None
		"""
        if self.low_slider.value() > self.high_slider.value():
            self.low_slider.setValue(self.high_slider.value())
        self.low_label.setText("LOW LEVEL: %0.0f" % (self.low_slider.value()))
        self.high_label.setText("HIGH LEVEL: %0.0f" % (self.high_slider.value()))

    def get_steer_angle(self):
        """ Updates the steering angle readout
		Returns:
			None
		"""
        self.steer_label.setText("%0.0f DEG" % (self.steer_slider.value()))
        phase_delta = (
            2
            * 3.14159
            * 10.25e9
            * 0.014
            * np.sin(np.radians(self.steer_slider.value()))
            / (3e8)
        )
        my_phaser.set_beam_phase_diff(np.degrees(phase_delta))

    def set_range_res(self):
        """ Sets the RF bandwidth
		Returns:
			None
		"""
        global dist, slope
        bw = self.bw_slider.value() * 1e6
        slope = bw / ramp_time_s
        dist = (freq - signal_freq) * c / (4 * slope)
        print("New slope: %0.2fMHz/s" % (slope / 1e6))
        if self.x_axis_check.isChecked() == True:
            print("Range axis")
            plot_dist = True
            range_x = (100e3) * c / (4 * slope)
            self.fft_plot.setXRange(0, range_x)
        else:
            print("Frequency axis")
            plot_dist = False
            self.fft_plot.setXRange(100e3, 140e3)
        my_phaser.freq_dev_range = int(bw / 4)  # frequency deviation range in Hz
        my_phaser.enable = 0

    def end_program(self):
        """ Gracefully shutsdown the program and Pluto
		Returns:
			None
		"""
        my_sdr.tx_destroy_buffer()
        self.close()

    def change_x_axis(self, state):
        """ Toggles between showing frequency and range for the x-axis
		Args:
			state (QtCore.Qt.Checked) : State of check box
		Returns:
			None
		"""
        global plot_dist, slope
        plot_state = win.fft_plot.getViewBox().state
        if state == QtCore.Qt.Checked:
            print("Range axis")
            plot_dist = True
            range_x = (100e3) * c / (4 * slope)
            self.fft_plot.setXRange(0, range_x)
        else:
            print("Frequency axis")
            plot_dist = False
            self.fft_plot.setXRange(100e3, 200e3)


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
win = Window()
index = 0


def update():
    """ Updates the FFT in the window
	Returns:
		None
	"""
    global index, plot_dist, freq, dist
    label_style = {"color": "#FFF", "font-size": "14pt"}

    data = my_sdr.rx()
    data = data[0] + data[1]
    win_funct = np.blackman(len(data))
    y = data * win_funct
    sp = np.absolute(np.fft.fft(y))
    sp = np.fft.fftshift(sp)
    s_mag = np.abs(sp) / np.sum(win_funct)
    s_mag = np.maximum(s_mag, 10 ** (-15))
    s_dbfs = 20 * np.log10(s_mag / (2 ** 11))

    if plot_dist:
        win.fft_curve.setData(dist, s_dbfs)
        win.fft_plot.setLabel("bottom", text="Distance", units="m", **label_style)
    else:
        win.fft_curve.setData(freq, s_dbfs)
        win.fft_plot.setLabel("bottom", text="Frequency", units="Hz", **label_style)

    win.img_array = np.roll(win.img_array, 1, axis=0)
    win.img_array[0] = s_dbfs
    win.imageitem.setLevels([win.low_slider.value(), win.high_slider.value()])
    win.imageitem.setImage(win.img_array, autoLevels=False)

    if index == 1:
        win.fft_plot.enableAutoRange("xy", False)
    index = index + 1


timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

# start the app
sys.exit(App.exec())
