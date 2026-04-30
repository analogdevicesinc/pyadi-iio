# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic radio button widget for PySide6.

Subclasses QRadioButton so it's a drop-in replacement with the same
signals (toggled) and API (isChecked, setChecked, etc.).

Matches the Harmonic web component spec:
  - Outer circle: 16x16 px, 1 px border, fully round
  - When selected: filled circle with a 6x6 inner dot in content-inverse color
  - When unselected: empty circle with border

Usage:
    from adi.harmonic.radio import HmcRadio
    rb = HmcRadio("Option A")
    rb.toggled.connect(lambda on: print("Option A", on))
"""

from harmonic.container import HmcMainWindow
from harmonic.theme import HmcTheme
from PySide6.QtCore import QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QRadioButton, QWidget

# Dimensions from radio-button.scss
_CIRCLE_SIZE = 16
_BORDER_WIDTH = 1
_DOT_SIZE = 6
_SPACING = 8


class HmcRadio(QRadioButton):
    """A QRadioButton that paints as a Harmonic radio with an inner dot."""

    def __init__(
        self,
        text: str = "",
        theme: HmcTheme | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        self._apply_colors(theme or HmcTheme.default)

    # --- theming ----------------------------------------------------------

    def _apply_colors(self, t: HmcTheme):
        self._border_idle = QColor(t.selection_unselected_border)
        self._border_hover = QColor(t.selection_unselected_border_hover)
        self._border_disabled = QColor(t.selection_unselected_border_disabled)

        self._bg_container = QColor(t.layout_container)

        self._selected_bg = QColor(t.selection_selected_bg)
        self._selected_bg_hover = QColor(t.selection_selected_bg_hover)
        self._selected_bg_disabled = QColor(t.selection_selected_bg_disabled)

        self._dot_color = QColor(t.content_inverse)
        self._text_color = QColor(t.content_default)
        self._text_disabled = QColor(t.content_weak)
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange:
            window = self.window()
            if isinstance(window, HmcMainWindow):
                self._apply_colors(window.theme)
        super().changeEvent(event)

    # --- size hints -------------------------------------------------------

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(self.text()) if self.text() else 0
        w = _CIRCLE_SIZE + ((_SPACING + text_w) if text_w else 0)
        h = max(_CIRCLE_SIZE, fm.height())
        return QSize(w, h)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    # --- hit test ---------------------------------------------------------

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    # --- paint ------------------------------------------------------------

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        checked = self.isChecked()
        disabled = not self.isEnabled()
        hovered = self.underMouse() and not disabled

        y_off = (self.height() - _CIRCLE_SIZE) / 2
        circle_rect = QRectF(0, y_off, _CIRCLE_SIZE, _CIRCLE_SIZE)

        if checked:
            p.setPen(Qt.PenStyle.NoPen)
            if disabled:
                p.setBrush(self._selected_bg_disabled)
            elif hovered:
                p.setBrush(self._selected_bg_hover)
            else:
                p.setBrush(self._selected_bg)
        else:
            if disabled:
                border_color = self._border_disabled
            elif hovered:
                border_color = self._border_hover
            else:
                border_color = self._border_idle
            p.setPen(QPen(border_color, _BORDER_WIDTH))
            p.setBrush(self._bg_container)

        p.drawEllipse(circle_rect)

        if checked:
            dot_offset = (_CIRCLE_SIZE - _DOT_SIZE) / 2
            dot_rect = QRectF(dot_offset, y_off + dot_offset, _DOT_SIZE, _DOT_SIZE)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self._dot_color)
            p.drawEllipse(dot_rect)

        if self.text():
            p.setPen(self._text_disabled if disabled else self._text_color)
            p.setFont(self.font())
            fm = QFontMetrics(self.font())
            text_x = _CIRCLE_SIZE + _SPACING
            text_y = int((self.height() + fm.ascent() - fm.descent()) / 2)
            p.drawText(text_x, text_y, self.text())

        p.end()

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)
