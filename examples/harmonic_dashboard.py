# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic Design System — PySide6 + pyqtgraph dashboard example.

Supports light/dark mode toggle via the moon/sun icon in the header.
"""

import sys
from datetime import datetime

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QEvent, QSize, Qt, QTimer
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from harmonic.checkbox import HmcCheckbox
from harmonic.container import HmcCard, HmcMainWindow
from harmonic.graph import HmcPlot
from harmonic.icons import HmcIcon, HmcLogoIcon
from harmonic.radio import HmcRadio
from harmonic.theme import HmcTheme
from harmonic.toggle import HmcToggleSwitch

# ---------------------------------------------------------------------------
# pyqtgraph defaults
# ---------------------------------------------------------------------------
pg.setConfigOptions(antialias=True, background=None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# KPI Card widget
# ---------------------------------------------------------------------------

class KPICard(QFrame):
    def __init__(self, title: str, value: str, badge_text: str, badge_id: str):
        super().__init__()
        self.setProperty("class", "card")
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(20, 16, 20, 16)

        lbl_title = QLabel(title)
        lbl_title.setProperty("class", "subheading")

        lbl_value = QLabel(value)
        lbl_value.setProperty("class", "kpi-value")

        badge = QLabel(badge_text)
        badge.setObjectName(badge_id)
        badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_value)
        layout.addWidget(badge)


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------

class Sidebar(QFrame):
    def __init__(self, theme: HmcTheme):
        super().__init__()
        self._theme = theme
        self.setFixedWidth(60)
        self.setProperty("class", "sidebar")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(0)

        icons = [
            ("mdi6.view-dashboard", "Dashboard"),
            ("mdi6.chart-line", "Charts"),
            ("mdi6.cog", "Settings"),
        ]

        self.buttons: list[QPushButton] = []
        for icon_name, tooltip in icons:
            btn = QPushButton()
            btn.setProperty("class", "nav")
            btn.setIcon(HmcIcon(icon_name, HmcTheme.Token.CONTENT_MEDIUM, parent=btn))
            btn.setIconSize(QSize(32, 32))
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.setFixedSize(40, 40)
            btn.clicked.connect(lambda checked, b=btn: self._on_click(b))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)
            self.buttons.append(btn)

        layout.addStretch()
        self.buttons[0].setChecked(True)

    def _on_click(self, clicked_btn: QPushButton):
        for btn in self.buttons:
            btn.setChecked(btn is clicked_btn)


# ---------------------------------------------------------------------------
# Overview tab
# ---------------------------------------------------------------------------

class OverviewTab(QWidget):
    def __init__(self, theme: HmcTheme):
        super().__init__()
        self._theme = theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- KPI row ---
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        kpi_row.addWidget(KPICard("Sampling Rate", "1.024 MS/s", "Active", "badge-success"))
        kpi_row.addWidget(KPICard("Signal-to-Noise", "72.4 dB", "+3.1 dB", "badge-info"))
        kpi_row.addWidget(KPICard("Error Rate", "0.03%", "Low", "badge-warning"))
        layout.addLayout(kpi_row)

        # --- Time-series plot ---
        self.ts_plot = HmcPlot(theme=theme, title="Multi-channel signal capture")
        self.ts_legend = self.ts_plot.addLegend(offset=(10, 10))

        t = np.linspace(0, 2 * np.pi, 500)
        self._ts_data = [
            ("Channel A", t, np.sin(t * 3) + np.random.normal(0, 0.05, len(t))),
            ("Channel B", t, 0.7 * np.sin(t * 5 + 1) + np.random.normal(0, 0.05, len(t))),
            ("Channel C", t, 0.5 * np.cos(t * 2 + 0.5) + np.random.normal(0, 0.05, len(t))),
        ]
        for i, (name, x, y) in enumerate(self._ts_data):
            self.ts_plot.plot(x, y, pen=pg.mkPen(theme.categorical[i], width=2), name=name)
        self.ts_plot.setLabel("bottom", "Time", units="s")
        self.ts_plot.setLabel("left", "Amplitude", units="V")

        ts_card_layout = QVBoxLayout()
        ts_card = HmcCard(layout=ts_card_layout)
        ts_card_layout.addWidget(self.ts_plot)
        layout.addWidget(ts_card)

        # --- Scatter plot ---
        self.scatter_plot = HmcPlot(theme=theme, title="Frequency vs. amplitude distribution")
        self._scatter_data = []
        for i in range(4):
            x = np.random.normal(10 * (i + 1), 3, 80)
            y = np.random.normal(0.5 * (i + 1), 0.3, 80)
            self._scatter_data.append((x, y))
            scatter = pg.ScatterPlotItem(
                x, y,
                pen=pg.mkPen(theme.categorical[i], width=1),
                brush=pg.mkBrush(theme.categorical[i] + "99"),
                size=8,
                name=f"Band {i + 1}",
            )
            self.scatter_plot.addItem(scatter)
        self.scatter_plot.setLabel("bottom", "Frequency", units="Hz")
        self.scatter_plot.setLabel("left", "Amplitude", units="V")
        self.scatter_legend = self.scatter_plot.addLegend(offset=(10, 10))

        scatter_card_layout = QVBoxLayout()
        scatter_card = HmcCard(layout=scatter_card_layout)
        scatter_card_layout.addWidget(self.scatter_plot)
        layout.addWidget(scatter_card)


# ---------------------------------------------------------------------------
# Analysis tab
# ---------------------------------------------------------------------------

class AnalysisTab(QWidget):
    def __init__(self, theme: HmcTheme):
        super().__init__()
        self._theme = theme
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # --- Controls row ---
        controls = QHBoxLayout()
        controls.setSpacing(12)

        lbl = QLabel("Dataset:")
        lbl.setProperty("class", "subheading")
        controls.addWidget(lbl)

        self.combo = QComboBox()
        self.combo.addItems(["Power spectrum", "Harmonic distortion", "Noise floor"])
        self.combo.setMinimumWidth(200)
        self.combo.currentIndexChanged.connect(self._refresh_data)
        controls.addWidget(self.combo)

        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setProperty("class", "secondary")
        self.btn_refresh.setIcon(HmcIcon("mdi6.refresh", HmcTheme.Token.PRIMARY, parent=self.btn_refresh))
        self.btn_refresh.clicked.connect(self._refresh_data)
        controls.addWidget(self.btn_refresh)

        self.btn_download = QPushButton("Export")
        self.btn_download.setProperty("class", "tertiary")
        self.btn_download.setIcon(HmcIcon("mdi6.download", HmcTheme.Token.CONTENT_DEFAULT, parent=self.btn_download))
        controls.addWidget(self.btn_download)

        controls.addStretch()
        layout.addLayout(controls)

        # --- Bar chart ---
        self.bar_plot = HmcPlot(theme=theme, title="Spectral analysis")
        self.bar_plot.setLabel("bottom", "Frequency bin")
        self.bar_plot.setLabel("left", "Magnitude", units="dB")
        bar_card_layout = QVBoxLayout()
        bar_card = HmcCard(layout=bar_card_layout)
        bar_card_layout.addWidget(self.bar_plot)
        layout.addWidget(bar_card)

        # --- Line detail plot ---
        self.detail_plot = HmcPlot(theme=theme, title="Time-domain detail")
        self.detail_plot.setLabel("bottom", "Sample")
        self.detail_plot.setLabel("left", "Value")
        detail_card_layout = QVBoxLayout()
        detail_card = HmcCard(layout=detail_card_layout)
        detail_card_layout.addWidget(self.detail_plot)
        layout.addWidget(detail_card)

        self._refresh_data()

    def _refresh_data(self):
        theme = self._theme
        self.bar_plot.clear()
        self.detail_plot.clear()
        idx = self.combo.currentIndex()

        np.random.seed(idx + int(datetime.now().timestamp()) % 1000)
        n_bins = 32
        x = np.arange(n_bins)

        for series_i in range(3):
            heights = np.random.exponential(5, n_bins) * (series_i + 1) * 0.6
            bar = pg.BarGraphItem(
                x=x + series_i * 0.25 - 0.25,
                height=heights,
                width=0.22,
                brush=pg.mkBrush(theme.categorical[series_i] + "CC"),
                pen=pg.mkPen(theme.categorical[series_i], width=1),
            )
            self.bar_plot.addItem(bar)

        samples = np.arange(200)
        for series_i in range(2):
            freq = 0.05 * (idx + 1) * (series_i + 1)
            signal = np.sin(2 * np.pi * freq * samples) * (1 + 0.3 * series_i)
            signal += np.random.normal(0, 0.1, len(samples))
            self.detail_plot.plot(
                samples, signal,
                pen=pg.mkPen(theme.categorical[series_i + 3], width=2),
            )


# ---------------------------------------------------------------------------
# Components showcase tab
# ---------------------------------------------------------------------------

class ComponentsTab(QWidget):
    def __init__(self, theme: HmcTheme):
        super().__init__()
        self._theme = theme

        scroll_content = QVBoxLayout(self)
        scroll_content.setContentsMargins(24, 24, 24, 24)
        scroll_content.setSpacing(16)

        heading = QLabel("Component showcase")
        heading.setProperty("class", "heading")
        scroll_content.addWidget(heading)

        # --- Row 1: Selection controls --------------------------------
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        # Checkboxes
        cb_group = QGroupBox("Checkboxes")
        cb_layout = QVBoxLayout(cb_group)
        self.cb1 = HmcCheckbox("Default option")
        self.cb2 = HmcCheckbox("Checked option")
        self.cb2.setChecked(True)
        self.cb3 = HmcCheckbox("Disabled option")
        self.cb3.setEnabled(False)
        self.cb4 = HmcCheckbox("Disabled checked")
        self.cb4.setChecked(True)
        self.cb4.setEnabled(False)
        for cb in (self.cb1, self.cb2, self.cb3, self.cb4):
            cb_layout.addWidget(cb)
        row1.addWidget(cb_group)

        # Radio buttons
        rb_group = QGroupBox("Radio buttons")
        rb_layout = QVBoxLayout(rb_group)
        self.rb1 = HmcRadio("Option A")
        self.rb1.setChecked(True)
        self.rb2 = HmcRadio("Option B")
        self.rb3 = HmcRadio("Option C")
        self.rb4 = HmcRadio("Disabled")
        self.rb4.setEnabled(False)
        for rb in (self.rb1, self.rb2, self.rb3, self.rb4):
            rb_layout.addWidget(rb)
        row1.addWidget(rb_group)

        # Toggle switches
        toggle_group = QGroupBox("Toggle switches")
        tg_layout = QVBoxLayout(toggle_group)
        self.tg1 = HmcToggleSwitch("Wi-Fi", theme)
        self.tg2 = HmcToggleSwitch("Bluetooth", theme)
        self.tg2.setChecked(True)
        self.tg3 = HmcToggleSwitch("Notifications", theme)
        self.tg4 = HmcToggleSwitch("Disabled toggle", theme)
        self.tg4.setEnabled(False)
        self.toggles = [self.tg1, self.tg2, self.tg3, self.tg4]
        for tg in self.toggles:
            tg_layout.addWidget(tg)
        row1.addWidget(toggle_group)

        scroll_content.addLayout(row1)

        # --- Row 2: Progress bars & text input ------------------------
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # Progress bars
        pb_group = QGroupBox("Progress bars")
        pb_layout = QVBoxLayout(pb_group)

        pb_lbl1 = QLabel("Default (65%)")
        pb_lbl1.setProperty("class", "caption")
        self.pb1 = QProgressBar()
        self.pb1.setValue(65)

        pb_lbl2 = QLabel("Success (100%)")
        pb_lbl2.setProperty("class", "caption")
        self.pb2 = QProgressBar()
        self.pb2.setProperty("class", "success")
        self.pb2.setValue(100)

        pb_lbl3 = QLabel("Danger (30%)")
        pb_lbl3.setProperty("class", "caption")
        self.pb3 = QProgressBar()
        self.pb3.setProperty("class", "danger")
        self.pb3.setValue(30)

        pb_lbl4 = QLabel("Indeterminate")
        pb_lbl4.setProperty("class", "caption")
        self.pb4 = QProgressBar()
        self.pb4.setRange(0, 0)  # indeterminate

        for w in (pb_lbl1, self.pb1, pb_lbl2, self.pb2,
                  pb_lbl3, self.pb3, pb_lbl4, self.pb4):
            pb_layout.addWidget(w)
        row2.addWidget(pb_group)

        # Text input
        ti_group = QGroupBox("Text input")
        ti_layout = QVBoxLayout(ti_group)

        lbl_line = QLabel("Line edit")
        lbl_line.setProperty("class", "caption")
        self.line_edit = QLineEdit()
        self.line_edit.setPlaceholderText("Type something...")

        lbl_text = QLabel("Text area")
        lbl_text.setProperty("class", "caption")
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter longer text here...")
        self.text_edit.setMaximumHeight(100)

        lbl_disabled = QLabel("Disabled")
        lbl_disabled.setProperty("class", "caption")
        self.line_disabled = QLineEdit("Cannot edit")
        self.line_disabled.setEnabled(False)

        for w in (lbl_line, self.line_edit, lbl_text, self.text_edit,
                  lbl_disabled, self.line_disabled):
            ti_layout.addWidget(w)
        row2.addWidget(ti_group)

        # Sliders
        sl_group = QGroupBox("Sliders")
        sl_layout = QVBoxLayout(sl_group)

        sl_lbl1 = QLabel("Horizontal")
        sl_lbl1.setProperty("class", "caption")
        self.slider1 = QSlider(Qt.Orientation.Horizontal)
        self.slider1.setRange(0, 100)
        self.slider1.setValue(40)

        self.sl_val_lbl = QLabel("Gain: -5 dB")
        self.sl_val_lbl.setProperty("class", "caption")
        self.slider_val = QSlider(Qt.Orientation.Horizontal)
        self.slider_val.setRange(-320, 0)
        self.slider_val.setValue(-50)
        self.slider_val.valueChanged.connect(
            lambda v: self.sl_val_lbl.setText(f"Gain: {v/10} dB ...")
        )
        self.slider_val.sliderReleased.connect(
            lambda: self.sl_val_lbl.setText(f"Gain: {self.slider_val.value()/10} dB")
        )

        sl_lbl2 = QLabel("Disabled")
        sl_lbl2.setProperty("class", "caption")
        self.slider2 = QSlider(Qt.Orientation.Horizontal)
        self.slider2.setRange(0, 100)
        self.slider2.setValue(60)
        self.slider2.setEnabled(False)

        for w in (sl_lbl1, self.slider1,
                  self.sl_val_lbl, self.slider_val,
                  sl_lbl2, self.slider2):
            sl_layout.addWidget(w)
        sl_layout.addStretch()
        row2.addWidget(sl_group)

        scroll_content.addLayout(row2)

        # --- Row 3: Buttons & badges ----------------------------------
        row3 = QHBoxLayout()
        row3.setSpacing(16)

        btn_group = QGroupBox("Button variants")
        btn_layout = QVBoxLayout(btn_group)

        for label, cls in [("Primary", None), ("Secondary", "secondary"),
                           ("Tertiary", "tertiary"), ("Ghost", "ghost"),
                           ("Danger", "danger")]:
            btn = QPushButton(label)
            if cls:
                btn.setProperty("class", cls)
            btn.setToolTip(f"This is a {label.lower()} button — hover to see tooltip")
            btn_layout.addWidget(btn)
        btn_disabled = QPushButton("Disabled")
        btn_disabled.setEnabled(False)
        btn_layout.addWidget(btn_disabled)
        row3.addWidget(btn_group)

        badge_group = QGroupBox("Badges & dialog")
        badge_layout = QVBoxLayout(badge_group)

        for text, obj_name in [("Success", "badge-success"), ("Danger", "badge-danger"),
                               ("Warning", "badge-warning"), ("Info", "badge-info"),
                               ("Highlight", "badge-highlight")]:
            badge = QLabel(text)
            badge.setObjectName(obj_name)
            badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
            badge_layout.addWidget(badge)

        badge_layout.addSpacing(8)
        self.btn_dialog = QPushButton("Open dialog")
        self.btn_dialog.setProperty("class", "secondary")
        self.btn_dialog.clicked.connect(self._show_dialog)
        badge_layout.addWidget(self.btn_dialog)
        row3.addWidget(badge_group)

        scroll_content.addLayout(row3)
        scroll_content.addStretch()

    def _show_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Harmonic Dialog")
        dlg.setMinimumWidth(360)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(12)

        lbl = QLabel("Confirm action")
        lbl.setProperty("class", "heading")
        layout.addWidget(lbl)

        desc = QLabel("Are you sure you want to proceed? This is a themed QDialog.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setIcon(
            HmcIcon("mdi6.check", HmcTheme.Token.SUCCESS, parent=dlg)
        )
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setIcon(
            HmcIcon("mdi6.close", HmcTheme.Token.DANGER, parent=dlg)
        )
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        dlg.exec()


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------

class HarmonicDashboard(HmcMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Harmonic Dashboard")
        self.resize(1200, 800)

        # --- Central widget ---
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self._theme)
        main_layout.addWidget(self.sidebar)

        # Content area
        content = QVBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        # --- Header ---
        self.header = QFrame()
        self.header.setProperty("class", "header")
        self.header.setFixedHeight(56)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        self.title_icon = QLabel()
        self._title_icon_hmc = HmcLogoIcon(token=HmcTheme.Token.PRIMARY, parent=self)
        self.title_icon.setPixmap(self._title_icon_hmc.pixmap(32, 32))
        header_layout.addWidget(self.title_icon)

        title = QLabel("Harmonic Dashboard")
        title.setProperty("class", "heading")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Theme toggle button
        self.btn_theme = QPushButton()
        self.btn_theme.setProperty("class", "theme-toggle")
        #self.btn_theme.setFixedSize(40, 40)
        self.btn_theme.setToolTip("Toggle dark mode")
        self._update_theme_button_icon()
        self.btn_theme.clicked.connect(self._toggle_theme)
        header_layout.addWidget(self.btn_theme)

        self.btn_filter = QPushButton("Filter")
        self.btn_filter.setProperty("class", "tertiary")
        self.btn_filter.setIcon(HmcIcon("mdi6.filter", HmcTheme.Token.CONTENT_DEFAULT, parent=self.btn_filter))
        header_layout.addWidget(self.btn_filter)

        self.btn_add = QPushButton("New capture")
        self.btn_add.setIcon(HmcIcon("mdi6.plus", HmcTheme.Token.CONTENT_INVERSE, parent=self.btn_add))
        header_layout.addWidget(self.btn_add)

        content.addWidget(self.header)

        # --- Tabs ---
        self.tabs = QTabWidget()
        self.overview_tab = OverviewTab(self._theme)
        self.analysis_tab = AnalysisTab(self._theme)
        self.components_tab = ComponentsTab(self._theme)
        self.tabs.addTab(self.overview_tab, "Overview")
        self.tabs.addTab(self.analysis_tab, "Analysis")
        self.tabs.addTab(self.components_tab, "Components")
        content.addWidget(self.tabs)

        main_layout.addLayout(content)

        # --- Status bar ---
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.connected = QLabel()
        self.connected.setPixmap(HmcIcon("mdi6.lan-connect", HmcTheme.Token.SUCCESS, parent=self.connected).pixmap(20, 20))
        status_bar.addWidget(self.connected)
        status_bar.addWidget(QLabel("Connected"))

        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)
        self._update_time()

        timer = QTimer(self)
        timer.timeout.connect(self._update_time)
        timer.start(1000)

    def _update_theme_button_icon(self):
        if self._theme.name == "light":
            self.btn_theme.setIcon(HmcIcon("mdi6.weather-night", parent=self.btn_theme))
        else:
            self.btn_theme.setIcon(HmcIcon("mdi6.weather-sunny", parent=self.btn_theme))
        self.btn_theme.setIconSize(QSize(32, 32))

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange and hasattr(self, "title_icon"):
            self.title_icon.setPixmap(self._title_icon_hmc.pixmap(32, 32))
            self._update_theme_button_icon()
        super().changeEvent(event)

    def _toggle_theme(self):
        self.theme = HmcTheme.DARK if self._theme.name == "light" else HmcTheme.LIGHT

    def _update_time(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.setText(f"Last update: {now}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = HarmonicDashboard()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
