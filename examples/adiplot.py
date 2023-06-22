import argparse
import os
import sys  # We need sys so that we can pass argv to QApplication
import threading
import time
from queue import Full, Queue
from random import randint

import adi
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from pyqtgraph import GraphicsLayoutWidget, PlotWidget, plot
from scipy import signal
from scipy.fftpack import fft

try:
    import genalyzer

    use_genalyzer = True
    print("Using genalyzer :)")
except ImportError:
    use_genalyzer = False

pg.setConfigOptions(antialias=True)
pg.setConfigOption("background", "k")

REAL_DEV_NAME = "cn05".lower()


class ADIPlotter(object):
    def setup_genalyzer(self, fftsize, fs):

        bits = 12
        navg = 1
        window = 2

        c = genalyzer.config_fftz(fftsize, bits, navg, fftsize, window)
        genalyzer.config_set_sample_rate(fs, c)
        genalyzer.gn_config_fa_auto(ssb_width=120, c=c)

        return c

    def __init__(self, classname, uri):
        self.classname = classname
        self.q = Queue(maxsize=20)
        self.stream = eval("adi." + classname + "(uri='" + uri + "')")
        self.stream.sample_rate = 10000000
        if REAL_DEV_NAME not in classname.lower():
            self.stream.rx_lo = 1000000000
            self.stream.tx_lo = 1000000000
            self.stream.dds_single_tone(3000000, 0.9)
        self.stream.rx_buffer_size = 2 ** 12
        self.stream.rx_enabled_channels = [0]

        if use_genalyzer:
            self.c = self.setup_genalyzer(
                self.stream.rx_buffer_size, self.stream.sample_rate
            )
            self.update_interval = 100
            self.current_count = 0

        self.app = QtWidgets.QApplication(sys.argv)

        self.qmw = QtWidgets.QMainWindow()

        self.qmw.central_widget = QtWidgets.QWidget()
        self.qmw.vertical_layout = QtWidgets.QVBoxLayout()
        self.qmw.setCentralWidget(self.qmw.central_widget)
        self.qmw.central_widget.setLayout(self.qmw.vertical_layout)

        #### Add Plot
        self.qmw.graphWidget = pg.PlotWidget()
        self.qmw.graphWidget.setBackground("black")

        self.traces = {}

        self.win = GraphicsLayoutWidget()
        self.qmw.vertical_layout.addWidget(self.win, 1)
        self.win.setWindowTitle("Spectrum Analyzer")
        self.win.setGeometry(5, 115, 1910, 1070)
        self.win.setBackground(background="black")

        wf_xaxis = pg.AxisItem(orientation="bottom")
        wf_xaxis.setLabel(units="Seconds")

        if REAL_DEV_NAME in classname.lower():
            wf_ylabels = [(0, "0"), (2 ** 11, "2047")]
        else:
            wf_ylabels = [(-2 * 11, "-2047"), (0, "0"), (2 ** 11, "2047")]
        wf_yaxis = pg.AxisItem(orientation="left")
        wf_yaxis.setTicks([wf_ylabels])

        sp_xaxis = pg.AxisItem(orientation="bottom")
        sp_xaxis.setLabel(units="Hz")

        self.waveform = self.win.addPlot(
            title="WAVEFORM", row=1, col=1, axisItems={"bottom": wf_xaxis},
        )
        self.spectrum = self.win.addPlot(
            title="SPECTRUM", row=2, col=1, axisItems={"bottom": sp_xaxis},
        )
        self.waveform.showGrid(x=True, y=True)
        self.spectrum.showGrid(x=True, y=True)

        # waveform and spectrum x points
        self.x = np.arange(0, self.stream.rx_buffer_size) / self.stream.sample_rate
        self.f = np.linspace(
            -1 * self.stream.sample_rate / 2,
            self.stream.sample_rate / 2,
            self.stream.rx_buffer_size,
        )

        self.counter = 0
        self.min = -100
        self.window = signal.kaiser(self.stream.rx_buffer_size, beta=38)

        #### Add a plot to contain our measurement data
        # This is faster than using a table
        self.measurements = self.win.addPlot(title="Measurements", row=3, col=1)
        self.measurements.hideAxis("left")
        self.measurements.hideAxis("bottom")

        self.qmw.show()

        self.run_source = True
        self.thread = threading.Thread(target=self.source)
        self.thread.start()

        self.markers_added = False

    def source(self):
        print("Thread running")
        self.counter = 0
        while self.run_source:
            data = self.stream.rx()
            self.counter += 1
            try:
                self.q.put(data, block=False, timeout=4)
            except Full:
                continue

    def start(self):
        self.app.exec_()

    def add_markers(self, plot, genalyzer_results=None):
        #### Add peak marker for spectrum plot
        data = plot.getData()
        if data[0] is None:
            return
        self.curve_point = pg.CurvePoint(plot)
        self.spectrum.addItem(self.curve_point)
        self.text_peak = pg.TextItem("TEST", anchor=(0.5, 1.0))
        self.text_peak.setParentItem(parent=self.curve_point)

        self.build_custom_table_from_textitems(genalyzer_results)

        self.markers_added = True

    def build_custom_table_from_textitems(self, genalyzer_results):
        text_items = ["Peak", "Frequency", "Amplitude"]
        self.custom_table = {}
        self.table_x = 180
        self.table_y = 50
        scaler = 30
        for i, text in enumerate(text_items):
            self.custom_table[text] = pg.TextItem(text=text)
            # set parent plot
            self.custom_table[text].setParentItem(parent=self.measurements)
            # set position
            self.custom_table[text].setPos(self.table_x, self.table_y + scaler * i)

        if use_genalyzer:
            offset = (len(text_items) + 2) * scaler
            for i, key in enumerate(genalyzer_results):
                self.custom_table[key] = pg.TextItem(text=key)
                self.custom_table[key].setParentItem(parent=self.measurements)
                x_pos = i % 6
                y_pos = np.floor(i // 6)
                self.custom_table[key].setPos(
                    self.table_x + x_pos * 300, self.table_y + offset + scaler * y_pos
                )

    def update_custom_table(self, genalyzer_updates=None):
        if not self.markers_added:
            return
        self.custom_table["Frequency"].setText(
            "Frequency: {:.2f} Hz".format(self.curve_point.pos().x())
        )
        self.custom_table["Amplitude"].setText(
            "Amplitude: {:.2f} dB".format(self.curve_point.pos().y())
        )

        if use_genalyzer:
            for key in genalyzer_updates:
                self.custom_table[key].setText(
                    "{}: {:.2f}".format(key, genalyzer_updates[key])
                )

    def update_genalyzer_table(self, table):
        if not self.markers_added:
            return

        for key in table:
            self.custom_table[key].setText("{}: {:.2f}".format(key, table[key]))
        self.custom_table["Frequency"].setText(
            "Frequency: {:.2f} Hz".format(self.curve_point.pos().x())
        )
        self.custom_table["Amplitude"].setText(
            "Amplitude: {:.2f} dB".format(self.curve_point.pos().y())
        )

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        elif name == "spectrum":
            self.traces[name] = self.spectrum.plot(pen="m", width=3)
            self.spectrum.setLogMode(x=False, y=False)
            self.spectrum.setYRange(self.min, 5, padding=0)
            start = (
                0
                if REAL_DEV_NAME in self.classname.lower()
                else -1 * self.stream.sample_rate / 2
            )
            self.spectrum.setXRange(
                start, self.stream.sample_rate / 2, padding=0.005,
            )
        elif name == "waveform":
            self.traces[name] = self.waveform.plot(pen="c", width=3)
            self.waveform.setYRange(-(2 ** 11) - 200, 2 ** 11 + 200, padding=0)
            self.waveform.setXRange(
                0, self.stream.rx_buffer_size / self.stream.sample_rate, padding=0.005,
            )

    def update(self):
        while not self.q.empty():
            wf_data = self.q.get()
            self.set_plotdata(
                name="waveform", data_x=self.x, data_y=np.real(wf_data),
            )
            if use_genalyzer:
                self.current_count = self.current_count + 1
                if self.current_count >= self.update_interval:
                    self.current_count = 0
                    # Convert array to list of ints
                    i = [int(np.real(a)) for a in wf_data]
                    q = [int(np.imag(b)) for b in wf_data]
                    fft_out_i, fft_out_q = genalyzer.fftz(i, q, self.c)
                    fft_out = [
                        val for pair in zip(fft_out_i, fft_out_q) for val in pair
                    ]

                    # sp_data = np.array(fft_out_i) + 1j * np.array(fft_out_q)
                    # sp_data = np.abs(np.fft.fftshift(sp_data)) / self.stream.rx_buffer_size
                    # sp_data = 20 * np.log10(sp_data / (2**11))

                    # get all Fourier analysis results
                    all_results = genalyzer.get_fa_results(fft_out, self.c)

            else:
                all_results = None

            sp_data = np.fft.fft(wf_data)
            sp_data = np.abs(np.fft.fftshift(sp_data)) / self.stream.rx_buffer_size
            sp_data = 20 * np.log10(sp_data / (2 ** 11))

            self.set_plotdata(name="spectrum", data_x=self.f, data_y=sp_data)

            if use_genalyzer and self.current_count != 0:
                return

            if not self.markers_added:
                self.add_markers(self.traces["spectrum"], all_results)

            # Find peak of spectrum
            index = np.argmax(sp_data)

            # Add label to plot at the peak of the spectrum
            if self.markers_added:
                self.curve_point.setPos(float(index) / (len(self.f) - 1))
                self.text_peak.setText(
                    "[%0.1f, %0.1f]" % (self.f[index], sp_data[index])
                )
                self.update_custom_table(all_results)

    def animation(self):
        timer = QtCore.QTimer()
        timer.timeout.connect(self.update)
        timer.start(1)
        self.start()
        self.run_source = False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ADI fast plotting app")
    parser.add_argument(
        "class", help="pyadi class name to use as plot source", action="store"
    )
    parser.add_argument("uri", help="URI of target device", action="store")
    args = vars(parser.parse_args())

    if args["class"] not in ["Pluto", "ad9361", "ad9364", "ad9363", "cn0532"]:
        raise Exception("Only AD936x based devices or CN0532 are supported")

    app = ADIPlotter(args["class"], args["uri"])
    app.animation()
    print("Exiting...")
    app.thread.join()
