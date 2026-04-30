# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic-styled pyqtgraph PlotWidget."""

import numpy as np
import pyqtgraph as pg
from harmonic.colors import INTENSITY
from harmonic.container import HmcMainWindow
from harmonic.theme import HmcTheme
from PySide6.QtCore import QEvent


def HmcColorMap(name: str = "dark", reverse: bool = False) -> pg.ColorMap:
    """Build a pyqtgraph ColorMap from a Harmonic intensity ramp.

    Args:
        name: key into ``harmonic.colors.INTENSITY``.
        reverse: flip the ramp (bright lows, dark highs) for light backgrounds.
    """
    try:
        stops = list(INTENSITY[name])
    except KeyError:
        raise KeyError(
            f"unknown colormap {name!r}; available: {sorted(INTENSITY)}"
        ) from None
    if reverse:
        stops.reverse()
    positions = np.linspace(0.0, 1.0, len(stops))
    return pg.ColorMap(positions, [pg.mkColor(c) for c in stops])


class HmcPlot(pg.PlotWidget):
    """A pyqtgraph PlotWidget themed to match Harmonic."""

    def __init__(self, theme: HmcTheme | None = None, title: str = "", **kwargs):
        super().__init__(**kwargs)
        self._title = title
        self.setMinimumHeight(220)
        self._apply_colors(theme or HmcTheme.default)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange:
            window = self.window()
            if isinstance(window, HmcMainWindow):
                self._apply_colors(window.theme)
        super().changeEvent(event)

    def _apply_colors(self, theme: HmcTheme):
        self.setBackground(theme.layout_container)

        if self._title:
            self.setTitle(self._title, color=theme.content_default, size="14px")
        else:
            label = self.getPlotItem().titleLabel
            if label.text:
                label.setText(label.text, color=theme.content_default)

        for axis_name in ("bottom", "left"):
            axis = self.getAxis(axis_name)
            axis.setPen(pg.mkPen(theme.layout_divider, width=1))
            axis.setTextPen(pg.mkPen(theme.content_medium))
            axis.setStyle(tickLength=-8)

        self.getPlotItem().showGrid(x=True, y=True, alpha=0.15)

        legend = self.getPlotItem().legend
        if legend:
            legend.setLabelTextColor(theme.content_medium)
            legend.setBrush(pg.mkBrush(theme.layout_container))
            legend.setPen(pg.mkPen(theme.layout_divider_weak))
