# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic-styled scrolling intensity map."""

import numpy as np
import pyqtgraph as pg
from harmonic.container import HmcMainWindow
from harmonic.graph import HmcColorMap, HmcPlot
from harmonic.theme import HmcTheme
from PySide6.QtCore import QEvent, QRectF
from PySide6.QtWidgets import QBoxLayout, QWidget


class HmcWaterfall(QWidget):
    """A scrolling intensity map (waterfall / spectrogram).

    Rows are pushed one at a time and scroll along the time axis.  Row 0 of the
    internal buffer is always the newest one; ``newest`` picks which edge of the
    plot that is, by flipping the axis rather than the data.

    An optional side graph plots the row as it is pushed, along with any
    parallel traces handed to ``pushRow``.  It shares the data axis with the
    image and sits on the ``newest`` edge, so a feature lines up with the trace
    that produced it.  Its value axis grows away from the image and spans
    ``levels``, keeping it in step with the colors.  Orientation and the newest
    edge are fixed at construction; the side graph can be toggled at runtime.

    Args:
        bins: samples per row (e.g. FFT length).  ``pushRow`` resizes to match.
        history: number of rows kept.
        orientation: ``"vertical"`` puts the data on x and time on y,
            ``"horizontal"`` puts time on x and the data on y.
        colormap: key into ``harmonic.colors.INTENSITY``, or ``"harmonic"`` to
            follow the theme (the ``"dark"`` ramp on a dark background, the
            ``"light"`` one on a light background).
        levels: ``(low, high)`` value range mapped onto the colormap.
        newest: edge holding the newest row — ``"top"``/``"bottom"`` when
            vertical, ``"left"``/``"right"`` when horizontal.
        fill: value the buffer is (re)initialized with, ``levels[0]`` by default.
        frameInterval: seconds between rows.  When given, the time axis is
            labelled in elapsed seconds instead of frames.
        colorbar: add a themed color bar beside the image.
        trace: show the side graph.  Toggle later with ``setTraceVisible``.
        traceRatio: fraction of the widget the side graph takes.
    """

    _NEWEST_EDGES = {
        "vertical": ("top", "bottom"),
        "horizontal": ("left", "right"),
    }
    # Fixed extent for the axis shared between the two plots, so their data
    # axes line up however wide the tick labels get.
    _VALUE_AXIS_WIDTH = 64
    _VALUE_AXIS_HEIGHT = 34
    _COLORBAR_WIDTH = 76
    # Colormap name that follows the theme instead of naming a ramp: the
    # ``"dark"`` and ``"light"`` ramps are keyed by HmcTheme.name.
    _THEME_COLORMAP = "harmonic"

    class _ImagePlot(HmcPlot):
        """The image half: no grid, no mouse, no buttons."""

        def _apply_colors(self, theme: HmcTheme):
            super()._apply_colors(theme)
            plot_item = self.getPlotItem()
            plot_item.showGrid(x=False, y=False)
            plot_item.setMouseEnabled(x=False, y=False)
            plot_item.hideButtons()

    def __init__(
        self,
        bins: int = 1024,
        history: int = 256,
        orientation: str = "vertical",
        colormap: str = "harmonic",
        levels: tuple[float, float] = (-120.0, 0.0),
        newest: str | None = None,
        fill: float | None = None,
        frameInterval: float | None = None,
        colorbar: bool = False,
        trace: bool = False,
        traceRatio: float = 0.3,
        theme: HmcTheme | None = None,
        title: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._bins = int(bins)
        self._history = max(1, int(history))
        self._orientation = self._checked_orientation(orientation)
        self._levels = (float(levels[0]), float(levels[1]))
        self._newest = self._checked_newest(newest, self._orientation)
        self._vertical = self._orientation == "vertical"
        self._fill = self._levels[0] if fill is None else float(fill)
        self._frame_interval = frameInterval
        self._colormap_name = colormap
        self._data_range = (0.0, float(self._bins))
        self._data_label = ("Bin", None)
        self._value_label = ("Magnitude", None)
        self._trace_ratio = min(max(float(traceRatio), 0.05), 0.9)
        self._colorbar = None
        self._buffer = np.full((self._history, self._bins), self._fill, dtype=np.float32)
        self._axis = np.linspace(*self._data_range, self._bins)

        self._theme = theme or HmcTheme.default
        self._title = title
        self.image_plot = self._ImagePlot(theme=self._theme)
        self.trace_plot = HmcPlot(theme=self._theme)
        self.trace_plot.setMinimumHeight(80)
        self.trace_plot.setVisible(trace)
        # Newest edge first: top/left holds the trace, the image follows.
        self._order = [self.trace_plot, self.image_plot]
        if self._newest in ("bottom", "right"):
            self._order.reverse()

        self._image = pg.ImageItem()
        self._image.setColorMap(self._resolved_colormap())
        self.image_plot.addItem(self._image)
        self._trace = self.trace_plot.plot(
            [], [], pen=pg.mkPen(self._theme.categorical[0], width=2)
        )
        self._aux = []  # parallel traces from the last pushRow
        self._aux_curves = []

        # The two plots stack along the time axis; the color bar sits outside
        # that stack so it cannot shrink the image out of line with the trace.
        self._stack = QWidget()
        self._layout = QBoxLayout(QBoxLayout.Direction.TopToBottom, self._stack)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        outer = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(self._stack, 1)

        if colorbar:
            self._colorbar = pg.ColorBarItem(
                values=self._levels,
                colorMap=self._resolved_colormap(),
                interactive=False,
            )
            self._colorbar.setImageItem(self._image)
            self._colorbar_view = pg.GraphicsLayoutWidget()
            self._colorbar_view.setFixedWidth(self._COLORBAR_WIDTH)
            self._colorbar_view.addItem(self._colorbar)
            outer.addWidget(self._colorbar_view)
            self._color_colorbar(self._theme)

        self._apply_layout()
        self._redraw()

    # -- configuration ------------------------------------------------------

    @property
    def levels(self) -> tuple[float, float]:
        return self._levels

    def setLevels(self, low: float, high: float):
        """Set the value range mapped onto the colormap and the side graph."""
        self._levels = (float(low), float(high))
        self._image.setLevels(self._levels)
        if self._colorbar is not None:
            self._colorbar.setLevels(self._levels)
        self._range_trace()

    def setTraceVisible(self, visible: bool):
        """Show or hide the side graph."""
        self.trace_plot.setVisible(bool(visible))
        # With the trace gone the image has to take the data axis back over.
        self._label_axes()

    def isTraceVisible(self) -> bool:
        # isHidden(), not isVisible(): the answer must not depend on whether
        # the waterfall itself has been shown yet.
        return not self.trace_plot.isHidden()

    def setValueLabel(self, label: str, units: str | None = None):
        """Label the side graph's value axis, e.g. ("Magnitude", "dBV")."""
        self._value_label = (label, units)
        self._label_axes()

    def autoLevels(self, lowPct: float = 5.0, highPct: float = 99.5):
        """Fit the levels to the buffer contents using percentiles."""
        finite = self._buffer[np.isfinite(self._buffer)]
        if finite.size == 0:
            return
        low, high = (float(v) for v in np.percentile(finite, [lowPct, highPct]))
        self.setLevels(low, high if high > low else low + 1.0)

    def setColorMap(self, name: str):
        """Swap the intensity ramp (see ``harmonic.colors.INTENSITY``).

        ``"harmonic"`` is not a ramp of its own: it tracks the theme, using the
        ``"dark"`` ramp on a dark background and ``"light"`` on a light one.
        """
        self._colormap_name = name
        self._apply_colormap()

    def colorMapName(self) -> str:
        """The requested name, which may be the ``"harmonic"`` keyword."""
        return self._colormap_name

    def setHistory(self, history: int):
        """Resize the time axis, keeping as many recent rows as still fit."""
        history = max(1, int(history))
        if history == self._history:
            return
        buffer = np.full((history, self._bins), self._fill, dtype=np.float32)
        keep = min(history, self._history)
        buffer[:keep] = self._buffer[:keep]
        self._buffer = buffer
        self._history = history
        self._redraw()

    def setDataRange(
        self,
        start: float,
        stop: float,
        label: str = "Frequency",
        units: str | None = "Hz",
    ):
        """Map the bin axis onto real units, e.g. an FFT frequency span."""
        self._data_range = (float(start), float(stop))
        self._data_label = (label, units)
        self._axis = np.linspace(*self._data_range, self._bins)
        self._label_axes()
        self._redraw()

    # -- data ---------------------------------------------------------------

    def pushRow(self, row, *aux):
        """Append one time step; the oldest one falls off the far edge.

        The first row is the main one: it scrolls into the image and drives the
        side graph. Any further rows — passed as extra arguments or as the
        remaining rows of a 2-D ``row`` — are parallel data for that same time
        step (a threshold, a running average, the other receiver) and are drawn
        on the side graph only. They must be the same length as the main row.

        Note the difference from ``pushRows``, which takes consecutive rows in
        time rather than parallel traces of one time step.
        """
        rows = [np.asarray(r, dtype=np.float32).ravel() for r in (row, *aux)]
        if len(rows) == 1 and np.ndim(row) > 1:
            rows = list(np.asarray(row, dtype=np.float32).reshape(-1, np.shape(row)[-1]))

        main = rows[0]
        if main.size != self._bins:
            self._resize_bins(main.size)
        bad = [r.size for r in rows[1:] if r.size != main.size]
        if bad:
            raise ValueError(
                f"auxiliary traces must be {main.size} samples long, got {bad}"
            )

        self._buffer[1:] = self._buffer[:-1]
        self._buffer[0] = main
        self._aux = rows[1:]
        self._redraw()

    def pushRows(self, rows):
        """Append several consecutive time steps at once, oldest first."""
        for row in np.atleast_2d(np.asarray(rows, dtype=np.float32)):
            self.pushRow(row)

    def clearData(self):
        """Reset every row to the fill value and drop the auxiliary traces."""
        self._buffer[:] = self._fill
        self._aux = []
        self._redraw()

    # -- internals ----------------------------------------------------------

    @classmethod
    def _checked_orientation(cls, orientation: str) -> str:
        if orientation not in cls._NEWEST_EDGES:
            raise ValueError(
                f"orientation must be one of {sorted(cls._NEWEST_EDGES)},"
                f" got {orientation!r}"
            )
        return orientation

    @classmethod
    def _checked_newest(cls, newest: str | None, orientation: str) -> str:
        edges = cls._NEWEST_EDGES[orientation]
        if newest is None:
            return edges[0]
        if newest not in edges:
            raise ValueError(
                f"newest must be one of {list(edges)} for a {orientation}"
                f" waterfall, got {newest!r}"
            )
        return newest

    def _resolved_colormap(self) -> pg.ColorMap:
        """Build the ramp, resolving the ``"harmonic"`` keyword to the theme."""
        name = self._colormap_name
        if name == self._THEME_COLORMAP:
            name = self._theme.name
        return HmcColorMap(name)

    def _apply_colormap(self):
        colormap = self._resolved_colormap()
        self._image.setColorMap(colormap)
        if self._colorbar is not None:
            self._colorbar.setColorMap(colormap)

    def _resize_bins(self, bins: int):
        self._bins = int(bins)
        self._buffer = np.full((self._history, self._bins), self._fill, dtype=np.float32)
        if self._data_label[0] == "Bin":
            self._data_range = (0.0, float(self._bins))
        self._axis = np.linspace(*self._data_range, self._bins)
        self._label_axes()

    def _apply_layout(self):
        """Arrange the two plots. Orientation is fixed at construction."""
        # row-major reads the buffer as (y=time, x=bins); col-major swaps them.
        self._image.setOpts(axisOrder="row-major" if self._vertical else "col-major")

        image = self.image_plot.getPlotItem()
        trace = self.trace_plot.getPlotItem()
        image.invertY(self._newest == "top")
        image.invertX(self._newest == "right")
        # Mirror the trace so its values grow away from the image.
        trace.invertY(self._newest == "bottom")
        trace.invertX(self._newest == "left")

        # Stack along the time axis, newest edge first, and tie the two
        # together along the shared data axis.
        self._layout.setDirection(
            QBoxLayout.Direction.TopToBottom
            if self._vertical
            else QBoxLayout.Direction.LeftToRight
        )
        for widget in self._order:
            self._layout.addWidget(widget)
        trace_stretch = max(1, round(self._trace_ratio * 10))
        self._layout.setStretchFactor(self.trace_plot, trace_stretch)
        self._layout.setStretchFactor(self.image_plot, 10 - trace_stretch)

        if self._vertical:
            trace.setXLink(image)
        else:
            trace.setYLink(image)

        self._apply_title()
        self._label_axes()
        self._range_trace()

    def _apply_title(self):
        """Title on the leading plot; a blank one keeps the pair aligned."""
        lead = self._order[0]
        for plot in (self.image_plot, self.trace_plot):
            # HmcPlot._title is what survives a theme change.
            plot._title = self._title if plot is lead else ""
            if plot is not lead and self._title and not self._vertical:
                # Side by side, both need the title row or the shared axis
                # would sit at different heights.
                plot._title = " "
            plot.setTitle(plot._title or None, color=self._theme.content_default)

    def _label_axes(self):
        """Data axis on the outer edge, value axis on the trace only.

        Both plots keep the axis parallel to the shared one at a fixed extent
        so their data axes stay aligned.
        """
        image = self.image_plot.getPlotItem()
        trace = self.trace_plot.getPlotItem()
        data_label, data_units = self._data_label
        value_label, value_units = self._value_label
        data_axis, value_axis = (
            ("bottom", "left") if self._vertical else ("left", "bottom")
        )

        for plot_item in (image, trace):
            if self._vertical:
                plot_item.getAxis(value_axis).setWidth(self._VALUE_AXIS_WIDTH)
            else:
                plot_item.getAxis(value_axis).setHeight(self._VALUE_AXIS_HEIGHT)

        # The data axis belongs on the outer edge of the pair: the lower plot
        # when vertical, the leftmost when horizontal.  The other hides it to
        # avoid a duplicate — unless the trace is hidden, leaving only one.
        outer = self._order[-1] if self._vertical else self._order[0]
        if not self.isTraceVisible():
            outer = self.image_plot
        for plot in (self.image_plot, self.trace_plot):
            plot_item = plot.getPlotItem()
            if plot is outer:
                plot_item.showAxis(data_axis)
                plot_item.setLabel(data_axis, data_label, units=data_units)
            else:
                plot_item.hideAxis(data_axis)

        trace.setLabel(value_axis, value_label, units=value_units)
        if self._frame_interval:
            image.setLabel(value_axis, "Elapsed", units="s")
        else:
            image.setLabel(value_axis, "Frames")

    def _range_trace(self):
        """Pin the trace's value axis to the color levels."""
        trace = self.trace_plot.getPlotItem()
        if self._vertical:
            trace.setYRange(*self._levels, padding=0.0)
        else:
            trace.setXRange(*self._levels, padding=0.0)

    def _draw_trace(self, curve, values):
        """Plot one trace against the data axis, whichever way it runs."""
        if self._vertical:
            curve.setData(self._axis, values)
        else:
            curve.setData(values, self._axis)

    def _sync_aux_curves(self):
        """Match the auxiliary curve count to the last pushed row."""
        palette = self._theme.categorical
        while len(self._aux_curves) < len(self._aux):
            color = palette[(len(self._aux_curves) + 1) % len(palette)]
            self._aux_curves.append(
                self.trace_plot.plot([], [], pen=pg.mkPen(color, width=1))
            )
        for curve in self._aux_curves[len(self._aux) :]:
            curve.setData([], [])

    def _redraw(self):
        start, stop = self._data_range
        span = stop - start
        elapsed = self._history * float(self._frame_interval or 1.0)
        if self._vertical:
            rect = QRectF(start, 0.0, span, elapsed)
        else:
            rect = QRectF(0.0, start, elapsed, span)

        self._draw_trace(self._trace, self._buffer[0])
        self._sync_aux_curves()
        for curve, values in zip(self._aux_curves, self._aux):
            self._draw_trace(curve, values)

        self._image.setImage(self._buffer, autoLevels=False, levels=self._levels)
        self._image.setRect(rect)
        self.image_plot.getPlotItem().setRange(rect, padding=0.0, disableAutoRange=True)

    def _color_colorbar(self, theme: HmcTheme):
        self._colorbar_view.setBackground(theme.layout_container)
        axis = self._colorbar.getAxis("right")
        axis.setPen(pg.mkPen(theme.layout_divider, width=1))
        axis.setTextPen(pg.mkPen(theme.content_medium))

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange:
            window = self.window()
            if isinstance(window, HmcMainWindow):
                theme = self._theme = window.theme
                palette = theme.categorical
                self._trace.setPen(pg.mkPen(palette[0], width=2))
                for idx, curve in enumerate(self._aux_curves, start=1):
                    curve.setPen(pg.mkPen(palette[idx % len(palette)], width=1))
                # Flips the ramp too when the name is the theme keyword.
                self._apply_colormap()
                if self._colorbar is not None:
                    self._color_colorbar(theme)
        super().changeEvent(event)
