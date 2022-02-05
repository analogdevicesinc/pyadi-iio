import argparse
import sys
import threading
import time
from queue import Full, Queue

import adi
import numpy as np
import pyqtgraph as pg

# from PyQt5 import QtGui as PQG
# from PyQt5.QtWidgets import QSlider, QHBoxLayout, QVBoxLayout, QWidget, QApplication
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)
from pyqtgraph.Qt import QtCore, QtGui
from scipy import signal
from scipy.fftpack import fft


REAL_DEV_NAME = "cn05".lower()


class CheckBox(QWidget):

    device = False

    def __init__(self, device, parent=None):
        super(CheckBox, self).__init__(parent)

        self.device = device

        self.layout = QHBoxLayout(self)
        self.b1 = QCheckBox("Hop TX LO")
        self.b1.setChecked(False)
        self.b1.stateChanged.connect(lambda: self.btnstate(self.b1))
        self.layout.addWidget(self.b1)
        self.setLayout(self.layout)

    def hop(self):
        if self.device.tx_lo > int(1e9 + 4e6):
            self.device.tx_lo = int(1e9 - 4e6)
        else:
            self.device.tx_lo = int(self.device.tx_lo + 1e6)

    def start_timer(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.hop)
        self.timer.start(100)

    def stop_timer(self):
        self.timer.stop()

    def btnstate(self, b):
        if b.isChecked() == True:
            self.start_timer()
        else:
            self.stop_timer()


class Slider(QWidget):
    device = None

    def __init__(self, minimum, maximum, device, dds_freq, parent=None):
        super(Slider, self).__init__(parent=parent)
        self.hLayout = QHBoxLayout(self)
        self.label = QLabel(self)
        self.hLayout.addWidget(self.label)

        self.vLayout = QVBoxLayout()
        spacerItem = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.vLayout.addItem(spacerItem)
        self.slider = QSlider(self)

        self.slider.setOrientation(QtCore.Qt.Horizontal)

        self.vLayout.addWidget(self.slider)
        spacerItem1 = QSpacerItem(0, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.vLayout.addItem(spacerItem1)
        self.hLayout.addLayout(self.vLayout)
        self.resize(self.sizeHint())

        self.minimum = minimum
        self.maximum = maximum
        self.slider.valueChanged.connect(self.setLabelValue)

        dds_freq_indx = (
            (dds_freq - minimum)
            / (maximum - minimum)
            * (self.slider.maximum() - self.slider.minimum())
        )
        dds_freq_indx = int(dds_freq_indx)
        self.x = dds_freq_indx
        self.slider.setValue(dds_freq_indx)
        self.setLabelValue(self.slider.value())
        self.device = device

    def setLabelValue(self, value):
        self.x = self.minimum + (
            float(value) / (self.slider.maximum() - self.slider.minimum())
        ) * (self.maximum - self.minimum)
        self.label.setText("DDS Frequency {0:.4g} Hz".format(self.x))
        if self.device:
            self.device.dds_single_tone(self.x, 0.9)


class ADIPlotter(QWidget):
    def __init__(self, classname, uri):

        super(ADIPlotter, self).__init__(parent=None)

        self.classname = classname
        self.q = Queue(maxsize=20)
        self.stream = eval("adi." + classname + "(uri='" + uri + "')")
        self.stream.sample_rate = 10000000
        dds_freq = 3e6
        if REAL_DEV_NAME not in classname.lower():
            self.stream.rx_lo = 1000000000
            self.stream.tx_lo = 1000000000
            self.stream.dds_single_tone(dds_freq, 0.9)
        self.stream.rx_buffer_size = 2 ** 12
        self.stream.rx_enabled_channels = [0]

        pg.setConfigOptions(antialias=True)
        self.traces = {}

        self.verticalLayout = QVBoxLayout(self)

        self.win = pg.GraphicsWindow(title="Spectrum Analyzer")
        self.win.setWindowTitle("Spectrum Analyzer")
        self.win.setGeometry(5, 115, 1910, 1070)

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
            title="WAVEFORM",
            row=1,
            col=1,
            axisItems={"bottom": wf_xaxis},
        )
        self.spectrum = self.win.addPlot(
            title="SPECTRUM",
            row=2,
            col=1,
            axisItems={"bottom": sp_xaxis},
        )
        self.waveform.showGrid(x=True, y=True)
        self.spectrum.showGrid(x=True, y=True)

        self.verticalLayout.addWidget(self.win)

        if REAL_DEV_NAME not in classname.lower():
            self.sp = Slider(
                -self.stream.sample_rate / 2,
                self.stream.sample_rate / 2,
                device=self.stream,
                dds_freq=dds_freq,
            )

            self.cb = CheckBox(device=self.stream)

            self.verticalLayout.addWidget(self.sp)
            self.verticalLayout.addWidget(self.cb)

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

        self.run_source = True
        self.thread = threading.Thread(target=self.source)
        self.thread.start()

    def source(self):
        print("Thread running")
        while self.run_source:
            data = self.stream.rx()
            try:
                self.q.put(data, block=False, timeout=4)
            except Full:
                continue

    def start(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
            QtGui.QApplication.instance().exec_()

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            if name == "peak":
                y = np.max(data_y)
                x = np.argmax(data_y)
                x = data_x[x]

                self.arrow.setPos(x, y)
                self.text.setPos(x, y + 15)

                self.text.setText("[%0.1f MHz, %0.1f dBFS]" % (x / 1e6, y))
            else:
                self.traces[name].setData(data_x, data_y)

        else:
            if name == "spectrum":
                self.traces[name] = self.spectrum.plot(pen="m", width=3)
                self.spectrum.setLogMode(x=False, y=False)
                self.spectrum.setYRange(self.min, 5, padding=0)
                if REAL_DEV_NAME in self.classname.lower():
                    start = 0
                else:
                    start = -1 * self.stream.sample_rate / 2
                self.spectrum.setXRange(
                    start,
                    self.stream.sample_rate / 2,
                    padding=0.005,
                )
            elif name == "waveform":
                self.traces[name] = self.waveform.plot(pen="c", width=3)
                self.waveform.setYRange(-(2 ** 11) - 200, 2 ** 11 + 200, padding=0)
                self.waveform.setXRange(
                    0,
                    self.stream.rx_buffer_size / self.stream.sample_rate,
                    padding=0.005,
                )
            elif name == "peak":
                self.text = pg.TextItem("Test", anchor=(0.5, -1.0))
                self.spectrum.addItem(self.text)
                ym = np.argmax(data_y)
                self.text.setPos(data_x[ym], data_y.max())
                self.arrow = pg.ArrowItem(pos=(data_x[ym], data_y.max()), angle=-90)
                self.spectrum.addItem(self.arrow)
                self.traces[name] = True

    def update(self):
        while not self.q.empty():
            wf_data = self.q.get()
            self.set_plotdata(
                name="waveform",
                data_x=self.x,
                data_y=np.real(wf_data),
            )
            sp_data = np.fft.fft(wf_data)
            sp_data = np.abs(np.fft.fftshift(sp_data)) / self.stream.rx_buffer_size
            sp_data = 20 * np.log10(sp_data / (2 ** 11))
            self.set_plotdata(name="spectrum", data_x=self.f, data_y=sp_data)
            self.set_plotdata(name="peak", data_x=self.f, data_y=sp_data)

    def animation(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1)
        self.show()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="ADI fast plotting app")
    parser.add_argument(
        "class", help="pyadi class name to use as plot source", action="store"
    )
    parser.add_argument("uri", help="URI of target device", action="store")
    args = vars(parser.parse_args())

    if args["class"] not in ["Pluto", "ad9361", "ad9364", "ad9363", "cn0532"]:
        raise Exception("Only AD936x based devices or CN0532 are supported")

    appq = QtGui.QApplication(sys.argv)

    app = ADIPlotter(args["class"], args["uri"])
    app.animation()
    appq.exec_()
    app.run_source = False
    app.thread.join()
