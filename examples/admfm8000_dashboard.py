# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""ADMFM8000 FMCW Transmitter Dashboard — PySide6 + pyqtgraph GUI.

Provides tabbed control for Single Tone, Parallel Port, Digital Ramp
Generator, and RAM modes of the ADMFM8000 system.

Usage:
    python admfm8000_dashboard.py [--uri ip:10.32.22.147] [--theme dark]
"""

import math
import sys

import numpy as np
import pyqtgraph as pg
from harmonic.container import HmcCard, HmcMainWindow
from harmonic.graph import HmcPlot
from harmonic.icons import HmcIcon, HmcLogoIcon
from harmonic.theme import HmcTheme
from harmonic.toggle import HmcToggleSwitch
from PySide6.QtCore import QSize
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

pg.setConfigOptions(antialias=True, background=None)

FREQ_MIN_GHZ = 23.8
FREQ_MAX_GHZ = 26.8
NUM_PROFILES = 8


# ---------------------------------------------------------------------------
# Single Tone tab
# ---------------------------------------------------------------------------


class SingleToneTab(QWidget):
    def __init__(self, theme: HmcTheme, fmcw=None):
        super().__init__()
        self._theme = theme
        self._fmcw = fmcw
        self._cards = []
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        heading = QLabel("Single Tone Profiles")
        heading.setProperty("class", "heading")
        layout.addWidget(heading)

        grid = QGridLayout()
        grid.setSpacing(16)

        for i in range(NUM_PROFILES):
            card_layout = QVBoxLayout()
            card_layout.setSpacing(8)
            card = HmcCard(layout=card_layout)

            lbl = QLabel(f"Profile {i}")
            lbl.setProperty("class", "subheading")
            card_layout.addWidget(lbl)

            freq_lbl = QLabel("Frequency (GHz)")
            freq_lbl.setProperty("class", "caption")
            card_layout.addWidget(freq_lbl)
            freq_spin = QDoubleSpinBox()
            freq_spin.setRange(FREQ_MIN_GHZ, FREQ_MAX_GHZ)
            freq_spin.setDecimals(4)
            freq_spin.setSingleStep(0.1)
            freq_spin.setValue(25.3)
            freq_spin.setSuffix(" GHz")
            card_layout.addWidget(freq_spin)

            scale_lbl = QLabel("Scale")
            scale_lbl.setProperty("class", "caption")
            card_layout.addWidget(scale_lbl)
            scale_spin = QDoubleSpinBox()
            scale_spin.setRange(0.0, 1.0)
            scale_spin.setDecimals(2)
            scale_spin.setSingleStep(0.01)
            scale_spin.setValue(1.0)
            card_layout.addWidget(scale_spin)

            phase_lbl = QLabel("Phase (rad)")
            phase_lbl.setProperty("class", "caption")
            card_layout.addWidget(phase_lbl)
            phase_spin = QDoubleSpinBox()
            phase_spin.setRange(0.0, 2 * math.pi)
            phase_spin.setDecimals(3)
            phase_spin.setSingleStep(0.01)
            phase_spin.setValue(0.0)
            card_layout.addWidget(phase_spin)

            btn_row = QHBoxLayout()
            btn_apply = QPushButton("Apply")
            btn_apply.setProperty("class", "secondary")
            btn_select = QPushButton("Select")
            btn_row.addWidget(btn_apply)
            btn_row.addWidget(btn_select)
            card_layout.addLayout(btn_row)

            row, col = divmod(i, 4)
            grid.addWidget(card, row, col)

            self._cards.append(
                {
                    "freq": freq_spin,
                    "scale": scale_spin,
                    "phase": phase_spin,
                    "apply": btn_apply,
                    "select": btn_select,
                    "profile": i,
                }
            )

        layout.addLayout(grid)
        layout.addStretch()

    def _connect_signals(self):
        for card in self._cards:
            p = card["profile"]
            card["apply"].clicked.connect(lambda _, p=p: self._on_apply(p))
            card["select"].clicked.connect(lambda _, p=p: self._on_select(p))

    def _on_apply(self, profile):
        c = self._cards[profile]
        freq = c["freq"].value() * 1e9
        scale = c["scale"].value()
        phase = c["phase"].value()
        if self._fmcw:
            try:
                self._fmcw.single_tone_config(
                    profile=profile, frequency=freq, scale=scale, phase=phase
                )
                self._status(
                    f"Profile {profile}: {freq/1e9:.4f} GHz, scale={scale}, phase={phase:.3f} rad"
                )
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(
                f"[dry-run] single_tone_config(profile={profile}, "
                f"frequency={freq:.0f}, scale={scale}, phase={phase:.3f})"
            )

    def _on_select(self, profile):
        if self._fmcw:
            try:
                self._fmcw.profile = profile
                self._status(f"Active profile set to {profile}")
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(f"[dry-run] profile = {profile}")

    def _status(self, msg):
        w = self.window()
        if isinstance(w, QMainWindow):
            w.statusBar().showMessage(msg, 5000)


# ---------------------------------------------------------------------------
# Parallel Port tab
# ---------------------------------------------------------------------------


class ParallelPortTab(QWidget):
    def __init__(self, theme: HmcTheme, fmcw=None):
        super().__init__()
        self._theme = theme
        self._fmcw = fmcw
        self._freqs = None
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        heading = QLabel("Parallel Port")
        heading.setProperty("class", "heading")
        layout.addWidget(heading)

        # --- Controls card ---
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setSpacing(12)
        ctrl_card = HmcCard(layout=ctrl_layout)

        file_row = QHBoxLayout()
        file_lbl = QLabel("CSV File")
        file_lbl.setProperty("class", "subheading")
        file_row.addWidget(file_lbl)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText(
            "Select a CSV file with frequency values (Hz)..."
        )
        self.file_edit.setReadOnly(True)
        file_row.addWidget(self.file_edit)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setProperty("class", "tertiary")
        self.btn_browse.setIcon(
            HmcIcon("mdi6.folder-open", HmcTheme.Token.CONTENT_DEFAULT)
        )
        file_row.addWidget(self.btn_browse)
        ctrl_layout.addLayout(file_row)

        params_row = QHBoxLayout()
        params_row.setSpacing(16)

        cyclic_lbl = QLabel("Cyclic")
        cyclic_lbl.setProperty("class", "caption")
        params_row.addWidget(cyclic_lbl)
        self.cyclic_toggle = HmcToggleSwitch("", self._theme)
        self.cyclic_toggle.setChecked(True)
        params_row.addWidget(self.cyclic_toggle)

        sweep_lbl = QLabel("Sweep Time (us)")
        sweep_lbl.setProperty("class", "caption")
        params_row.addWidget(sweep_lbl)
        self.sweep_spin = QDoubleSpinBox()
        self.sweep_spin.setRange(1.0, 10000.0)
        self.sweep_spin.setDecimals(1)
        self.sweep_spin.setSingleStep(10.0)
        self.sweep_spin.setValue(100.0)
        self.sweep_spin.setSuffix(" us")
        params_row.addWidget(self.sweep_spin)
        params_row.addStretch()

        ctrl_layout.addLayout(params_row)

        btn_row = QHBoxLayout()
        self.btn_start = QPushButton("Start")
        self.btn_start.setIcon(HmcIcon("mdi6.play", HmcTheme.Token.CONTENT_INVERSE))
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setProperty("class", "danger")
        self.btn_stop.setIcon(HmcIcon("mdi6.stop", HmcTheme.Token.CONTENT_INVERSE))
        btn_row.addWidget(self.btn_start)
        btn_row.addWidget(self.btn_stop)
        btn_row.addStretch()
        ctrl_layout.addLayout(btn_row)

        layout.addWidget(ctrl_card)

        # --- Preview plot ---
        plot_layout = QVBoxLayout()
        self.plot = HmcPlot(theme=self._theme, title="Frequency preview")
        self.plot.setLabel("bottom", "Sample index")
        self.plot.setLabel("left", "Frequency", units="Hz")
        plot_layout.addWidget(self.plot)
        plot_card = HmcCard(layout=plot_layout)
        layout.addWidget(plot_card)

    def _connect_signals(self):
        self.btn_browse.clicked.connect(self._browse_csv)
        self.btn_start.clicked.connect(self._on_start)
        self.btn_stop.clicked.connect(self._on_stop)

    def _browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        self.file_edit.setText(path)
        try:
            self._freqs = np.loadtxt(path, delimiter=",", ndmin=1).flatten()
            self._update_preview()
            self._status(f"Loaded {len(self._freqs)} frequency values")
        except Exception as ex:
            self._status(f"Error loading CSV: {ex}")
            self._freqs = None

    def _update_preview(self):
        self.plot.clear()
        if self._freqs is not None and len(self._freqs) > 0:
            self.plot.plot(
                np.arange(len(self._freqs)),
                self._freqs,
                pen=pg.mkPen(self._theme.categorical[0], width=2),
            )

    def _on_start(self):
        if self._freqs is None or len(self._freqs) == 0:
            self._status("No frequency data loaded — select a CSV file first")
            return
        cyclic = self.cyclic_toggle.isChecked()
        sweep_us = self.sweep_spin.value()
        rate = len(self._freqs) / (sweep_us * 1e-6)
        if self._fmcw:
            try:
                self._fmcw.parallel_port_config(
                    enable=True, frequency_np=self._freqs, cyclic=cyclic, rate=rate
                )
                self._status(
                    f"Parallel Port started: {len(self._freqs)} pts, rate={rate:.0f} SPS"
                )
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(
                f"[dry-run] parallel_port_config(enable=True, "
                f"len={len(self._freqs)}, cyclic={cyclic}, rate={rate:.0f})"
            )

    def _on_stop(self):
        if self._fmcw:
            try:
                self._fmcw.parallel_port_config(enable=False)
                self._status("Parallel Port stopped")
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status("[dry-run] parallel_port_config(enable=False)")

    def _status(self, msg):
        w = self.window()
        if isinstance(w, QMainWindow):
            w.statusBar().showMessage(msg, 5000)


# ---------------------------------------------------------------------------
# Digital Ramp Generator tab
# ---------------------------------------------------------------------------

DRG_MODES = [
    ("Bidirectional Continuous", "BIDIRECTIONAL_CONTINUOUS"),
    ("Ramp Up", "RAMP_UP"),
    ("Ramp Down", "RAMP_DOWN"),
    ("Bidirectional", "BIDIRECTIONAL"),
]


class DigitalRampTab(QWidget):
    def __init__(self, theme: HmcTheme, fmcw=None):
        super().__init__()
        self._theme = theme
        self._fmcw = fmcw
        self._build_ui()
        self._connect_signals()
        self._on_mode_changed()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- Controls card (left side) ---
        ctrl_layout = QVBoxLayout()
        ctrl_layout.setSpacing(12)
        ctrl_card = HmcCard(layout=ctrl_layout)

        heading = QLabel("DRG Configuration")
        heading.setProperty("class", "subheading")
        ctrl_layout.addWidget(heading)

        mode_lbl = QLabel("Mode")
        mode_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(mode_lbl)
        self.mode_combo = QComboBox()
        for display, _ in DRG_MODES:
            self.mode_combo.addItem(display)
        ctrl_layout.addWidget(self.mode_combo)

        freq_min_lbl = QLabel("Freq Min (GHz)")
        freq_min_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(freq_min_lbl)
        self.freq_min_spin = QDoubleSpinBox()
        self.freq_min_spin.setRange(FREQ_MIN_GHZ, FREQ_MAX_GHZ)
        self.freq_min_spin.setDecimals(4)
        self.freq_min_spin.setSingleStep(0.1)
        self.freq_min_spin.setValue(FREQ_MIN_GHZ)
        self.freq_min_spin.setSuffix(" GHz")
        ctrl_layout.addWidget(self.freq_min_spin)

        freq_max_lbl = QLabel("Freq Max (GHz)")
        freq_max_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(freq_max_lbl)
        self.freq_max_spin = QDoubleSpinBox()
        self.freq_max_spin.setRange(FREQ_MIN_GHZ, FREQ_MAX_GHZ)
        self.freq_max_spin.setDecimals(4)
        self.freq_max_spin.setSingleStep(0.1)
        self.freq_max_spin.setValue(FREQ_MAX_GHZ)
        self.freq_max_spin.setSuffix(" GHz")
        ctrl_layout.addWidget(self.freq_max_spin)

        inc_lbl = QLabel("Inc Ramp Time (us)")
        inc_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(inc_lbl)
        self.inc_time_spin = QDoubleSpinBox()
        self.inc_time_spin.setRange(0.1, 10000.0)
        self.inc_time_spin.setDecimals(1)
        self.inc_time_spin.setSingleStep(10.0)
        self.inc_time_spin.setValue(50.0)
        self.inc_time_spin.setSuffix(" us")
        ctrl_layout.addWidget(self.inc_time_spin)

        dec_lbl = QLabel("Dec Ramp Time (us)")
        dec_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(dec_lbl)
        self.dec_time_spin = QDoubleSpinBox()
        self.dec_time_spin.setRange(0.1, 10000.0)
        self.dec_time_spin.setDecimals(1)
        self.dec_time_spin.setSingleStep(10.0)
        self.dec_time_spin.setValue(50.0)
        self.dec_time_spin.setSuffix(" us")
        ctrl_layout.addWidget(self.dec_time_spin)

        # --- IIO Backend section ---
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setProperty("class", "divider")
        ctrl_layout.addWidget(divider)

        delay_lbl = QLabel("Ramp Delay (us)")
        delay_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(delay_lbl)
        self.delay_spin = QDoubleSpinBox()
        self.delay_spin.setRange(0.0, 10000.0)
        self.delay_spin.setDecimals(1)
        self.delay_spin.setSingleStep(10.0)
        self.delay_spin.setValue(50.0)
        self.delay_spin.setSuffix(" us")
        ctrl_layout.addWidget(self.delay_spin)

        burst_count_lbl = QLabel("Burst Count")
        burst_count_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(burst_count_lbl)
        self.burst_count_spin = QSpinBox()
        self.burst_count_spin.setRange(0, 100)
        self.burst_count_spin.setValue(0)
        ctrl_layout.addWidget(self.burst_count_spin)

        burst_delay_lbl = QLabel("Burst Delay (us)")
        burst_delay_lbl.setProperty("class", "caption")
        ctrl_layout.addWidget(burst_delay_lbl)
        self.burst_delay_spin = QDoubleSpinBox()
        self.burst_delay_spin.setRange(0.0, 10000.0)
        self.burst_delay_spin.setDecimals(1)
        self.burst_delay_spin.setSingleStep(10.0)
        self.burst_delay_spin.setValue(100.0)
        self.burst_delay_spin.setSuffix(" us")
        ctrl_layout.addWidget(self.burst_delay_spin)

        self._backend_widgets = [
            delay_lbl, self.delay_spin,
            burst_count_lbl, self.burst_count_spin,
            burst_delay_lbl, self.burst_delay_spin,
        ]

        ctrl_layout.addSpacing(8)

        btn_row = QHBoxLayout()
        self.btn_apply = QPushButton("Apply")
        self.btn_apply.setIcon(HmcIcon("mdi6.play", HmcTheme.Token.CONTENT_INVERSE))
        self.btn_disable = QPushButton("Disable")
        self.btn_disable.setProperty("class", "danger")
        btn_row.addWidget(self.btn_apply)
        btn_row.addWidget(self.btn_disable)
        ctrl_layout.addLayout(btn_row)

        ctrl_layout.addStretch()
        layout.addWidget(ctrl_card, 1)

        # --- Preview plot (right side) ---
        plot_outer = QVBoxLayout()
        plot_heading = QLabel("Ramp Preview")
        plot_heading.setProperty("class", "heading")
        plot_outer.addWidget(plot_heading)

        plot_layout = QVBoxLayout()
        self.plot = HmcPlot(theme=self._theme, title="DRG frequency ramp")
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", "Frequency", units="Hz")
        plot_layout.addWidget(self.plot)
        plot_card = HmcCard(layout=plot_layout)
        plot_outer.addWidget(plot_card)

        layout.addLayout(plot_outer, 2)

    def _connect_signals(self):
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        self.freq_min_spin.valueChanged.connect(lambda: self._update_preview())
        self.freq_max_spin.valueChanged.connect(lambda: self._update_preview())
        self.inc_time_spin.valueChanged.connect(lambda: self._update_preview())
        self.dec_time_spin.valueChanged.connect(lambda: self._update_preview())
        self.delay_spin.valueChanged.connect(lambda: self._update_preview())
        self.burst_count_spin.valueChanged.connect(lambda: self._update_preview())
        self.burst_delay_spin.valueChanged.connect(lambda: self._update_preview())
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_disable.clicked.connect(self._on_disable)

    def _on_mode_changed(self):
        _, mode_key = DRG_MODES[self.mode_combo.currentIndex()]
        enabled = mode_key != "BIDIRECTIONAL_CONTINUOUS"
        for w in self._backend_widgets:
            w.setEnabled(enabled)
        self._update_preview()

    def _add_ramp(self, t, f, direction, f_min, f_max, inc_time, dec_time, t_offset):
        n = 200
        if direction == "up":
            t_seg = np.linspace(0, inc_time, n) + t_offset
            f_seg = np.linspace(f_min, f_max, n)
        else:
            t_seg = np.linspace(0, dec_time, n) + t_offset
            f_seg = np.linspace(f_max, f_min, n)
        t.append(t_seg)
        f.append(f_seg)
        return t_seg[-1]

    def _add_dwell(self, t, f, duration, level, t_offset):
        if duration <= 0:
            return t_offset
        n = 50
        t.append(np.linspace(0, duration, n) + t_offset)
        f.append(np.full(n, level))
        return t_offset + duration

    @staticmethod
    def _ramp_directions(mode_key):
        if mode_key == "RAMP_UP":
            return ["up"]
        elif mode_key == "RAMP_DOWN":
            return ["down"]
        else:
            return ["up", "down"]

    def _next_direction(self, directions, idx):
        return directions[idx % len(directions)]

    def _dwell_level(self, mode_key, direction, f_min, f_max):
        if mode_key == "RAMP_UP":
            return f_min
        elif mode_key == "RAMP_DOWN":
            return f_max
        else:
            return f_max if direction == "up" else f_min

    def _update_preview(self):
        self.plot.clear()
        f_min = self.freq_min_spin.value() * 1e9
        f_max = self.freq_max_spin.value() * 1e9
        if f_min >= f_max:
            return

        inc_time = self.inc_time_spin.value() * 1e-6
        dec_time = self.dec_time_spin.value() * 1e-6
        ramp_delay = self.delay_spin.value() * 1e-6
        burst_count = self.burst_count_spin.value()
        burst_delay = self.burst_delay_spin.value() * 1e-6

        _, mode_key = DRG_MODES[self.mode_combo.currentIndex()]
        directions = self._ramp_directions(mode_key)
        is_continuous = mode_key == "BIDIRECTIONAL_CONTINUOUS"

        t_segs = []
        f_segs = []
        t_off = 0.0

        if is_continuous:
            for i in range(4):
                d = self._next_direction(directions, i)
                t_off = self._add_ramp(
                    t_segs, f_segs, d, f_min, f_max, inc_time, dec_time, t_off
                )
        elif burst_count == 0:
            for i in range(2):
                d = self._next_direction(directions, i)
                t_off = self._add_ramp(
                    t_segs, f_segs, d, f_min, f_max, inc_time, dec_time, t_off
                )
                t_off = self._add_dwell(
                    t_segs, f_segs, ramp_delay,
                    self._dwell_level(mode_key, d, f_min, f_max), t_off,
                )
        else:
            ramp_idx = 0
            for _ in range(2):
                for j in range(burst_count):
                    d = self._next_direction(directions, ramp_idx)
                    t_off = self._add_ramp(
                        t_segs, f_segs, d, f_min, f_max, inc_time, dec_time, t_off
                    )
                    ramp_idx += 1
                    if j < burst_count - 1:
                        t_off = self._add_dwell(
                            t_segs, f_segs, ramp_delay,
                            self._dwell_level(mode_key, d, f_min, f_max), t_off,
                        )

                d = self._next_direction(directions, ramp_idx - 1)
                t_off = self._add_dwell(
                    t_segs, f_segs, burst_delay,
                    self._dwell_level(mode_key, d, f_min, f_max), t_off,
                )

        t_all = np.concatenate(t_segs)
        f_all = np.concatenate(f_segs)
        self.plot.plot(
            t_all, f_all, pen=pg.mkPen(self._theme.categorical[0], width=2)
        )

    def _on_apply(self):
        _, mode_key = DRG_MODES[self.mode_combo.currentIndex()]
        f_min = self.freq_min_spin.value() * 1e9
        f_max = self.freq_max_spin.value() * 1e9
        inc_time = self.inc_time_spin.value() * 1e-6
        dec_time = self.dec_time_spin.value() * 1e-6
        toggle_en = 0 if mode_key == "BIDIRECTIONAL_CONTINUOUS" else 1
        delay = self.delay_spin.value() * 1e-6
        burst_count = self.burst_count_spin.value()
        burst_delay_val = self.burst_delay_spin.value() * 1e-6

        kwargs = {
            "toggle_en": toggle_en,
            "ramp_delay": delay,
            "burst_count": burst_count,
            "burst_delay": burst_delay_val,
        }

        if self._fmcw:
            try:
                from adi.ad9910 import ad9910

                mode = ad9910.digital_ramp_generator.mode[mode_key]
                self._fmcw.digital_ramp_config(
                    enable=True,
                    mode=mode,
                    freq_min=f_min,
                    freq_max=f_max,
                    inc_ramp_time=inc_time,
                    dec_ramp_time=dec_time,
                    **kwargs,
                )
                self._status(
                    f"DRG enabled: {mode_key}, {f_min/1e9:.4f}–{f_max/1e9:.4f} GHz"
                )
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(
                f"[dry-run] digital_ramp_config(enable=True, mode={mode_key}, "
                f"freq_min={f_min:.0f}, freq_max={f_max:.0f}, "
                f"inc_ramp_time={inc_time}, dec_ramp_time={dec_time}, {kwargs})"
            )

    def _on_disable(self):
        if self._fmcw:
            try:
                self._fmcw.digital_ramp_config(enable=False)
                self._status("DRG disabled")
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status("[dry-run] digital_ramp_config(enable=False)")

    def _status(self, msg):
        w = self.window()
        if isinstance(w, QMainWindow):
            w.statusBar().showMessage(msg, 5000)


# ---------------------------------------------------------------------------
# RAM Mode tab
# ---------------------------------------------------------------------------

RAM_MODES = [
    ("Direct Switch", "DIRECT_SWITCH"),
    ("Ramp Up", "RAMP_UP"),
    ("Bidirectional", "BIDIRECTIONAL"),
    ("Bidirectional Continuous", "BIDIRECTIONAL_CONTINUOUS"),
    ("Ramp Up Continuous", "RAMP_UP_CONTINUOUS"),
]


class RAMProfileWidget(QWidget):
    """Configuration widget for a single RAM profile."""

    def __init__(self, profile: int):
        super().__init__()
        self._profile = profile
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        mode_lbl = QLabel("Mode")
        mode_lbl.setProperty("class", "caption")
        layout.addWidget(mode_lbl)
        self.mode_combo = QComboBox()
        for display, _ in RAM_MODES:
            self.mode_combo.addItem(display)
        self.mode_combo.setCurrentIndex(4)
        layout.addWidget(self.mode_combo)

        start_lbl = QLabel("Address Start")
        start_lbl.setProperty("class", "caption")
        layout.addWidget(start_lbl)
        self.addr_start_spin = QSpinBox()
        self.addr_start_spin.setRange(0, 1023)
        self.addr_start_spin.setValue(0)
        layout.addWidget(self.addr_start_spin)

        end_lbl = QLabel("Address End")
        end_lbl.setProperty("class", "caption")
        layout.addWidget(end_lbl)
        self.addr_end_spin = QSpinBox()
        self.addr_end_spin.setRange(0, 1023)
        self.addr_end_spin.setValue(999)
        layout.addWidget(self.addr_end_spin)

        rate_lbl = QLabel("Rate (MSPS)")
        rate_lbl.setProperty("class", "caption")
        layout.addWidget(rate_lbl)
        self.rate_spin = QDoubleSpinBox()
        self.rate_spin.setRange(0.001, 250.0)
        self.rate_spin.setDecimals(3)
        self.rate_spin.setSingleStep(1.0)
        self.rate_spin.setValue(10.0)
        self.rate_spin.setSuffix(" MSPS")
        layout.addWidget(self.rate_spin)

        self.btn_apply = QPushButton("Apply Profile")
        self.btn_apply.setProperty("class", "secondary")
        layout.addWidget(self.btn_apply)

        layout.addStretch()

    @property
    def profile(self):
        return self._profile

    @property
    def mode_key(self):
        _, key = RAM_MODES[self.mode_combo.currentIndex()]
        return key

    @property
    def addr_range(self):
        return (self.addr_start_spin.value(), self.addr_end_spin.value())

    @property
    def rate_hz(self):
        return self.rate_spin.value() * 1e6


class RAMTab(QWidget):
    def __init__(self, theme: HmcTheme, fmcw=None):
        super().__init__()
        self._theme = theme
        self._fmcw = fmcw
        self._freqs = None
        self._profiles = []
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- Left: vertical profile tabs inside a card ---
        self.profile_tabs = QTabWidget()
        self.profile_tabs.setTabPosition(QTabWidget.TabPosition.West)
        self.profile_tabs.tabBar().setProperty("class", "vertical")

        for i in range(NUM_PROFILES):
            pw = RAMProfileWidget(i)
            self.profile_tabs.addTab(pw, f"P{i}")
            self._profiles.append(pw)

        profiles_card_layout = QVBoxLayout()
        profiles_card_layout.setContentsMargins(0, 0, 0, 0)
        profiles_heading = QLabel("Profile Configuration")
        profiles_heading.setProperty("class", "subheading")
        profiles_heading.setContentsMargins(16, 12, 0, 0)
        profiles_card_layout.addWidget(profiles_heading)
        profiles_card_layout.addWidget(self.profile_tabs)
        profiles_card = HmcCard(layout=profiles_card_layout)
        layout.addWidget(profiles_card, 1)

        # --- Right: data card + preview plot ---
        right = QVBoxLayout()
        right.setSpacing(16)

        # Data card
        data_layout = QVBoxLayout()
        data_layout.setSpacing(8)
        data_card = HmcCard(layout=data_layout)

        data_heading = QLabel("RAM Data")
        data_heading.setProperty("class", "subheading")
        data_layout.addWidget(data_heading)

        file_row = QHBoxLayout()
        file_lbl = QLabel("CSV File")
        file_lbl.setProperty("class", "caption")
        file_row.addWidget(file_lbl)
        self.file_edit = QLineEdit()
        self.file_edit.setPlaceholderText("Frequency values (Hz), one per line...")
        self.file_edit.setReadOnly(True)
        file_row.addWidget(self.file_edit)
        self.btn_browse = QPushButton("Browse")
        self.btn_browse.setProperty("class", "tertiary")
        self.btn_browse.setIcon(
            HmcIcon("mdi6.folder-open", HmcTheme.Token.CONTENT_DEFAULT)
        )
        file_row.addWidget(self.btn_browse)
        data_layout.addLayout(file_row)

        self.data_info = QLabel("No data loaded")
        self.data_info.setProperty("class", "caption")
        data_layout.addWidget(self.data_info)

        btn_row = QHBoxLayout()
        self.btn_enable = QPushButton("Enable RAM")
        self.btn_enable.setIcon(HmcIcon("mdi6.play", HmcTheme.Token.CONTENT_INVERSE))
        self.btn_disable = QPushButton("Disable RAM")
        self.btn_disable.setProperty("class", "danger")
        btn_row.addWidget(self.btn_enable)
        btn_row.addWidget(self.btn_disable)
        btn_row.addStretch()
        data_layout.addLayout(btn_row)

        right.addWidget(data_card)

        # Preview plot
        plot_layout = QVBoxLayout()
        self.plot = HmcPlot(theme=self._theme, title="RAM frequency preview")
        self.plot.setLabel("bottom", "Sample index")
        self.plot.setLabel("left", "Frequency", units="Hz")
        plot_layout.addWidget(self.plot)
        plot_card = HmcCard(layout=plot_layout)
        right.addWidget(plot_card)

        layout.addLayout(right, 2)

    def _connect_signals(self):
        self.btn_browse.clicked.connect(self._browse_csv)
        self.btn_enable.clicked.connect(self._on_enable)
        self.btn_disable.clicked.connect(self._on_disable)
        for pw in self._profiles:
            pw.btn_apply.clicked.connect(lambda _, p=pw: self._on_apply_profile(p))

    def _browse_csv(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        if not path:
            return
        self.file_edit.setText(path)
        try:
            self._freqs = np.loadtxt(path, delimiter=",", ndmin=1).flatten()
            self.data_info.setText(f"{len(self._freqs)} values loaded")
            self._update_preview()
            self._status(f"Loaded {len(self._freqs)} frequency values for RAM")
        except Exception as ex:
            self._status(f"Error loading CSV: {ex}")
            self._freqs = None
            self.data_info.setText("Error loading file")

    def _update_preview(self):
        self.plot.clear()
        if self._freqs is not None and len(self._freqs) > 0:
            self.plot.plot(
                np.arange(len(self._freqs)),
                self._freqs,
                pen=pg.mkPen(self._theme.categorical[0], width=2),
            )

    def _on_apply_profile(self, pw: RAMProfileWidget):
        profile = pw.profile
        mode_key = pw.mode_key
        addr_range = pw.addr_range
        rate = pw.rate_hz

        if self._fmcw:
            try:
                from adi.ad9910 import ad9910

                mode = ad9910.ram_control.mode[mode_key]
                self._fmcw.ram_control_profile_config(
                    profile=profile, mode=mode, addr_range=addr_range, rate=rate
                )
                self._status(
                    f"RAM Profile {profile}: {mode_key}, "
                    f"addr={addr_range}, rate={rate/1e6:.3f} MSPS"
                )
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(
                f"[dry-run] ram_control_profile_config(profile={profile}, "
                f"mode={mode_key}, addr_range={addr_range}, rate={rate:.0f})"
            )

    def _on_enable(self):
        if self._freqs is None or len(self._freqs) == 0:
            self._status("No frequency data loaded — select a CSV file first")
            return
        if self._fmcw:
            try:
                self._fmcw.ram_control_config(enable=True, frequency_np=self._freqs)
                self._status(f"RAM enabled with {len(self._freqs)} values")
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(
                f"[dry-run] ram_control_config(enable=True, len={len(self._freqs)})"
            )

    def _on_disable(self):
        if self._fmcw:
            try:
                self._fmcw.ram_control_config(enable=False)
                self._status("RAM disabled")
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status("[dry-run] ram_control_config(enable=False)")

    def _status(self, msg):
        w = self.window()
        if isinstance(w, QMainWindow):
            w.statusBar().showMessage(msg, 5000)


# ---------------------------------------------------------------------------
# Register table widget (reused for DDS and PLL)
# ---------------------------------------------------------------------------


class RegisterAccess(QWidget):
    """Compact register read/write widget with a combobox selector."""

    def __init__(self, device_name, reg_enum):
        super().__init__()
        self._device_name = device_name
        self._regs = list(reg_enum)
        self._dev = None
        self._build_ui()
        self._connect_signals()

    def set_device(self, dev):
        self._dev = dev

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        reg_lbl = QLabel("Register")
        reg_lbl.setProperty("class", "caption")
        layout.addWidget(reg_lbl)
        self.reg_combo = QComboBox()
        for reg in self._regs:
            self.reg_combo.addItem(f"{reg.name}  (0x{reg.value:02X})")
        layout.addWidget(self.reg_combo)

        val_lbl = QLabel("Value (hex)")
        val_lbl.setProperty("class", "caption")
        layout.addWidget(val_lbl)
        self.val_edit = QLineEdit()
        self.val_edit.setPlaceholderText("0x00000000")
        layout.addWidget(self.val_edit)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.btn_read = QPushButton("Read")
        self.btn_read.setProperty("class", "secondary")
        self.btn_write = QPushButton("Write")
        self.btn_write.setProperty("class", "tertiary")
        btn_row.addWidget(self.btn_read)
        btn_row.addWidget(self.btn_write)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _connect_signals(self):
        self.btn_read.clicked.connect(self._on_read)
        self.btn_write.clicked.connect(self._on_write)

    def _selected_reg(self):
        return self._regs[self.reg_combo.currentIndex()]

    def _on_read(self):
        reg = self._selected_reg()
        if self._dev:
            try:
                val = self._dev.reg_read(reg)
                self.val_edit.setText(hex(val))
                self._status(f"{self._device_name}: {reg.name} = {hex(val)}")
            except Exception as ex:
                self._status(f"Error reading {reg.name}: {ex}")
        else:
            self._status(f"[dry-run] {self._device_name}.reg_read({reg.name})")

    def _on_write(self):
        reg = self._selected_reg()
        text = self.val_edit.text().strip()
        if not text:
            self._status("Enter a hex value first")
            return
        try:
            value = int(text, 0)
        except ValueError:
            self._status(f"Invalid hex value: {text}")
            return

        if self._dev:
            try:
                self._dev.reg_write(reg, value)
                self._status(f"{self._device_name}: wrote {hex(value)} to {reg.name}")
            except Exception as ex:
                self._status(f"Error writing {reg.name}: {ex}")
        else:
            self._status(
                f"[dry-run] {self._device_name}.reg_write({reg.name}, {hex(value)})"
            )

    def _status(self, msg):
        w = self.window()
        if isinstance(w, QMainWindow):
            w.statusBar().showMessage(msg, 5000)


# ---------------------------------------------------------------------------
# Debug tab
# ---------------------------------------------------------------------------


class DebugTab(QWidget):
    def __init__(self, theme: HmcTheme, fmcw=None):
        super().__init__()
        self._theme = theme
        self._fmcw = fmcw
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        from adi.ad9910 import ad9910
        from adi.adf4151x import adf41513

        # DDS card
        dds_card_layout = QVBoxLayout()
        dds_heading = QLabel("AD9910 (DDS)")
        dds_heading.setProperty("class", "heading")
        dds_card_layout.addWidget(dds_heading)
        self.dds_access = RegisterAccess("DDS", ad9910.reg)
        if self._fmcw:
            self.dds_access.set_device(self._fmcw.dds)
        dds_card_layout.addWidget(self.dds_access)
        dds_card = HmcCard(layout=dds_card_layout)
        layout.addWidget(dds_card)

        # PLL card
        pll_card_layout = QVBoxLayout()
        pll_heading = QLabel("ADF41513 (PLL)")
        pll_heading.setProperty("class", "heading")
        pll_card_layout.addWidget(pll_heading)
        self.pll_access = RegisterAccess("PLL", adf41513.reg)
        if self._fmcw:
            self.pll_access.set_device(self._fmcw.pll)
        pll_card_layout.addWidget(self.pll_access)
        pll_card = HmcCard(layout=pll_card_layout)
        layout.addWidget(pll_card)


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------


class ADMFM8000Dashboard(HmcMainWindow):
    def __init__(self, fmcw=None, uri=None, theme=None):
        super().__init__(theme=theme)
        self._fmcw = fmcw
        if fmcw is None and uri is not None:
            from adi.admfm8000 import admfm8000

            self._fmcw = admfm8000(uri=uri)

        self.setWindowTitle("ADMFM8000 Dashboard")
        self.resize(1280, 800)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Header ---
        self.header = QWidget()
        self.header.setProperty("class", "header")
        self.header.setFixedHeight(56)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title_icon = QLabel()
        title_icon.setPixmap(HmcLogoIcon(token=HmcTheme.Token.PRIMARY).pixmap(32, 32))
        header_layout.addWidget(title_icon)

        title = QLabel("ADMFM8000")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)

        header_layout.addSpacing(32)

        pll_lbl = QLabel("PLL N:")
        pll_lbl.setProperty("class", "caption")
        header_layout.addWidget(pll_lbl)
        self.pll_n_spin = QSpinBox()
        self.pll_n_spin.setRange(20, 100)
        self.pll_n_spin.setValue(20)
        self.pll_n_spin.setFixedWidth(80)
        header_layout.addWidget(self.pll_n_spin)

        header_layout.addSpacing(16)

        atten_lbl = QLabel("Attenuation:")
        atten_lbl.setProperty("class", "caption")
        header_layout.addWidget(atten_lbl)
        self.atten_spin = QDoubleSpinBox()
        self.atten_spin.setRange(0.0, 30.0)
        self.atten_spin.setDecimals(1)
        self.atten_spin.setSingleStep(2.0)
        self.atten_spin.setValue(0.0)
        self.atten_spin.setSuffix(" dB")
        self.atten_spin.setFixedWidth(100)
        header_layout.addWidget(self.atten_spin)

        header_layout.addStretch()

        conn_icon_name = "mdi6.lan-connect" if self._fmcw else "mdi6.lan-disconnect"
        conn_token = HmcTheme.Token.SUCCESS if self._fmcw else HmcTheme.Token.DANGER
        conn_label = QLabel()
        conn_label.setPixmap(HmcIcon(conn_icon_name, conn_token).pixmap(20, 20))
        header_layout.addWidget(conn_label)
        conn_text = QLabel("Connected" if self._fmcw else "No device")
        conn_text.setProperty("class", "caption")
        header_layout.addWidget(conn_text)

        main_layout.addWidget(self.header)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.single_tone_tab = SingleToneTab(self._theme, self._fmcw)
        self.parallel_port_tab = ParallelPortTab(self._theme, self._fmcw)
        self.drg_tab = DigitalRampTab(self._theme, self._fmcw)
        self.ram_tab = RAMTab(self._theme, self._fmcw)
        self.debug_tab = DebugTab(self._theme, self._fmcw)
        self.tabs.addTab(self.single_tone_tab, "Single Tone")
        self.tabs.addTab(self.parallel_port_tab, "Parallel Port")
        self.tabs.addTab(self.drg_tab, "Digital Ramp")
        self.tabs.addTab(self.ram_tab, "RAM Mode")
        self.tabs.addTab(self.debug_tab, "Debug")
        main_layout.addWidget(self.tabs)

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        if not self._fmcw:
            status_bar.showMessage("Running in dry-run mode — no hardware connected")

    def _connect_signals(self):
        self.pll_n_spin.valueChanged.connect(self._on_pll_n_changed)
        self.atten_spin.valueChanged.connect(self._on_atten_changed)

    def _on_pll_n_changed(self, value):
        if self._fmcw:
            try:
                self._fmcw.pll_N = value
                self.statusBar().showMessage(f"PLL N divider set to {value}", 3000)
            except Exception as ex:
                self.statusBar().showMessage(f"Error: {ex}", 5000)
        else:
            self.statusBar().showMessage(f"[dry-run] pll_N = {value}", 3000)

    def _on_atten_changed(self, value):
        if self._fmcw:
            try:
                self._fmcw.attenuation = value
                self.statusBar().showMessage(f"Attenuation set to {value} dB", 3000)
            except Exception as ex:
                self.statusBar().showMessage(f"Error: {ex}", 5000)
        else:
            self.statusBar().showMessage(f"[dry-run] attenuation = {value} dB", 3000)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ADMFM8000 Dashboard")
    parser.add_argument("--uri", type=str, default=None, help="IIO context URI")
    parser.add_argument(
        "--theme", choices=["light", "dark"], default="light", help="UI theme"
    )
    args = parser.parse_args()

    theme = HmcTheme.DARK if args.theme == "dark" else HmcTheme.LIGHT
    app = QApplication(sys.argv)

    window = ADMFM8000Dashboard(uri=args.uri, theme=theme)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
