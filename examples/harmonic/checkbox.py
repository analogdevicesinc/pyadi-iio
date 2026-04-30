# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic checkbox widget for PySide6.

Subclasses QCheckBox so it's a drop-in replacement with the same
signals (stateChanged, checkStateChanged) and API (isChecked, setChecked,
setTristate, etc.).

Supports three visual states matching the Harmonic web component spec:
  - Unselected: 16x16 box with 1px border, empty
  - Selected: filled box with check-m icon
  - Indeterminate: filled box with subtract-m icon

Usage:
    from adi.harmonic.checkbox import HmcCheckbox
    cb = HmcCheckbox("Accept terms")
    cb.stateChanged.connect(lambda state: print(state))
"""

import qtawesome as qta
from harmonic.container import HmcMainWindow
from harmonic.theme import HmcTheme
from PySide6.QtCore import QEvent, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen, QPixmap
from PySide6.QtWidgets import QCheckBox, QWidget

# Dimensions from checkbox.scss
_BOX_SIZE = 16
_BORDER_RADIUS = 4
_BORDER_WIDTH = 1
_ICON_SIZE = 16
_SPACING = 8


def _icon_pixmap(name: str, color: str, size: int = _ICON_SIZE) -> "QPixmap":
    return qta.icon(name, color=color).pixmap(size, size)


class HmcCheckbox(QCheckBox):
    """A QCheckBox that paints as a Harmonic checkbox with check/subtract icons."""

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

        self._icon_color = t.selection_selected_content
        self._text_color = QColor(t.content_default)
        self._text_disabled = QColor(t.content_weak)

        self._check_pixmap = _icon_pixmap("mdi6.check", self._icon_color)
        self._subtract_pixmap = _icon_pixmap("mdi6.minus", self._icon_color)
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
        w = _BOX_SIZE + ((_SPACING + text_w) if text_w else 0)
        h = max(_BOX_SIZE, fm.height())
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
        indeterminate = self.checkState() == Qt.CheckState.PartiallyChecked
        active = checked or indeterminate
        disabled = not self.isEnabled()
        hovered = self.underMouse() and not disabled

        y_off = (self.height() - _BOX_SIZE) / 2
        box_rect = QRectF(0, y_off, _BOX_SIZE, _BOX_SIZE)

        if active:
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

        p.drawRoundedRect(box_rect, _BORDER_RADIUS, _BORDER_RADIUS)

        if active:
            icon_offset = int((_BOX_SIZE - _ICON_SIZE) / 2)
            pixmap = self._subtract_pixmap if indeterminate else self._check_pixmap
            p.drawPixmap(icon_offset, int(y_off) + icon_offset, pixmap)

        if self.text():
            p.setPen(self._text_disabled if disabled else self._text_color)
            p.setFont(self.font())
            fm = QFontMetrics(self.font())
            text_x = _BOX_SIZE + _SPACING
            text_y = int((self.height() + fm.ascent() - fm.descent()) / 2)
            p.drawText(text_x, text_y, self.text())

        p.end()

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)
