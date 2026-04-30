# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic toggle-switch widget for PySide6.

Subclasses QCheckBox so it's a drop-in replacement with the same
signals (toggled, stateChanged) and API (isChecked, setChecked, etc.).

Matches the Harmonic web component spec:
  - Track: 35x16 px, border-radius 8 px
  - Knob: 14x14 px circle, 1 px margin
  - Knob slides 19 px when checked, 200 ms animation

Usage:
    from adi.harmonic.toggle import HmcToggleSwitch
    toggle = HmcToggleSwitch("Wi-Fi")
    toggle.toggled.connect(lambda on: print("Wi-Fi", on))
"""

from harmonic.container import HmcMainWindow
from harmonic.theme import HmcTheme
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QEvent,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
)
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import QCheckBox, QWidget

# Dimensions from toggle.scss
_TRACK_W = 35
_TRACK_H = 16
_KNOB_SIZE = 14
_KNOB_MARGIN = 1
_KNOB_TRAVEL = 19  # translateX distance when checked
_ANIM_DURATION = 200
_SPACING = 8


class HmcToggleSwitch(QCheckBox):
    """A QCheckBox that paints as a Harmonic toggle switch with animated knob."""

    def __init__(
        self,
        text: str = "",
        theme: HmcTheme | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(text, parent)
        t = theme or HmcTheme.default

        self._offset = 0.0

        self._anim = QPropertyAnimation(self, b"offset")
        self._anim.setDuration(_ANIM_DURATION)
        self._anim.setEasingCurve(QEasingCurve.Type.Linear)

        self.toggled.connect(self._run_animation)
        self._apply_colors(t)

    # --- animated property -------------------------------------------

    def _get_offset(self) -> float:
        return self._offset

    def _set_offset(self, v: float):
        self._offset = v
        self.update()

    offset = Property(float, _get_offset, _set_offset)

    # --- theming ------------------------------------------------------

    def _apply_colors(self, t: HmcTheme):
        self._track_off = QColor(t.selection_unselected_bg)
        self._track_off_hover = QColor(t.selection_unselected_bg_hover)
        self._track_off_disabled = QColor(t.selection_unselected_bg_disabled)
        self._track_on = QColor(t.selection_selected_bg)
        self._track_on_hover = QColor(t.selection_selected_bg_hover)
        self._track_on_disabled = QColor(t.selection_selected_bg_disabled)
        self._knob_color = QColor(t.selection_unselected_content)
        self._text_color = QColor(t.content_default)
        self._text_disabled = QColor(t.content_weak)
        self.update()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.StyleChange:
            window = self.window()
            if isinstance(window, HmcMainWindow):
                self._apply_colors(window.theme)
        super().changeEvent(event)

    # --- overrides ----------------------------------------------------

    def setChecked(self, on: bool):
        super().setChecked(on)
        # Snap knob position without animation
        self._offset = float(_KNOB_TRAVEL) if on else 0.0
        self.update()

    # --- animation ----------------------------------------------------

    def _run_animation(self, checked: bool):
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(float(_KNOB_TRAVEL) if checked else 0.0)
        self._anim.start()

    # --- size hints ---------------------------------------------------

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(self.font())
        text_w = fm.horizontalAdvance(self.text()) if self.text() else 0
        w = _TRACK_W + ((_SPACING + text_w) if text_w else 0)
        h = max(_TRACK_H, fm.height())
        return QSize(w, h)

    def minimumSizeHint(self) -> QSize:
        return self.sizeHint()

    # --- hit test: click anywhere on widget toggles -------------------

    def hitButton(self, pos) -> bool:
        return self.rect().contains(pos)

    # --- paint --------------------------------------------------------

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Vertical centering
        y_off = (self.height() - _TRACK_H) / 2

        # Track color
        if not self.isEnabled():
            track_c = (
                self._track_on_disabled
                if self.isChecked()
                else self._track_off_disabled
            )
        elif self.underMouse():
            track_c = (
                self._track_on_hover if self.isChecked() else self._track_off_hover
            )
        else:
            track_c = self._track_on if self.isChecked() else self._track_off

        # Draw track
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(track_c)
        p.drawRoundedRect(
            QRect(0, int(y_off), _TRACK_W, _TRACK_H), _TRACK_H / 2, _TRACK_H / 2,
        )

        # Draw knob
        knob_x = _KNOB_MARGIN + self._offset
        knob_y = y_off + _KNOB_MARGIN
        p.setBrush(self._knob_color)
        p.drawEllipse(int(knob_x), int(knob_y), _KNOB_SIZE, _KNOB_SIZE)

        # Draw label text
        if self.text():
            p.setPen(self._text_disabled if not self.isEnabled() else self._text_color)
            p.setFont(self.font())
            fm = QFontMetrics(self.font())
            text_x = _TRACK_W + _SPACING
            text_y = int((self.height() + fm.ascent() - fm.descent()) / 2)
            p.drawText(text_x, text_y, self.text())

        p.end()

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)
