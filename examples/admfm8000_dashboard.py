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
from PySide6.QtCore import QSize, Qt
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
DAC_FULL_SCALE_MA = 20.5


def _set_value(widget, value):
    """Set a widget value without emitting valueChanged/currentIndexChanged."""
    widget.blockSignals(True)
    if isinstance(widget, QComboBox):
        widget.setCurrentIndex(value)
    else:
        widget.setValue(value)
    widget.blockSignals(False)


def _mode_index(modes, key):
    """Index of the (display, key) entry matching key, -1 if not listed."""
    for idx, (_, mode_key) in enumerate(modes):
        if mode_key == key:
            return idx
    return -1


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

            amp_lbl = QLabel("Amplitude (mA)")
            amp_lbl.setProperty("class", "caption")
            card_layout.addWidget(amp_lbl)
            amp_spin = QDoubleSpinBox()
            amp_spin.setRange(0.0, DAC_FULL_SCALE_MA)
            amp_spin.setDecimals(3)
            amp_spin.setSingleStep(0.1)
            amp_spin.setValue(DAC_FULL_SCALE_MA)
            amp_spin.setSuffix(" mA")
            card_layout.addWidget(amp_spin)

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
                    "amplitude": amp_spin,
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
        amplitude = c["amplitude"].value()
        phase = c["phase"].value()
        if self._fmcw:
            try:
                self._fmcw.single_tone_config(
                    profile=profile,
                    frequency=freq,
                    amplitude=amplitude,
                    phase=phase,
                )
                self.refresh(profile)
                freq = c["freq"].value() * 1e9
                amplitude = c["amplitude"].value()
                phase = c["phase"].value()
                self._status(
                    f"Profile {profile}: {freq/1e9:.4f} GHz, {amplitude:.3f} mA, "
                    f"phase={phase:.3f} rad"
                )
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(
                f"[dry-run] single_tone_config(profile={profile}, "
                f"frequency={freq:.0f}, amplitude={amplitude:.3f}, phase={phase:.3f})"
            )

    def _on_select(self, profile):
        if self._fmcw:
            try:
                self._fmcw.profile = profile
                self.refresh()
                self._status(f"Active profile set to {profile}")
            except Exception as ex:
                self._status(f"Error: {ex}")
        else:
            self._status(f"[dry-run] profile = {profile}")

    def refresh(self, profile=None):
        """Read the device back and populate the controls with the readback

        :param profile: single profile to refresh, or None for all of them
        """
        if not self._fmcw:
            return

        profiles = range(NUM_PROFILES) if profile is None else [profile]
        for i in profiles:
            c = self._cards[i]
            st = self._fmcw.st.profiles[i]
            full_scale = st.scale * self._fmcw.ASF_MAX
            c["amplitude"].setRange(0.0, full_scale)
            _set_value(c["freq"], st.frequency / 1e9)
            _set_value(c["amplitude"], st.amplitude)
            _set_value(c["phase"], st.phase)

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
        self._readback = None
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
            self._readback = None
            self._update_preview()
            self._status(f"Loaded {len(self._freqs)} frequency values")
        except Exception as ex:
            self._status(f"Error loading CSV: {ex}")
            self._freqs = None
            self._readback = None

    def _update_preview(self):
        self.plot.clear()
        if self._freqs is not None and len(self._freqs) > 0:
            self.plot.plot(
                np.arange(len(self._freqs)),
                self._freqs,
                pen=pg.mkPen(self._theme.categorical[0], width=2),
            )
        if self._readback is not None and len(self._readback) > 0:
            self.plot.plot(
                np.arange(len(self._readback)),
                self._readback,
                pen=pg.mkPen(self._theme.categorical[1], width=1, style=Qt.DashLine),
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
                rate = self.refresh()
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

    def refresh(self):
        """Read the device back, populate the controls and the preview

        The parallel port resolves the requested rate to a divider of the
        sysclk and the frequencies to a 16-bit word plus a power of two gain,
        so the readback shows what the hardware actually plays. Returns the
        effective rate in samples/second.
        """
        if not self._fmcw:
            return 0.0

        pp = self._fmcw.parallel_port
        rate = pp.rate
        _set_value(self.sweep_spin, len(self._freqs) / rate * 1e6)

        scale = pp.frequency_scale
        offset = pp.frequency_offset
        words = np.clip(np.round(self._freqs / scale) - offset, 0, 0xFFFF)
        self._readback = (words + offset) * scale
        self._update_preview()

        return rate

    def _status(self, msg):
        w = self.window()
        if isinstance(w, QMainWindow):
            w.statusBar().showMessage(msg, 5000)


# ---------------------------------------------------------------------------
# Digital Ramp Generator tab
# ---------------------------------------------------------------------------


class RateSpinBox(QDoubleSpinBox):
    """Spin whose value is always (base/div)/1e6 MSPS for div ∈ [1, 65535].

    Stepping moves through consecutive legal divisors, so the visible MSPS
    jumps in the non-linear increments required by the hardware, rather than
    QDoubleSpinBox's default fixed singleStep.
    """

    def __init__(self, base_getter):
        super().__init__()
        self._base = base_getter
        self.setDecimals(3)
        self.setSuffix(" MSPS")
        self.refresh_range()
        self.setValue(self._msps_for_div(1))

    def refresh_range(self):
        base = self._base()
        self.setRange(base / 65535 / 1e6, base / 1e6)

    def _msps_for_div(self, div):
        return (self._base() / max(1, min(65535, int(div)))) / 1e6

    def _current_div(self):
        base = self._base()
        msps = self.value()
        if msps <= 0:
            return 65535
        return max(1, min(65535, round(base / (msps * 1e6))))

    def stepBy(self, steps):
        # Higher div → lower rate. Up-arrow (steps>0) should raise the rate,
        # so it decreases the divisor.
        new_div = max(1, min(65535, self._current_div() - steps))
        self.refresh_range()
        self.setValue(self._msps_for_div(new_div))


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

    def _sysclk(self) -> float:
        """Live sysclk (Hz); may change at runtime. Falls back to 1 GHz."""
        if self._fmcw:
            return float(self._fmcw.sysclk_frequency)
        return 1e9

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

        def _dspin(rng, decimals, step, value, suffix):
            s = QDoubleSpinBox()
            s.setRange(*rng)
            s.setDecimals(decimals)
            s.setSingleStep(step)
            s.setValue(value)
            s.setSuffix(suffix)
            return s

        self.freq_min_spin = _dspin(
            (FREQ_MIN_GHZ, FREQ_MAX_GHZ), 4, 0.1, FREQ_MIN_GHZ, " GHz"
        )
        self.freq_max_spin = _dspin(
            (FREQ_MIN_GHZ, FREQ_MAX_GHZ), 4, 0.1, FREQ_MAX_GHZ, " GHz"
        )
        self.inc_time_spin = _dspin((0.1, 10000.0), 1, 10.0, 50.0, " us")
        self.dec_time_spin = _dspin((0.1, 10000.0), 1, 10.0, 50.0, " us")
        # DRG rate = (sysclk / 4) / div  where div is a non-zero uint16.
        # Custom RateSpinBox steps through consecutive legal divisors so the
        # displayed MSPS jumps in the non-linear increments required by HW.
        self.inc_rate_spin = RateSpinBox(lambda: self._sysclk() / 4.0)
        self.dec_rate_spin = RateSpinBox(lambda: self._sysclk() / 4.0)
        self.inc_int_spin = _dspin((0.0, 100000.0), 2, 10.0, 100.0, " us")
        self.dec_int_spin = _dspin((0.0, 100000.0), 2, 10.0, 100.0, " us")
        self.burst_count_spin = QSpinBox()
        self.burst_count_spin.setRange(0, 100)
        self.burst_count_spin.setValue(0)
        self.burst_delay_spin = _dspin((0.0, 100000.0), 1, 10.0, 100.0, " us")

        # Two-column paired grid: (left label + spin, right label + spin)
        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)
        pairs = [
            (
                "Freq Min (GHz)",
                self.freq_min_spin,
                "Freq Max (GHz)",
                self.freq_max_spin,
            ),
            ("Ramp-up Rate", self.inc_rate_spin, "Ramp-down Rate", self.dec_rate_spin),
            (
                "Ramp-up Slope Time",
                self.inc_time_spin,
                "Ramp-down Slope Time",
                self.dec_time_spin,
            ),
            (
                "Ramp-up Control Time",
                self.inc_int_spin,
                "Ramp-down Control Time",
                self.dec_int_spin,
            ),
            (
                "Burst Count",
                self.burst_count_spin,
                "Burst Delay",
                self.burst_delay_spin,
            ),
        ]
        self._drctl_widgets = []
        # up_side / down_side: per-direction widgets that can be toggled
        # off entirely in one-shot ramp modes.
        self._up_side = []
        self._down_side = []
        for row, (l1, w1, l2, w2) in enumerate(pairs):
            r = row * 2
            lbl1 = QLabel(l1)
            lbl1.setProperty("class", "caption")
            lbl2 = QLabel(l2)
            lbl2.setProperty("class", "caption")
            grid.addWidget(lbl1, r, 0)
            grid.addWidget(lbl2, r, 1)
            grid.addWidget(w1, r + 1, 0)
            grid.addWidget(w2, r + 1, 1)
            if row >= 3:  # integration-time and burst rows are DRCTL-only
                self._drctl_widgets.extend([lbl1, w1, lbl2, w2])
            if row in (1, 2):  # ramp-time and rate rows have up/down sides
                self._up_side.extend([lbl1, w1])
                self._down_side.extend([lbl2, w2])
            elif row == 3:  # integration-time row also has up/down sides
                self._up_side.extend([lbl1, w1])
                self._down_side.extend([lbl2, w2])
        ctrl_layout.addLayout(grid)

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
        header_row = QHBoxLayout()
        plot_heading = QLabel("Ramp Preview")
        plot_heading.setProperty("class", "heading")
        header_row.addWidget(plot_heading)
        header_row.addStretch()
        preview_lbl = QLabel("Preview Time")
        preview_lbl.setProperty("class", "caption")
        header_row.addWidget(preview_lbl)
        self.preview_time_spin = QDoubleSpinBox()
        self.preview_time_spin.setRange(1.0, 100000.0)
        self.preview_time_spin.setDecimals(1)
        self.preview_time_spin.setSingleStep(50.0)
        self.preview_time_spin.setValue(400.0)
        self.preview_time_spin.setSuffix(" us")
        header_row.addWidget(self.preview_time_spin)
        plot_outer.addLayout(header_row)

        plot_layout = QVBoxLayout()
        self.plot = HmcPlot(theme=self._theme, title="DRG frequency ramp")
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", "Frequency", units="Hz")

        # Twin right axis for DRCTL (digital 0/1 line)
        self.plot.showAxis("right")
        self.plot.setLabel("right", "DRCTL")
        self._drctl_vb = pg.ViewBox()
        self.plot.scene().addItem(self._drctl_vb)
        self.plot.getAxis("right").linkToView(self._drctl_vb)
        self._drctl_vb.setXLink(self.plot.getViewBox())
        self._drctl_vb.setYRange(0.0, 1.0, padding=0)
        self._drctl_vb.setLimits(yMin=0.0, yMax=1.0)
        self.plot.getViewBox().sigResized.connect(
            lambda: self._drctl_vb.setGeometry(
                self.plot.getViewBox().sceneBoundingRect()
            )
        )
        self._drctl_curve = pg.PlotCurveItem(
            pen=pg.mkPen(self._theme.categorical[1], width=2),
            stepMode="right",
        )
        self._drctl_vb.addItem(self._drctl_curve)

        plot_layout.addWidget(self.plot)
        plot_card = HmcCard(layout=plot_layout)
        plot_outer.addWidget(plot_card)

        layout.addLayout(plot_outer, 2)

    def _connect_signals(self):
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        for spin in (
            self.freq_min_spin,
            self.freq_max_spin,
            self.inc_time_spin,
            self.dec_time_spin,
            self.inc_rate_spin,
            self.dec_rate_spin,
            self.inc_int_spin,
            self.dec_int_spin,
            self.burst_count_spin,
            self.burst_delay_spin,
            self.preview_time_spin,
        ):
            spin.valueChanged.connect(lambda _=None: self._update_preview())
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_disable.clicked.connect(self._on_disable)
        self.inc_rate_spin.editingFinished.connect(
            lambda: self._snap_rate(self.inc_rate_spin)
        )
        self.dec_rate_spin.editingFinished.connect(
            lambda: self._snap_rate(self.dec_rate_spin)
        )

    def _snap_rate(self, spin: QDoubleSpinBox):
        """Snap MSPS value to nearest legal (sysclk/4)/div, div ∈ [1, 65535]."""
        base = self._sysclk() / 4.0
        # Refresh the spin's allowed range in case sysclk changed.
        spin.setRange(base / 65535 / 1e6, base / 1e6)
        msps = spin.value()
        if msps <= 0:
            return
        div = max(1, min(65535, round(base / (msps * 1e6))))
        snapped = (base / div) / 1e6
        if abs(snapped - msps) > 1e-9:
            spin.blockSignals(True)
            spin.setValue(snapped)
            spin.blockSignals(False)
            self._update_preview()

    def _on_mode_changed(self):
        _, mode_key = DRG_MODES[self.mode_combo.currentIndex()]
        drctl_active = mode_key != "BIDIRECTIONAL_CONTINUOUS"
        up_active = mode_key != "RAMP_DOWN"
        down_active = mode_key != "RAMP_UP"
        drctl_ids = {id(w) for w in self._drctl_widgets}
        for w in self._up_side:
            w.setEnabled(up_active and (id(w) not in drctl_ids or drctl_active))
        for w in self._down_side:
            w.setEnabled(down_active and (id(w) not in drctl_ids or drctl_active))
        side_ids = {id(w) for w in self._up_side} | {id(w) for w in self._down_side}
        for w in self._drctl_widgets:
            if id(w) not in side_ids:
                w.setEnabled(drctl_active)
        self._update_preview()

    def _append(self, t_segs, f_segs, t_start, t_end, f_start, f_end, preview_end):
        """Append a linear segment, clipped to preview_end. Returns (t_end_clipped, f_end_clipped, done)."""
        if t_start >= preview_end:
            return t_start, f_start, True
        n = 50
        if t_end > preview_end:
            frac = (
                (preview_end - t_start) / (t_end - t_start) if t_end > t_start else 0.0
            )
            f_clip = f_start + (f_end - f_start) * frac
            t_segs.append(np.linspace(t_start, preview_end, n))
            f_segs.append(np.linspace(f_start, f_clip, n))
            return preview_end, f_clip, True
        t_segs.append(np.linspace(t_start, t_end, n))
        f_segs.append(np.linspace(f_start, f_end, n))
        return t_end, f_end, False

    def _build_drctl(
        self, mode_key, inc_int, dec_int, burst_count, burst_delay, preview_end
    ):
        """Build DRCTL step trace (times, levels) or (None, None) if N/A."""
        if mode_key == "BIDIRECTIONAL_CONTINUOUS":
            return None, None

        if mode_key == "RAMP_UP":
            period = inc_int
            half = period / 2.0
            pulse_shape = [(half, 1), (half, 0)]
            idle_level = 0
        elif mode_key == "RAMP_DOWN":
            period = dec_int
            half = period / 2.0
            pulse_shape = [(half, 0), (half, 1)]
            idle_level = 1
        else:  # BIDIRECTIONAL
            period = inc_int + dec_int
            pulse_shape = [(inc_int, 1), (dec_int, 0)]
            idle_level = 0

        if period <= 0:
            return None, None

        times = [0.0]
        levels = []
        t = 0.0
        pulse_idx = 0
        done = False
        while not done:
            for dur, lvl in pulse_shape:
                levels.append(lvl)
                t = min(t + dur, preview_end)
                times.append(t)
                if t >= preview_end:
                    done = True
                    break
            if done:
                break
            pulse_idx += 1
            if burst_count > 0 and pulse_idx >= burst_count:
                if burst_delay > 0:
                    levels.append(idle_level)
                    t = min(t + burst_delay, preview_end)
                    times.append(t)
                    if t >= preview_end:
                        done = True
                    pulse_idx = 0
                else:
                    levels.append(idle_level)
                    times.append(preview_end)
                    done = True
        return np.array(times), np.array(levels)

    def _update_preview(self):
        self.plot.clear()
        self._drctl_curve.setData(x=[], y=[])
        f_min = self.freq_min_spin.value() * 1e9
        f_max = self.freq_max_spin.value() * 1e9
        if f_min >= f_max:
            return

        inc_time = self.inc_time_spin.value() * 1e-6
        dec_time = self.dec_time_spin.value() * 1e-6
        inc_int = self.inc_int_spin.value() * 1e-6
        dec_int = self.dec_int_spin.value() * 1e-6
        preview_end = self.preview_time_spin.value() * 1e-6
        burst_count = self.burst_count_spin.value()
        burst_delay = self.burst_delay_spin.value() * 1e-6

        _, mode_key = DRG_MODES[self.mode_combo.currentIndex()]

        t_segs = []
        f_segs = []
        t_off = 0.0
        done = False
        pulse_idx = 0  # counts completed PWM periods within the current burst

        if mode_key == "BIDIRECTIONAL_CONTINUOUS":
            # Continuous up/down; integration times ignored.
            direction_up = True
            while not done:
                if direction_up:
                    t_off, _, done = self._append(
                        t_segs,
                        f_segs,
                        t_off,
                        t_off + inc_time,
                        f_min,
                        f_max,
                        preview_end,
                    )
                else:
                    t_off, _, done = self._append(
                        t_segs,
                        f_segs,
                        t_off,
                        t_off + dec_time,
                        f_max,
                        f_min,
                        preview_end,
                    )
                direction_up = not direction_up

        elif mode_key == "RAMP_UP":
            # No-dwell high: DRCTL rising edge triggers a full ramp up over
            # inc_time. Edges arriving while ramping are ignored; freq then
            # snaps to f_min and holds until the next unmissed rising edge.
            period = inc_int
            if period <= 0 or inc_time <= 0:
                return
            # Next edge strictly AFTER ramp completes. If ramp ends exactly on
            # an edge, that edge is missed too — hence floor()+1, not ceil().
            n_periods_per_cycle = math.floor(inc_time / period) + 1
            cycle_time = n_periods_per_cycle * period
            while not done:
                cycle_start = t_off
                t_ramp_end = cycle_start + inc_time
                t_off, _, done = self._append(
                    t_segs,
                    f_segs,
                    cycle_start,
                    t_ramp_end,
                    f_min,
                    f_max,
                    preview_end,
                )
                if done:
                    break
                cycle_end = cycle_start + cycle_time
                t_off, _, done = self._append(
                    t_segs,
                    f_segs,
                    t_off,
                    cycle_end,
                    f_min,
                    f_min,
                    preview_end,
                )
                if done:
                    break
                pulse_idx += 1
                if burst_count > 0 and pulse_idx >= burst_count:
                    if burst_delay > 0:
                        t_off, _, done = self._append(
                            t_segs,
                            f_segs,
                            t_off,
                            t_off + burst_delay,
                            f_min,
                            f_min,
                            preview_end,
                        )
                        pulse_idx = 0
                    else:
                        # n-shot: burst_count periods then stop, hold at idle
                        self._append(
                            t_segs,
                            f_segs,
                            t_off,
                            preview_end,
                            f_min,
                            f_min,
                            preview_end,
                        )
                        done = True

        elif mode_key == "RAMP_DOWN":
            # No-dwell low: DRCTL falling edge triggers a full ramp down over
            # dec_time. Edges arriving while ramping are ignored; freq then
            # snaps to f_max and holds until the next unmissed falling edge.
            period = dec_int
            if period <= 0 or dec_time <= 0:
                return
            n_periods_per_cycle = math.floor(dec_time / period) + 1
            cycle_time = n_periods_per_cycle * period
            while not done:
                cycle_start = t_off
                t_ramp_end = cycle_start + dec_time
                t_off, _, done = self._append(
                    t_segs,
                    f_segs,
                    cycle_start,
                    t_ramp_end,
                    f_max,
                    f_min,
                    preview_end,
                )
                if done:
                    break
                cycle_end = cycle_start + cycle_time
                t_off, _, done = self._append(
                    t_segs,
                    f_segs,
                    t_off,
                    cycle_end,
                    f_max,
                    f_max,
                    preview_end,
                )
                if done:
                    break
                pulse_idx += 1
                if burst_count > 0 and pulse_idx >= burst_count:
                    if burst_delay > 0:
                        t_off, _, done = self._append(
                            t_segs,
                            f_segs,
                            t_off,
                            t_off + burst_delay,
                            f_max,
                            f_max,
                            preview_end,
                        )
                        pulse_idx = 0
                    else:
                        self._append(
                            t_segs,
                            f_segs,
                            t_off,
                            preview_end,
                            f_max,
                            f_max,
                            preview_end,
                        )
                        done = True

        else:  # BIDIRECTIONAL
            # High phase (inc_int): ramp toward f_max at inc slope; dwell if reached.
            # Low  phase (dec_int): ramp toward f_min at dec slope; dwell if reached.
            # If DRCTL toggles before a limit is reached, the reverse ramp starts
            # from the current freq, not from the (unreached) limit.
            inc_slope = (f_max - f_min) / inc_time if inc_time > 0 else float("inf")
            dec_slope = (f_max - f_min) / dec_time if dec_time > 0 else float("inf")
            f_current = f_min
            while not done:
                # High phase
                time_to_max = (f_max - f_current) / inc_slope if inc_slope > 0 else 0.0
                t_ramp_end = t_off + min(time_to_max, inc_int)
                f_at_end = f_current + inc_slope * (t_ramp_end - t_off)
                t_off, f_current, done = self._append(
                    t_segs,
                    f_segs,
                    t_off,
                    t_ramp_end,
                    f_current,
                    f_at_end,
                    preview_end,
                )
                if done:
                    break
                high_end = t_off + max(0.0, inc_int - time_to_max)
                if high_end > t_off:
                    t_off, f_current, done = self._append(
                        t_segs,
                        f_segs,
                        t_off,
                        high_end,
                        f_current,
                        f_current,
                        preview_end,
                    )
                    if done:
                        break
                # Low phase
                time_to_min = (f_current - f_min) / dec_slope if dec_slope > 0 else 0.0
                t_ramp_end = t_off + min(time_to_min, dec_int)
                f_at_end = f_current - dec_slope * (t_ramp_end - t_off)
                t_off, f_current, done = self._append(
                    t_segs,
                    f_segs,
                    t_off,
                    t_ramp_end,
                    f_current,
                    f_at_end,
                    preview_end,
                )
                if done:
                    break
                low_end = t_off + max(0.0, dec_int - time_to_min)
                if low_end > t_off:
                    t_off, f_current, done = self._append(
                        t_segs,
                        f_segs,
                        t_off,
                        low_end,
                        f_current,
                        f_current,
                        preview_end,
                    )
                    if done:
                        break
                pulse_idx += 1
                if burst_count > 0 and pulse_idx >= burst_count:
                    if burst_delay > 0:
                        t_off, f_current, done = self._append(
                            t_segs,
                            f_segs,
                            t_off,
                            t_off + burst_delay,
                            f_current,
                            f_current,
                            preview_end,
                        )
                        pulse_idx = 0
                    else:
                        self._append(
                            t_segs,
                            f_segs,
                            t_off,
                            preview_end,
                            f_current,
                            f_current,
                            preview_end,
                        )
                        done = True

        if t_segs:
            t_all = np.concatenate(t_segs)
            f_all = np.concatenate(f_segs)
            self.plot.plot(
                t_all, f_all, pen=pg.mkPen(self._theme.categorical[0], width=2)
            )

        drctl_t, drctl_l = self._build_drctl(
            mode_key,
            inc_int,
            dec_int,
            burst_count,
            burst_delay,
            preview_end,
        )
        if drctl_t is not None and len(drctl_l) > 0:
            # stepMode="right" requires len(x) == len(y). times has one extra
            # trailing boundary — repeat the last level to match.
            drctl_l = np.append(drctl_l, drctl_l[-1])
            self._drctl_curve.setData(x=drctl_t, y=drctl_l)
        self._drctl_vb.setGeometry(self.plot.getViewBox().sceneBoundingRect())

    def _on_apply(self):
        _, mode_key = DRG_MODES[self.mode_combo.currentIndex()]
        f_min = self.freq_min_spin.value() * 1e9
        f_max = self.freq_max_spin.value() * 1e9
        inc_time = self.inc_time_spin.value() * 1e-6
        dec_time = self.dec_time_spin.value() * 1e-6
        inc_rate = self.inc_rate_spin.value() * 1e6
        dec_rate = self.dec_rate_spin.value() * 1e6
        inc_int = self.inc_int_spin.value() * 1e-6
        dec_int = self.dec_int_spin.value() * 1e-6

        kwargs = {"inc_rate": inc_rate, "dec_rate": dec_rate}
        if mode_key != "BIDIRECTIONAL_CONTINUOUS":
            kwargs["inc_time"] = inc_int
            kwargs["dec_time"] = dec_int
            kwargs["burst_count"] = self.burst_count_spin.value()
            kwargs["burst_delay"] = self.burst_delay_spin.value() * 1e-6

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
                self.refresh()
                f_min = self.freq_min_spin.value() * 1e9
                f_max = self.freq_max_spin.value() * 1e9
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

    def refresh(self):
        """Read the DRG back and populate the controls with the readback

        The device resolves the ramp limits to 32-bit codes, the slopes to a
        code per update and the rates to a divider of the sysclk, so the
        readback differs from what was requested. The burst settings are write
        only in this dashboard and are left untouched.
        """
        if not self._fmcw:
            return

        ramp = self._fmcw.drg.frequency
        mode_idx = _mode_index(DRG_MODES, ramp.operating_mode.name)
        if mode_idx >= 0:
            _set_value(self.mode_combo, mode_idx)

        _set_value(self.freq_min_spin, ramp.min / 1e9)
        _set_value(self.freq_max_spin, ramp.max / 1e9)

        for spin, rate in (
            (self.inc_rate_spin, ramp.positive_slope_rate),
            (self.dec_rate_spin, ramp.negative_slope_rate),
        ):
            spin.refresh_range()
            _set_value(spin, rate / 1e6)

        _set_value(self.inc_time_spin, ramp.positive_slope_time * 1e6)
        _set_value(self.dec_time_spin, ramp.negative_slope_time * 1e6)
        _set_value(self.inc_int_spin, ramp.positive_ctl_time * 1e6)
        _set_value(self.dec_int_spin, ramp.negative_ctl_time * 1e6)

        self._on_mode_changed()

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

    def __init__(self, profile: int, sysclk_getter=None):
        super().__init__()
        self._profile = profile
        self._sysclk_getter = sysclk_getter or (lambda: 1e9)
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

        rate_lbl = QLabel("Rate")
        rate_lbl.setProperty("class", "caption")
        layout.addWidget(rate_lbl)
        self.rate_spin = RateSpinBox(lambda: self._sysclk_getter() / 4.0)
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

        sysclk_getter = (
            (lambda: float(self._fmcw.sysclk_frequency))
            if self._fmcw
            else (lambda: 1e9)
        )
        for i in range(NUM_PROFILES):
            pw = RAMProfileWidget(i, sysclk_getter=sysclk_getter)
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
                self.refresh(profile)
                addr_range = pw.addr_range
                rate = pw.rate_hz
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

    def refresh(self, profile=None):
        """Populate the profile controls with the staged RAM profile settings

        RAM profiles only reach the device as part of the RAM firmware image,
        so this reads back the staged settings, where the rate has already been
        resolved to a divider of the sysclk.

        :param profile: single profile to refresh, or None for all of them
        """
        if not self._fmcw:
            return

        profiles = range(NUM_PROFILES) if profile is None else [profile]
        for i in profiles:
            pw = self._profiles[i]
            ram = self._fmcw.ram.profiles[i]
            mode_idx = _mode_index(RAM_MODES, ram.operating_mode.name)
            if mode_idx >= 0:
                _set_value(pw.mode_combo, mode_idx)
            addr_start, addr_end = ram.address_range
            _set_value(pw.addr_start_spin, addr_start)
            _set_value(pw.addr_end_spin, addr_end)
            pw.rate_spin.refresh_range()
            _set_value(pw.rate_spin, ram.rate / 1e6)

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
            self.dds_access.set_device(self._fmcw)
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
        title_icon.setPixmap(
            HmcLogoIcon(token=HmcTheme.Token.PRIMARY, theme=self._theme).pixmap(32, 32)
        )
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
