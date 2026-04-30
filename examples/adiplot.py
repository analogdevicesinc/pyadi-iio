import argparse
import sys
import threading
from queue import Full, Queue

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QSize, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from scipy.signal.windows import kaiser

import adi
from harmonic.container import HmcCard, HmcMainWindow
from harmonic.graph import HmcPlot
from harmonic.icons import HmcIcon
from harmonic.theme import HmcTheme

try:
    import genalyzer

    use_genalyzer = True
    print("Using genalyzer :)")
except ImportError:
    use_genalyzer = False

pg.setConfigOptions(antialias=True, background=None)

REAL_DEV_NAME = "cn05".lower()


class ADIPlotter(object):
    def setup_genalyzer(self, fftsize, fs):
        key = "adiplot"
        genalyzer.fa_create(key)
        genalyzer.fa_fsample(key, fs)
        genalyzer.fa_fdata(key, fs)
        genalyzer.fa_max_tone(key, "signal", genalyzer.FaCompTag.SIGNAL)
        genalyzer.fa_hd(key, 5)
        genalyzer.fa_ssb(key, genalyzer.FaSsb.DEFAULT, 120)
        return key

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
            self.update_interval = 10
            self.current_count = 0

        self.app = QApplication(sys.argv)
        self._theme = HmcTheme.default

        self.qmw = HmcMainWindow()
        self.qmw.setWindowTitle("ADI Spectrum Analyzer")
        self.qmw.resize(1200, 800)

        central = QWidget()
        self.qmw.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header ---
        header = QFrame()
        header.setProperty("class", "header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 8, 16, 8)

        title = QLabel("ADI Spectrum Analyzer")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()

        self.theme_btn = QPushButton()
        self.theme_btn.setProperty("class", "theme-toggle")
        self._moon_icon = HmcIcon("mdi6.weather-night", HmcTheme.Token.CONTENT_MEDIUM, parent=self.theme_btn)
        self._sun_icon = HmcIcon("mdi6.white-balance-sunny", HmcTheme.Token.CONTENT_MEDIUM, parent=self.theme_btn)
        self.theme_btn.setIcon(self._moon_icon)
        self.theme_btn.setIconSize(QSize(24, 24))
        self.theme_btn.setFixedSize(40, 40)
        self.theme_btn.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.theme_btn)

        main_layout.addWidget(header)

        # --- Plot area ---
        plot_area = QVBoxLayout()
        plot_area.setContentsMargins(16, 16, 16, 16)
        plot_area.setSpacing(12)

        # Waveform plot
        self.waveform = HmcPlot(theme=self._theme, title="Waveform")
        wf_card_layout = QVBoxLayout()
        wf_card = HmcCard(layout=wf_card_layout)
        wf_card_layout.addWidget(self.waveform)
        plot_area.addWidget(wf_card)

        # Spectrum plot
        self.spectrum = HmcPlot(theme=self._theme, title="Spectrum")
        sp_card_layout = QVBoxLayout()
        sp_card = HmcCard(layout=sp_card_layout)
        sp_card_layout.addWidget(self.spectrum)
        plot_area.addWidget(sp_card)

        # --- Measurements panel ---
        meas_group = QGroupBox("Measurements")
        meas_layout = QHBoxLayout(meas_group)
        meas_layout.setSpacing(24)

        self.lbl_peak = QLabel("Peak: —")
        self.lbl_peak.setProperty("class", "subheading")
        self.lbl_freq = QLabel("Frequency: —")
        self.lbl_freq.setProperty("class", "subheading")
        self.lbl_amp = QLabel("Amplitude: —")
        self.lbl_amp.setProperty("class", "subheading")
        meas_layout.addWidget(self.lbl_peak)
        meas_layout.addWidget(self.lbl_freq)
        meas_layout.addWidget(self.lbl_amp)
        meas_layout.addStretch()

        self.genalyzer_labels = {}
        plot_area.addWidget(meas_group)
        if use_genalyzer:
            from PySide6.QtWidgets import QGridLayout, QScrollArea

            ga_group = QGroupBox("Genalyzer")
            ga_group.setMinimumHeight(200)
            ga_group.setMaximumHeight(300)
            ga_inner = QWidget()
            self.ga_grid = QGridLayout(ga_inner)
            self.ga_grid.setSpacing(8)
            self._ga_col_count = 4

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(ga_inner)
            scroll.setFrameShape(QFrame.Shape.NoFrame)
            scroll.setStyleSheet("QScrollArea { background: transparent; }")
            ga_inner.setStyleSheet("background: transparent;")

            ga_box = QVBoxLayout(ga_group)
            ga_box.setContentsMargins(0, 0, 0, 0)
            ga_box.addWidget(scroll)
            plot_area.addWidget(ga_group)

        main_layout.addLayout(plot_area)

        # --- Configure plots ---
        self.traces = {}

        self.x = np.arange(0, self.stream.rx_buffer_size) / self.stream.sample_rate
        self.f = np.linspace(
            -1 * self.stream.sample_rate / 2,
            self.stream.sample_rate / 2,
            self.stream.rx_buffer_size,
        )

        self.counter = 0
        self.min = -100
        self.window = kaiser(self.stream.rx_buffer_size, beta=38)

        self.qmw.show()

        self.run_source = True
        self.thread = threading.Thread(target=self.source)
        self.thread.start()

        self.markers_added = False

    def _toggle_theme(self):
        if self._theme is HmcTheme.LIGHT:
            self._theme = HmcTheme.DARK
            self.theme_btn.setIcon(self._sun_icon)
        else:
            self._theme = HmcTheme.LIGHT
            self.theme_btn.setIcon(self._moon_icon)
        self.qmw.theme = self._theme
        self._recolor_traces()

    def _recolor_traces(self):
        if "waveform" in self.traces:
            self.traces["waveform"].setPen(
                pg.mkPen(self._theme.categorical[0], width=2)
            )
        if "spectrum" in self.traces:
            self.traces["spectrum"].setPen(
                pg.mkPen(self._theme.categorical[1], width=2)
            )
        if self.markers_added:
            self.text_peak.setColor(self._theme.content_default)

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
        self.app.exec()

    def add_markers(self):
        spectrum_trace = self.traces.get("spectrum")
        if spectrum_trace is None:
            return
        self.curve_point = pg.CurvePoint(spectrum_trace)
        self.spectrum.addItem(self.curve_point)
        self.text_peak = pg.TextItem("", anchor=(0.5, 1.0))
        self.text_peak.setColor(self._theme.content_default)
        self.text_peak.setParentItem(self.curve_point)
        self.markers_added = True

    def set_plotdata(self, name, data_x, data_y):
        if name in self.traces:
            self.traces[name].setData(data_x, data_y)
        elif name == "spectrum":
            self.traces[name] = self.spectrum.plot(
                pen=pg.mkPen(self._theme.categorical[1], width=2)
            )
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
            self.spectrum.setLabel("bottom", "Frequency", units="Hz")
            self.spectrum.setLabel("left", "Power", units="dB")
        elif name == "waveform":
            self.traces[name] = self.waveform.plot(
                pen=pg.mkPen(self._theme.categorical[0], width=2)
            )
            self.waveform.setYRange(-(2 ** 11) - 200, 2 ** 11 + 200, padding=0)
            self.waveform.setXRange(
                0, self.stream.rx_buffer_size / self.stream.sample_rate, padding=0.005,
            )
            self.waveform.setLabel("bottom", "Time", units="s")
            self.waveform.setLabel("left", "Amplitude")

    def update(self):
        while not self.q.empty():
            wf_data = self.q.get()
            self.set_plotdata(
                name="waveform", data_x=self.x, data_y=np.real(wf_data),
            )

            genalyzer_results = None
            if use_genalyzer:
                self.current_count = self.current_count + 1
                if self.current_count >= self.update_interval:
                    self.current_count = 0
                    try:
                        fft_out = genalyzer.fft(
                            wf_data.astype(np.complex128),
                            1,
                            self.stream.rx_buffer_size,
                            genalyzer.Window.NO_WINDOW,
                        )
                        genalyzer_results = genalyzer.fft_analysis(
                            self.c, fft_out, self.stream.rx_buffer_size,
                        )
                    except Exception as e:
                        print("genalyzer error:", e)

            sp_data = np.fft.fft(wf_data)
            sp_data = np.abs(np.fft.fftshift(sp_data)) / self.stream.rx_buffer_size
            sp_data = 20 * np.log10(sp_data / (2 ** 11))

            self.set_plotdata(name="spectrum", data_x=self.f, data_y=sp_data)

            if use_genalyzer and self.current_count != 0:
                return

            if not self.markers_added:
                self.add_markers()

            index = np.argmax(sp_data)

            if self.markers_added:
                self.curve_point.setPos(float(index) / (len(self.f) - 1))
                self.text_peak.setText(
                    "[{:.1f}, {:.1f}]".format(self.f[index], sp_data[index])
                )

            self.lbl_peak.setText(
                "Peak: [{:.1f} Hz, {:.1f} dB]".format(self.f[index], sp_data[index])
            )
            self.lbl_freq.setText("Frequency: {:.2f} Hz".format(self.f[index]))
            self.lbl_amp.setText("Amplitude: {:.2f} dB".format(sp_data[index]))

            if use_genalyzer and genalyzer_results:
                self._update_genalyzer_labels(genalyzer_results)

    def _update_genalyzer_labels(self, results):
        for i, (key, value) in enumerate(results.items()):
            if key not in self.genalyzer_labels:
                lbl = QLabel()
                lbl.setProperty("class", "caption")
                row = i // self._ga_col_count
                col = i % self._ga_col_count
                self.ga_grid.addWidget(lbl, row, col)
                self.genalyzer_labels[key] = lbl
            self.genalyzer_labels[key].setText("{}: {:.2f}".format(key, value))

    def animation(self):
        timer = QTimer()
        timer.timeout.connect(self.update)
        timer.start(1)
        self.start()
        self.run_source = False
        self.thread.join()


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
