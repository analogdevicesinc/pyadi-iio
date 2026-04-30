# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic icons for PySide6.

Uses qtawesome for font-based icons and supports SVG recoloring.
Icons auto-update when the theme changes if created with a ``parent``
widget — the parent's ``StyleChange`` event triggers a rebuild.
"""

from pathlib import Path

import qtawesome as qta
from harmonic.container import HmcMainWindow
from harmonic.theme import HmcTheme
from PySide6.QtCore import QByteArray, QEvent, QObject, Qt
from PySide6.QtGui import QIcon, QIconEngine, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QWidget

_ADI_LOGO_SVG = """
<svg width="24" height="24" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
  <path d="M0 32H32V0H0V32ZM6.58523 4.98152L26.6496 16.2035L6.58523 27.9414V4.98152Z" fill="currentColor"/>
</svg>
"""


class HmcIconData(QObject):
    """Holds the parameters needed to rebuild a qtawesome icon per theme.

    When ``parent`` is a QWidget, installs an event filter so the icon
    auto-updates on ``StyleChange`` (triggered by stylesheet cascading
    from ``HmcMainWindow``).
    """

    def __init__(
        self,
        name: str,
        token: HmcTheme.Token = HmcTheme.Token.CONTENT_DEFAULT,
        theme: HmcTheme | None = None,
        parent: QWidget | None = None,
        **kwargs,
    ):
        super().__init__(parent)
        self.name = name
        self.token = token
        self.kwargs = kwargs
        self.icon: QIcon | None = None
        self.apply_theme(theme or HmcTheme.default)
        if parent and token:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.StyleChange:
            window = obj.window()
            if isinstance(window, HmcMainWindow):
                self.apply_theme(window.theme)
        return False

    def apply_theme(self, theme: HmcTheme):
        if self.token:
            self.kwargs["color"] = getattr(
                theme, self.token.value, theme.content_default
            )
        self.icon = qta.icon(self.name, **self.kwargs)


class HmcSvgIconData(QObject):
    """Holds the parameters needed to rebuild an SVG icon per theme.

    When ``parent`` is a QWidget, installs an event filter so the icon
    auto-updates on ``StyleChange``.
    """

    def __init__(
        self,
        svg_text: str,
        size: int,
        token: HmcTheme.Token = HmcTheme.Token.CONTENT_DEFAULT,
        theme: HmcTheme | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.svg_text = svg_text
        self.token = token
        self.size = size
        self.icon: QIcon | None = None
        self.apply_theme(theme or HmcTheme.default)
        if parent and token:
            parent.installEventFilter(self)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.StyleChange:
            window = obj.window()
            if isinstance(window, HmcMainWindow):
                self.apply_theme(window.theme)
        return False

    def apply_theme(self, theme: HmcTheme):
        svg = self.svg_text
        if self.token:
            color = getattr(theme, self.token.value, theme.content_default)
            svg = svg.replace("currentColor", color)
        renderer = QSvgRenderer(QByteArray(svg.encode()))
        pm = QPixmap(self.size, self.size)
        pm.fill(Qt.GlobalColor.transparent)
        with QPainter(pm) as p:
            renderer.render(p)
        self.icon = QIcon(pm)


class HmcIconEngine(QIconEngine):
    """HmcIconEngine that delegates painting to an ``icon``.

    All clones share the same ``data`` object, so when the theme
    changes and ``data.icon`` is rebuilt, every clone paints with the
    new icon on the next repaint.
    """

    def __init__(self, data):
        super().__init__()
        self._data = data

    def paint(self, painter, rect, mode, state):
        if self._data.icon:
            pm = self._data.icon.pixmap(rect.size(), mode, state)
            painter.drawPixmap(rect, pm)

    def pixmap(self, size, mode, state):
        if self._data.icon:
            return self._data.icon.pixmap(size, mode, state)
        return QPixmap(size)

    def clone(self):
        return HmcIconEngine(self._data)


def HmcIcon(
    name: str,
    token: HmcTheme.Token = HmcTheme.Token.CONTENT_DEFAULT,
    theme: HmcTheme | None = None,
    parent: QWidget | None = None,
    **kwargs,
) -> QIcon:
    """Create a themed qtawesome icon.

    Pass ``parent`` to auto-update on theme change; without it the icon
    renders once with the provided theme.
    """
    data = HmcIconData(name, token, theme, parent, **kwargs)
    if parent:
        return QIcon(HmcIconEngine(data))
    else:
        return data.icon


def _HmcSvgIcon(
    content: str,
    size: int = 32,
    token: HmcTheme.Token = HmcTheme.Token.CONTENT_DEFAULT,
    theme: HmcTheme | None = None,
    parent: QWidget | None = None,
) -> QIcon:
    data = HmcSvgIconData(content, size, token, theme, parent)
    if parent:
        return QIcon(HmcIconEngine(data))
    else:
        return data.icon


def HmcSvgIcon(
    path: str | Path,
    size: int = 32,
    token: HmcTheme.Token = HmcTheme.Token.CONTENT_DEFAULT,
    theme: HmcTheme | None = None,
    parent: QWidget | None = None,
) -> QIcon:
    """Create a themed SVG icon.

    The SVG must use ``currentColor`` for fill/stroke.
    Pass ``parent`` to auto-update on theme change.
    """
    return _HmcSvgIcon(Path(path).read_text(), size, token, theme, parent)


def HmcLogoIcon(
    size: int = 32,
    token: HmcTheme.Token = HmcTheme.Token.CONTENT_DEFAULT,
    theme: HmcTheme | None = None,
    parent: QWidget | None = None,
) -> QIcon:
    """Create a themed ADI logo icon.

    Pass ``parent`` to auto-update on theme change.
    """
    return _HmcSvgIcon(_ADI_LOGO_SVG, size, token, theme, parent)
