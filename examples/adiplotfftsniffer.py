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

# try:
#     import genalyzer

#     use_genalyzer = True
#     print("Using genalyzer :)")
# except ImportError:
use_genalyzer = False

pg.setConfigOptions(antialias=True)
pg.setConfigOption("background", "k")

REAL_DEV_NAME = "cn05".lower()


class ADIFFTSnifferPlotter(object):
    def setup_genalyzer(self, fftsize, fs):

        bits = 12
        navg = 1
        window = 2

        c = genalyzer.config_fftz(fftsize, bits, navg, fftsize, window)
        genalyzer.config_set_sample_rate(fs, c)
        genalyzer.gn_config_fa_auto(ssb_width=120, c=c)

        return c

    def __init__(self, uri):
        self.q = Queue(maxsize=20)
        self._ctrl = adi.ad9084(uri=uri)
        self.stream = self._ctrl.fftsniffer_a
        self.stream.fft_mode = "Magnitude"
        self.stream.sorting_enable = False
        self.stream.real_mode = True


        self.stream.is_complex = self.stream.fft_mode == "Complex"
        self.stream.rx_buffer_size = self.stream.fft_size
        self.stream.sample_rate = int(self.stream.adc_sampling_rate_Hz)

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

        sp_xaxis = pg.AxisItem(orientation="bottom")
        sp_xaxis.setLabel(units="Hz")
        if self.stream.is_complex:
            title = "SPECTRUM (I)"
        else:
            title = "SPECTRUM"
        self.spectrum = self.win.addPlot(
            title=title, row=1, col=1, axisItems={"bottom": sp_xaxis},
        )
        self.spectrum.showGrid(x=True, y=True)
        if self.stream.is_complex:
            spq_xaxis = pg.AxisItem(orientation="bottom")
            spq_xaxis.setLabel(units="Hz")
            self.spectrum_q = self.win.addPlot(
                title="SPECTRUM (Q)", row=2, col=1, axisItems={"bottom": spq_xaxis},
            )
            self.spectrum_q.showGrid(x=True, y=True)
        if self.stream.real_mode == 1:
            self.f = np.linspace(
                0,
                self.stream.sample_rate / 2,
                self.stream.rx_buffer_size,
            )
        else:
            self.f = np.linspace(
                -1 * self.stream.sample_rate / 2,
                self.stream.sample_rate / 2,
                self.stream.rx_buffer_size,
            )

        self.counter = 0
        self.min = -5

        #### Add a plot to contain our measurement data
        # This is faster than using a table
        self.measurements = self.win.addPlot(title="Measurements", row=1, col=2)
        self.measurements.hideAxis("left")
        self.measurements.hideAxis("bottom")

        self.qmw.show()

        self.run_source = True
        self.thread = threading.Thread(target=self.source)
        self.thread.start()

        # self.thread_sweeper = threading.Thread(target=self.sweeper)
        # self.thread_sweeper.start()

        self.markers_added = False

    def sweeper(self):
        freq = 1000000000
        step = 1000000000
        direction = 1
        while self.run_source:
            self._ctrl.tx_main_nco_frequencies = [freq]
            time.sleep(0.1)
            if direction == 1:
                freq += step
            else:
                freq -= step
            if freq >= 8000000000:
                direction = 0
            if freq <= 1000000000:
                direction = 1


    def source(self):
        print("Thread running")
        self.counter = 0
        while self.run_source:
            data = self.stream.capture_fft()
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

        if self.stream.is_complex:
            self.curve_point_q = pg.CurvePoint(plot)
            self.spectrum_q.addItem(self.curve_point_q)
            self.text_peak_q = pg.TextItem("TEST", anchor=(0.5, 1.0))
            self.text_peak_q.setParentItem(parent=self.curve_point_q)

        self.build_custom_table_from_textitems(genalyzer_results)

        self.markers_added = True

    def build_custom_table_from_textitems(self, genalyzer_results):
        text_items = ["Peak", "Frequency", "Amplitude"]
        if self.stream.is_complex:
            text_items += ["Frequency Q", "Amplitude Q"]
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
        prefix = "I " if self.stream.is_complex else ""
        self.custom_table["Frequency"].setText(
            prefix + "Frequency: {:.2f} Hz".format(self.curve_point.pos().x())
        )
        self.custom_table["Amplitude"].setText(
            prefix + "FFT Code: {:.2f}".format(self.curve_point.pos().y())
        )
        if self.stream.is_complex:
            self.custom_table["Frequency Q"].setText(
                "Q Frequency: {:.2f} Hz".format(self.curve_point_q.pos().x())
            )
            self.custom_table["Amplitude Q"].setText(
                "Q FFT Code: {:.2f}".format(self.curve_point_q.pos().y())
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
            self.spectrum.setYRange(self.min, 32, padding=0)
            # start = (
            #     0
            #     # if REAL_DEV_NAME in self.classname.lower()
            #     # else -1 * self.stream.sample_rate / 2
            # )
            start = self.f[0]
            self.spectrum.setXRange(
                start, self.stream.sample_rate / 2, padding=0.005,
            )
            if self.stream.is_complex:
                self.traces["spectrum_q"] = self.spectrum_q.plot(pen="c", width=3)
                self.spectrum_q.setLogMode(x=False, y=False)
                self.spectrum_q.setYRange(self.min, 32, padding=0)
                self.spectrum_q.setXRange(
                    start, self.stream.sample_rate / 2, padding=0.005,
                )

    def update(self):
        while not self.q.empty():
            wf_data = self.q.get()
            # self.set_plotdata(
            #     name="waveform", data_x=self.x, data_y=np.real(wf_data),
            # )
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

            if self.stream.is_complex:
                sp_data = np.real(wf_data)
            else:
                sp_data = wf_data

            self.set_plotdata(name="spectrum", data_x=self.f, data_y=sp_data)
            if self.stream.is_complex:
                self.set_plotdata(
                    name="spectrum_q", data_x=self.f, data_y=np.imag(wf_data),
                )

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
                if self.stream.is_complex:
                    sp_data = np.imag(wf_data)
                    index = np.argmax(sp_data)
                    self.curve_point_q.setPos(float(index) / (len(self.f) - 1))
                    self.text_peak_q.setText(
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
    parser.add_argument("uri", help="URI of target device", action="store")
    args = vars(parser.parse_args())

    app = ADIFFTSnifferPlotter(args["uri"])
    app.animation()
    print("Exiting...")
    app.thread.join()
