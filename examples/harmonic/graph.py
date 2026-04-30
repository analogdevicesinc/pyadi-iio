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

    #: max distance, in pixels, between the cursor and a data point to snap
    SNAP_RADIUS = 24

    def __init__(
        self,
        theme: HmcTheme | None = None,
        title: str = "",
        hover: bool = True,
        hover_format=None,
        **kwargs,
    ):
        """
        Args:
            theme: initial theme; follows the window theme afterwards.
            title: plot title.
            hover: show a tooltip with the nearest data point under the cursor.
            hover_format: optional ``f(x, y, name) -> str`` for the tooltip text.
        """
        super().__init__(**kwargs)
        self._title = title
        self._hover_format = hover_format
        self.setMinimumHeight(220)
        self._init_hover(hover)
        self._apply_colors(theme or HmcTheme.default)

    def _init_hover(self, enabled: bool):
        # Added straight to the ViewBox so PlotItem.clear() and
        # listDataItems() leave them alone.
        vb = self.getPlotItem().getViewBox()
        self._hover_marker = pg.ScatterPlotItem(size=9, pxMode=True)
        self._hover_label = pg.TextItem(anchor=(0, 1))
        for item in (self._hover_marker, self._hover_label):
            item.setZValue(1e9)
            item.hide()
            vb.addItem(item, ignoreBounds=True)
        self._hover_enabled = enabled
        self.scene().sigMouseMoved.connect(self._on_mouse_moved)

    def _hide_hover(self):
        self._hover_marker.hide()
        self._hover_label.hide()

    def leaveEvent(self, event):
        self._hide_hover()
        super().leaveEvent(event)

    def _on_mouse_moved(self, scene_pos):
        vb = self.getPlotItem().getViewBox()
        if not self._hover_enabled or not vb.sceneBoundingRect().contains(scene_pos):
            self._hide_hover()
            return

        mouse = vb.mapSceneToView(scene_pos)
        px_w, px_h = vb.viewPixelSize()
        best = None  # (dist², x, y, item)
        for item in self.getPlotItem().listDataItems():
            if not item.isVisible():
                continue
            xs, ys = item.getData()
            if xs is None or len(xs) == 0:
                continue
            # Distance in screen pixels so both axes weigh the same.
            d2 = ((xs - mouse.x()) / px_w) ** 2 + ((ys - mouse.y()) / px_h) ** 2
            if np.all(np.isnan(d2)):
                continue
            i = int(np.nanargmin(d2))
            if best is None or d2[i] < best[0]:
                best = (d2[i], float(xs[i]), float(ys[i]), item)

        if best is None or best[0] > self.SNAP_RADIUS**2:
            self._hide_hover()
            return

        _, x, y, item = best
        name = item.name() or ""
        if self._hover_format:
            text = self._hover_format(x, y, name)
        else:
            text = f"x: {x:.6g}\ny: {y:.6g}"
            if name:
                text = f"{name}\n{text}"

        pen = item.opts.get("pen")
        color = pg.mkPen(pen).color() if pen is not None else self._hover_label.color
        self._hover_marker.setData(
            [x], [y], brush=pg.mkBrush(color), pen=self._hover_marker_pen
        )
        self._hover_label.setText(text)

        # Flip the label to the other side of the point near the view edges.
        self._hover_label.setPos(x, y)
        label_rect = self._hover_label.boundingRect()
        point = vb.mapViewToScene(pg.Point(x, y))
        view_rect = vb.sceneBoundingRect()
        anchor_x = 1 if point.x() + label_rect.width() + 12 > view_rect.right() else 0
        anchor_y = 0 if point.y() - label_rect.height() - 12 < view_rect.top() else 1
        self._hover_label.setAnchor((anchor_x, anchor_y))

        self._hover_marker.show()
        self._hover_label.show()

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

        # Mirror the QToolTip rules from the theme stylesheet.
        self._hover_label.setColor(theme.tooltip_text or theme.content_default)
        self._hover_label.fill = pg.mkBrush(theme.tooltip_bg or theme.layout_canvas)
        self._hover_label.border = pg.mkPen(theme.layout_divider, width=1)
        font = self._hover_label.textItem.font()
        font.setPixelSize(12)
        self._hover_label.setFont(font)
        self._hover_label.update()
        self._hover_marker_pen = pg.mkPen(theme.layout_container, width=2)
