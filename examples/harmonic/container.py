# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic container widgets for PySide6."""

from harmonic.colors import FONT_FAMILY_BODY
from harmonic.theme import HmcTheme
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QFrame, QLayout, QMainWindow


class HmcMainWindow(QMainWindow):
    """A QMainWindow that manages the Harmonic theme.

    Sets the stylesheet on itself so it cascades to all child widgets.
    Works with any ``QApplication`` — no custom app subclass needed.
    """

    def __init__(self, *args, theme: HmcTheme | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._theme = theme or HmcTheme.default
        self.setStyleSheet(self._theme.styleSheet())
        self.setFont(QFont(FONT_FAMILY_BODY, 14))

    @property
    def theme(self) -> HmcTheme:
        return self._theme

    @theme.setter
    def theme(self, theme: HmcTheme):
        self._theme = theme
        self.setStyleSheet(theme.styleSheet())


class HmcCard(QFrame):
    """A QFrame with the Harmonic ``card`` style class applied."""

    def __init__(self, layout: QLayout | None = None, **kwargs):
        super().__init__(**kwargs)
        self.setProperty("class", "card")
        if layout is not None:
            self.setLayout(layout)
