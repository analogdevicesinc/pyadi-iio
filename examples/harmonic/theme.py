# Copyright (C) 2026 Analog Devices, Inc.
#
# SPDX short identifier: ADIBSD

"""Harmonic Design System theme for PySide6 — light and dark mode.

``HmcTheme`` is a dataclass holding all semantic color tokens.
Use ``theme.styleSheet()`` to get a resolved QSS stylesheet string.

Usage::

    from adi.harmonic.theme import HmcTheme
    app.setStyleSheet(HmcTheme.default.styleSheet())
"""

from dataclasses import dataclass, field
from enum import Enum

from harmonic.colors import (
    BLUE,
    CATEGORICAL_DARK,
    CATEGORICAL_LIGHT,
    FONT_FAMILY_BODY,
    FONT_FAMILY_HEADING,
    GRAY,
    GREEN,
    ORANGE,
    PURPLE,
    RED,
)


@dataclass
class HmcTheme:
    """Resolved semantic tokens for one mode (light or dark)."""

    class Token(str, Enum):
        """Attribute names for HmcTheme semantic color tokens."""

        # System
        PRIMARY = "primary"
        PRIMARY_HOVER = "primary_hover"
        PRIMARY_WEAK = "primary_weak"
        PRIMARY_WEAKEST = "primary_weakest"

        DANGER = "danger"
        DANGER_HOVER = "danger_hover"
        DANGER_WEAKEST = "danger_weakest"

        WARNING = "warning"
        WARNING_HOVER = "warning_hover"
        WARNING_WEAKEST = "warning_weakest"

        SUCCESS = "success"
        SUCCESS_HOVER = "success_hover"
        SUCCESS_WEAKEST = "success_weakest"

        HIGHLIGHT = "highlight"
        HIGHLIGHT_WEAKEST = "highlight_weakest"

        # Content
        CONTENT_DEFAULT = "content_default"
        CONTENT_MEDIUM = "content_medium"
        CONTENT_WEAK = "content_weak"
        CONTENT_INVERSE = "content_inverse"

        # Layout
        LAYOUT_CANVAS = "layout_canvas"
        LAYOUT_CONTAINER = "layout_container"
        LAYOUT_DIVIDER = "layout_divider"
        LAYOUT_DIVIDER_WEAK = "layout_divider_weak"

        # Inputs
        INPUT_BORDER_IDLE = "input_border_idle"
        INPUT_BORDER_HOVER = "input_border_hover"
        INPUT_BORDER_FOCUS = "input_border_focus"
        INPUT_BORDER_DISABLED = "input_border_disabled"
        INPUT_BORDER_ERROR = "input_border_error"
        INPUT_BORDER_WARNING = "input_border_warning"

        # Actions
        ACTION_STRONG_BG = "action_strong_bg"
        ACTION_STRONG_BG_HOVER = "action_strong_bg_hover"
        ACTION_STRONG_CONTENT = "action_strong_content"

        ACTION_MEDIUM_BORDER = "action_medium_border"
        ACTION_MEDIUM_BORDER_HOVER = "action_medium_border_hover"
        ACTION_MEDIUM_CONTENT = "action_medium_content"
        ACTION_MEDIUM_CONTENT_HOVER = "action_medium_content_hover"

        ACTION_WEAK_BORDER = "action_weak_border"
        ACTION_WEAK_BORDER_HOVER = "action_weak_border_hover"
        ACTION_WEAK_CONTENT = "action_weak_content"

        # Selection controls
        SELECTION_UNSELECTED_BORDER = "selection_unselected_border"
        SELECTION_UNSELECTED_BORDER_HOVER = "selection_unselected_border_hover"
        SELECTION_UNSELECTED_BORDER_DISABLED = "selection_unselected_border_disabled"
        SELECTION_UNSELECTED_BG = "selection_unselected_bg"
        SELECTION_UNSELECTED_BG_HOVER = "selection_unselected_bg_hover"
        SELECTION_UNSELECTED_BG_DISABLED = "selection_unselected_bg_disabled"
        SELECTION_UNSELECTED_CONTENT = "selection_unselected_content"
        SELECTION_SELECTED_BG = "selection_selected_bg"
        SELECTION_SELECTED_BG_HOVER = "selection_selected_bg_hover"
        SELECTION_SELECTED_BG_DISABLED = "selection_selected_bg_disabled"
        SELECTION_SELECTED_CONTENT = "selection_selected_content"

        # Progress
        PROGRESS_TRACK = "progress_track"
        PROGRESS_CONTENT = "progress_content"
        PROGRESS_SUCCESS = "progress_success"
        PROGRESS_DANGER = "progress_danger"

        # Tooltip
        TOOLTIP_BG = "tooltip_bg"
        TOOLTIP_TEXT = "tooltip_text"

        # Convenience palette refs
        BUTTON_PRESSED = "button_pressed"
        BUTTON_DISABLED_BG = "button_disabled_bg"
        GHOST_HOVER = "ghost_hover"
        TERTIARY_HOVER_BG = "tertiary_hover_bg"
        NAV_CHECKED_BG = "nav_checked_bg"
        INPUT_DISABLED_BG = "input_disabled_bg"
        TAB_HOVER_BG = "tab_hover_bg"
        SCROLLBAR_HANDLE = "scrollbar_handle"
        SCROLLBAR_HANDLE_HOVER = "scrollbar_handle_hover"

    class ButtonClass(str, Enum):
        """QPushButton ``class`` property values styled by the theme."""

        SECONDARY = "secondary"
        TERTIARY = "tertiary"
        GHOST = "ghost"
        DANGER = "danger"

    name: str

    # System
    primary: str
    primary_hover: str
    primary_weak: str
    primary_weakest: str

    danger: str
    danger_hover: str
    danger_weakest: str

    warning: str
    warning_hover: str
    warning_weakest: str

    success: str
    success_hover: str
    success_weakest: str

    highlight: str
    highlight_weakest: str

    # Content
    content_default: str
    content_medium: str
    content_weak: str
    content_inverse: str

    # Layout
    layout_canvas: str
    layout_container: str
    layout_divider: str
    layout_divider_weak: str

    # Inputs
    input_border_idle: str
    input_border_hover: str
    input_border_focus: str
    input_border_disabled: str
    input_border_error: str
    input_border_warning: str

    # Actions
    action_strong_bg: str
    action_strong_bg_hover: str
    action_strong_content: str

    action_medium_border: str
    action_medium_border_hover: str
    action_medium_content: str
    action_medium_content_hover: str

    action_weak_border: str
    action_weak_border_hover: str
    action_weak_content: str

    # Selection controls (checkbox, radio, toggle)
    selection_unselected_border: str = ""
    selection_unselected_border_hover: str = ""
    selection_unselected_border_disabled: str = ""
    selection_unselected_bg: str = ""
    selection_unselected_bg_hover: str = ""
    selection_unselected_bg_disabled: str = ""
    selection_unselected_content: str = ""
    selection_selected_bg: str = ""
    selection_selected_bg_hover: str = ""
    selection_selected_bg_disabled: str = ""
    selection_selected_content: str = ""

    # Progress
    progress_track: str = ""
    progress_content: str = ""
    progress_success: str = ""
    progress_danger: str = ""

    # Tooltip
    tooltip_bg: str = ""
    tooltip_text: str = ""

    # Convenience: extra palette refs used by QSS
    button_pressed: str = ""
    button_disabled_bg: str = ""
    ghost_hover: str = ""
    tertiary_hover_bg: str = ""
    nav_checked_bg: str = ""
    input_disabled_bg: str = ""
    tab_hover_bg: str = ""
    scrollbar_handle: str = ""
    scrollbar_handle_hover: str = ""

    # Data viz
    categorical: list = field(default_factory=list)

    def styleSheet(self) -> str:
        t = self
        return f"""
/* ===================================================================
   Harmonic Design System — PySide6 Stylesheet ({t.name})
   =================================================================== */

/* --- Global defaults ----------------------------------------------- */

* {{
    font-family: '{FONT_FAMILY_BODY}', sans-serif;
    font-size: 14px;
    color: {t.content_default};
}}

/* --- QMainWindow / top-level -------------------------------------- */

QMainWindow {{
    background-color: {t.layout_canvas};
}}

/* --- QPushButton -------------------------------------------------- */

QPushButton {{
    background-color: {t.action_strong_bg};
    color: {t.action_strong_content};
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 32px;
}}
QPushButton:hover  {{ background-color: {t.action_strong_bg_hover}; }}
QPushButton:pressed {{ background-color: {t.button_pressed}; }}
QPushButton:disabled {{
    background-color: {t.button_disabled_bg};
    color: {t.content_inverse};
}}

/* secondary variant — use setProperty("class", "secondary") */
QPushButton[class="secondary"] {{
    background-color: transparent;
    border: 1px solid {t.action_medium_border};
    color: {t.action_medium_content};
}}
QPushButton[class="secondary"]:hover {{
    border-color: {t.action_medium_border_hover};
    color: {t.action_medium_content_hover};
    background-color: {t.primary_weakest};
}}

/* tertiary variant */
QPushButton[class="tertiary"] {{
    background-color: transparent;
    border: 1px solid {t.action_weak_border};
    color: {t.action_weak_content};
}}
QPushButton[class="tertiary"]:hover {{
    border-color: {t.action_weak_border_hover};
    background-color: {t.tertiary_hover_bg};
}}

/* ghost variant */
QPushButton[class="ghost"] {{
    background-color: transparent;
    border: none;
    color: {t.content_default};
}}
QPushButton[class="ghost"]:hover {{
    background-color: {t.ghost_hover};
}}

/* danger variant */
QPushButton[class="danger"] {{
    background-color: {t.danger};
    color: {t.content_inverse};
    border: none;
}}
QPushButton[class="danger"]:hover {{
    background-color: {t.danger_hover};
}}

/* icon-only nav button */
QPushButton[class="nav"] {{
    background-color: transparent;
    border: none;
    border-radius: 4px;
    padding: 8px;
    min-height: 40px;
    min-width: 40px;
}}
QPushButton[class="nav"]:hover {{
    background-color: {t.ghost_hover};
}}
QPushButton[class="nav"]:checked {{
    background-color: {t.nav_checked_bg};
}}

/* --- QLineEdit / QSpinBox / QDoubleSpinBox ------------------------ */

QLineEdit, QSpinBox, QDoubleSpinBox {{
    border: 1px solid {t.input_border_idle};
    border-radius: 4px;
    padding: 6px 12px;
    background-color: {t.layout_container};
    color: {t.content_default};
    selection-background-color: {t.primary};
    selection-color: {t.content_inverse};
    min-height: 20px;
}}
QLineEdit:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {t.input_border_hover};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {t.primary};
    border-width: 2px;
    padding: 5px 11px;
}}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    background-color: {t.input_disabled_bg};
    color: {t.content_weak};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    width: 20px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 20px;
}}

/* --- QComboBox ---------------------------------------------------- */

QComboBox {{
    border: 1px solid {t.input_border_idle};
    border-radius: 4px;
    padding: 6px 12px;
    background-color: {t.layout_container};
    color: {t.content_default};
    min-height: 20px;
}}
QComboBox:hover {{ border-color: {t.input_border_hover}; }}
QComboBox:focus {{ border-color: {t.primary}; }}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {t.layout_divider};
    border-radius: 4px;
    background-color: {t.layout_container};
    color: {t.content_default};
    selection-background-color: {t.primary_weakest};
    selection-color: {t.content_default};
    padding: 4px;
}}

/* --- QLabel ------------------------------------------------------- */

QLabel {{
    background: transparent;
    border: none;
    padding: 0;
}}
QLabel[class="heading"] {{
    font-family: '{FONT_FAMILY_HEADING}', sans-serif;
    font-size: 18px;
    font-weight: 600;
    color: {t.content_default};
}}
QLabel[class="subheading"] {{
    font-family: '{FONT_FAMILY_HEADING}', sans-serif;
    font-size: 14px;
    font-weight: 600;
    color: {t.content_medium};
}}
QLabel[class="caption"] {{
    font-size: 12px;
    color: {t.content_weak};
}}
QLabel[class="kpi-value"] {{
    font-family: '{FONT_FAMILY_HEADING}', sans-serif;
    font-size: 28px;
    font-weight: 700;
    color: {t.content_default};
}}

/* --- QFrame (card) ------------------------------------------------ */

QFrame[class="card"] {{
    background-color: {t.layout_container};
    border: 1px solid {t.layout_divider_weak};
    border-radius: 8px;
}}

/* --- QTabWidget / QTabBar ----------------------------------------- */

QTabWidget::pane {{
    border: none;
    background-color: {t.layout_canvas};
}}
QTabBar {{
    background-color: {t.layout_container};
    border-bottom: 1px solid {t.layout_divider_weak};
}}
QTabBar::tab {{
    padding: 10px 20px;
    border: none;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: {t.content_medium};
    font-weight: 500;
}}
QTabBar::tab:hover {{
    color: {t.content_default};
    background-color: {t.tab_hover_bg};
}}
QTabBar::tab:selected {{
    color: {t.primary};
    border-bottom: 2px solid {t.primary};
}}

/* vertical (west) tab bar — set class="vertical" on the QTabBar */
QTabBar[class="vertical"]  {{
    border-bottom: none;
    border-right: 1px solid {t.layout_divider_weak};
}}
QTabBar[class="vertical"]::tab {{
    border-bottom: none;
    border-right: 2px solid transparent;
}}
QTabBar[class="vertical"]::tab:selected {{
    border-bottom: none;
    border-right: 2px solid {t.primary};
}}

/* --- QGroupBox ---------------------------------------------------- */

QGroupBox {{
    font-family: '{FONT_FAMILY_HEADING}', sans-serif;
    font-weight: 600;
    font-size: 14px;
    border: 1px solid {t.layout_divider_weak};
    border-radius: 8px;
    margin-top: 12px;
    padding: 20px 16px 16px 16px;
    background-color: {t.layout_container};
    color: {t.content_default};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 8px;
    color: {t.content_default};
}}

/* --- QStatusBar --------------------------------------------------- */

QStatusBar {{
    background-color: {t.layout_container};
    border-top: 1px solid {t.layout_divider_weak};
    color: {t.content_medium};
    font-size: 12px;
    padding: 4px 12px;
}}

/* --- QToolBar ----------------------------------------------------- */

QToolBar {{
    background-color: {t.layout_container};
    border-bottom: 1px solid {t.layout_divider_weak};
    spacing: 8px;
    padding: 4px 12px;
}}
QToolBar::separator {{
    width: 1px;
    background-color: {t.layout_divider_weak};
    margin: 4px 8px;
}}

/* --- QScrollBar --------------------------------------------------- */

QScrollBar:vertical {{
    background: {t.layout_canvas};
    width: 8px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.scrollbar_handle};
    min-height: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical:hover {{
    background: {t.scrollbar_handle_hover};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {t.layout_canvas};
    height: 8px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {t.scrollbar_handle};
    min-width: 24px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {t.scrollbar_handle_hover};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* --- Badge helpers (via object names) ----------------------------- */

QLabel#badge-success {{
    background-color: {t.success_weakest};
    color: {t.success};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}}
QLabel#badge-danger {{
    background-color: {t.danger_weakest};
    color: {t.danger};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}}
QLabel#badge-warning {{
    background-color: {t.warning_weakest};
    color: {t.warning};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}}
QLabel#badge-info {{
    background-color: {t.primary_weakest};
    color: {t.primary};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}}
QLabel#badge-highlight {{
    background-color: {t.highlight};
    color: {t.content_inverse};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 12px;
    font-weight: 600;
}}

/* --- QCheckBox ---------------------------------------------------- */

QCheckBox {{
    spacing: 8px;
    color: {t.content_default};
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {t.selection_unselected_border};
    border-radius: 4px;
    background-color: {t.layout_container};
}}
QCheckBox::indicator:hover {{
    border-color: {t.selection_unselected_border_hover};
}}
QCheckBox::indicator:checked {{
    background-color: {t.selection_selected_bg};
    border-color: {t.selection_selected_bg};
    image: none;
}}
QCheckBox::indicator:checked:hover {{
    background-color: {t.selection_selected_bg_hover};
    border-color: {t.selection_selected_bg_hover};
}}
QCheckBox::indicator:disabled {{
    border-color: {t.selection_unselected_border_disabled};
    background-color: {t.layout_container};
}}
QCheckBox::indicator:checked:disabled {{
    background-color: {t.selection_selected_bg_disabled};
    border-color: {t.selection_selected_bg_disabled};
}}
QCheckBox:disabled {{
    color: {t.content_weak};
}}

/* toggle-switch variant — use setProperty("class", "toggle") */
QCheckBox[class="toggle"] {{
    spacing: 8px;
}}
QCheckBox[class="toggle"]::indicator {{
    width: 35px;
    height: 16px;
    border-radius: 8px;
    border: none;
    background-color: {t.selection_unselected_bg};
}}
QCheckBox[class="toggle"]::indicator:hover {{
    background-color: {t.selection_unselected_bg_hover};
}}
QCheckBox[class="toggle"]::indicator:checked {{
    background-color: {t.selection_selected_bg};
}}
QCheckBox[class="toggle"]::indicator:checked:hover {{
    background-color: {t.selection_selected_bg_hover};
}}
QCheckBox[class="toggle"]::indicator:disabled {{
    background-color: {t.selection_unselected_bg_disabled};
}}
QCheckBox[class="toggle"]::indicator:checked:disabled {{
    background-color: {t.selection_selected_bg_disabled};
}}

/* --- QRadioButton ------------------------------------------------- */

QRadioButton {{
    spacing: 8px;
    color: {t.content_default};
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {t.selection_unselected_border};
    border-radius: 8px;
    background-color: {t.layout_container};
}}
QRadioButton::indicator:hover {{
    border-color: {t.selection_unselected_border_hover};
}}
QRadioButton::indicator:checked {{
    background-color: {t.selection_selected_bg};
    border-color: {t.selection_selected_bg};
}}
QRadioButton::indicator:checked:hover {{
    background-color: {t.selection_selected_bg_hover};
    border-color: {t.selection_selected_bg_hover};
}}
QRadioButton::indicator:disabled {{
    border-color: {t.selection_unselected_border_disabled};
    background-color: {t.layout_container};
}}
QRadioButton::indicator:checked:disabled {{
    background-color: {t.selection_selected_bg_disabled};
    border-color: {t.selection_selected_bg_disabled};
}}
QRadioButton:disabled {{
    color: {t.content_weak};
}}

/* --- QTextEdit / QPlainTextEdit ----------------------------------- */

QTextEdit, QPlainTextEdit {{
    border: 1px solid {t.input_border_idle};
    border-radius: 4px;
    padding: 6px 12px;
    background-color: {t.layout_container};
    color: {t.content_default};
    selection-background-color: {t.primary};
    selection-color: {t.content_inverse};
}}
QTextEdit:hover, QPlainTextEdit:hover {{
    border-color: {t.input_border_hover};
}}
QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {t.primary};
    border-width: 2px;
    padding: 5px 11px;
}}
QTextEdit:disabled, QPlainTextEdit:disabled {{
    background-color: {t.input_disabled_bg};
    color: {t.content_weak};
}}

/* --- QProgressBar ------------------------------------------------- */

QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {t.progress_track};
    height: 8px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    border-radius: 4px;
    background-color: {t.progress_content};
}}
QProgressBar[class="success"]::chunk {{
    background-color: {t.progress_success};
}}
QProgressBar[class="danger"]::chunk {{
    background-color: {t.progress_danger};
}}

/* --- QSlider ------------------------------------------------------ */

QSlider:horizontal {{
    min-height: 24px;
}}
QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {t.progress_track};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {t.primary};
    width: 16px;
    height: 16px;
    margin: -7px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{
    background: {t.primary_hover};
}}
QSlider::handle:horizontal:disabled {{
    background: {t.input_border_disabled};
}}
QSlider::groove:horizontal:disabled {{
    background: {t.layout_divider_weak};
}}
QSlider::sub-page:horizontal {{
    background: {t.primary};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal:disabled {{
    background: {t.input_border_disabled};
}}

QSlider:vertical {{
    min-width: 24px;
}}
QSlider::groove:vertical {{
    border: none;
    width: 4px;
    background: {t.progress_track};
    border-radius: 2px;
}}
QSlider::handle:vertical {{
    background: {t.primary};
    width: 16px;
    height: 16px;
    margin: 0 -7px;
    border-radius: 8px;
}}
QSlider::handle:vertical:hover {{
    background: {t.primary_hover};
}}
QSlider::handle:vertical:disabled {{
    background: {t.input_border_disabled};
}}
QSlider::groove:vertical:disabled {{
    background: {t.layout_divider_weak};
}}
QSlider::sub-page:vertical {{
    background: {t.primary};
    border-radius: 2px;
}}
QSlider::sub-page:vertical:disabled {{
    background: {t.input_border_disabled};
}}

/* --- QToolTip ----------------------------------------------------- */

QToolTip {{
    background-color: {t.tooltip_bg};
    color: {t.tooltip_text};
    border: 1px solid {t.layout_divider};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}

/* --- QDialog ------------------------------------------------------ */

QDialog {{
    background-color: {t.layout_container};
    border: 1px solid {t.layout_divider_weak};
    border-radius: 8px;
}}

/* --- App-level layout helpers ------------------------------------- */

QFrame[class="sidebar"] {{
    background-color: {t.layout_container};
    border-right: 1px solid {t.layout_divider_weak};
}}

QFrame[class="header"] {{
    background-color: {t.layout_container};
    border-bottom: 1px solid {t.layout_divider_weak};
}}

QPushButton[class="theme-toggle"] {{
    font-size: 20px;
    color: {t.content_medium};
    background-color: transparent;
    border: none;
}}
QPushButton[class="theme-toggle"]:hover {{
    background-color: {t.ghost_hover};
}}
"""


# ---------------------------------------------------------------------------
# Light theme  (from global.css — the default)
# ---------------------------------------------------------------------------

HmcTheme.LIGHT = HmcTheme(
    name="light",
    primary=BLUE["700"],
    primary_hover=BLUE["900"],
    primary_weak=BLUE["500"],
    primary_weakest=BLUE["100"],
    danger=RED["700"],
    danger_hover=RED["900"],
    danger_weakest=RED["100"],
    warning=ORANGE["500"],
    warning_hover=ORANGE["700"],
    warning_weakest=ORANGE["100"],
    success=GREEN["500"],
    success_hover=GREEN["700"],
    success_weakest=GREEN["100"],
    highlight=PURPLE["500"],
    highlight_weakest=PURPLE["100"],
    content_default=GRAY["black"],
    content_medium=GRAY["700"],
    content_weak=GRAY["500"],
    content_inverse=GRAY["white"],
    layout_canvas=GRAY["100"],
    layout_container=GRAY["white"],
    layout_divider=GRAY["300"],
    layout_divider_weak=GRAY["200"],
    input_border_idle=GRAY["500"],
    input_border_hover=GRAY["700"],
    input_border_focus=BLUE["700"],
    input_border_disabled=GRAY["400"],
    input_border_error=RED["700"],
    input_border_warning=ORANGE["700"],
    action_strong_bg=BLUE["700"],
    action_strong_bg_hover=BLUE["900"],
    action_strong_content=GRAY["white"],
    action_medium_border=BLUE["700"],
    action_medium_border_hover=BLUE["900"],
    action_medium_content=BLUE["700"],
    action_medium_content_hover=BLUE["900"],
    action_weak_border=GRAY["500"],
    action_weak_border_hover=GRAY["700"],
    action_weak_content=GRAY["black"],
    categorical=CATEGORICAL_LIGHT,
    selection_unselected_border=GRAY["500"],
    selection_unselected_border_hover=GRAY["700"],
    selection_unselected_border_disabled=GRAY["400"],
    selection_unselected_bg=GRAY["500"],
    selection_unselected_bg_hover=GRAY["700"],
    selection_unselected_bg_disabled=GRAY["400"],
    selection_unselected_content=GRAY["white"],
    selection_selected_bg=BLUE["700"],
    selection_selected_bg_hover=BLUE["900"],
    selection_selected_bg_disabled=BLUE["300"],
    selection_selected_content=GRAY["white"],
    progress_track=GRAY["300"],
    progress_content=BLUE["700"],
    progress_success=GREEN["500"],
    progress_danger=RED["700"],
    tooltip_bg=GRAY["1000"],
    tooltip_text=GRAY["white"],
    button_pressed=BLUE["1000"],
    button_disabled_bg=BLUE["300"],
    ghost_hover=GRAY["200"],
    tertiary_hover_bg=GRAY["100"],
    nav_checked_bg=BLUE["100"],
    input_disabled_bg=GRAY["100"],
    tab_hover_bg=GRAY["100"],
    scrollbar_handle=GRAY["300"],
    scrollbar_handle_hover=GRAY["400"],
)

# ---------------------------------------------------------------------------
# Dark theme  (from color-tokens-dark.json)
# ---------------------------------------------------------------------------

HmcTheme.DARK = HmcTheme(
    name="dark",
    primary=BLUE["300"],
    primary_hover=BLUE["100"],
    primary_weak=BLUE["500"],
    primary_weakest=BLUE["1000"],
    danger=RED["300"],
    danger_hover=RED["100"],
    danger_weakest=RED["900"],
    warning=ORANGE["500"],
    warning_hover=ORANGE["300"],
    warning_weakest=ORANGE["900"],
    success=GREEN["500"],
    success_hover=GREEN["300"],
    success_weakest=GREEN["900"],
    highlight=PURPLE["500"],
    highlight_weakest=PURPLE["900"],
    content_default=GRAY["white"],
    content_medium=GRAY["300"],
    content_weak=GRAY["500"],
    content_inverse=GRAY["black"],
    layout_canvas=GRAY["black"],
    layout_container=GRAY["1000"],
    layout_divider=GRAY["800"],
    layout_divider_weak=GRAY["900"],
    input_border_idle=GRAY["500"],
    input_border_hover=GRAY["300"],
    input_border_focus=BLUE["300"],
    input_border_disabled=GRAY["700"],
    input_border_error=RED["300"],
    input_border_warning=ORANGE["300"],
    action_strong_bg=BLUE["300"],
    action_strong_bg_hover=BLUE["100"],
    action_strong_content=GRAY["black"],
    action_medium_border=BLUE["300"],
    action_medium_border_hover=BLUE["100"],
    action_medium_content=BLUE["300"],
    action_medium_content_hover=BLUE["100"],
    action_weak_border=GRAY["500"],
    action_weak_border_hover=GRAY["300"],
    action_weak_content=GRAY["white"],
    categorical=CATEGORICAL_DARK,
    selection_unselected_border=GRAY["500"],
    selection_unselected_border_hover=GRAY["300"],
    selection_unselected_border_disabled=GRAY["700"],
    selection_unselected_bg=GRAY["500"],
    selection_unselected_bg_hover=GRAY["300"],
    selection_unselected_bg_disabled=GRAY["700"],
    selection_unselected_content=GRAY["white"],
    selection_selected_bg=BLUE["300"],
    selection_selected_bg_hover=BLUE["100"],
    selection_selected_bg_disabled=BLUE["900"],
    selection_selected_content=GRAY["black"],
    progress_track=GRAY["700"],
    progress_content=BLUE["300"],
    progress_success=GREEN["500"],
    progress_danger=RED["300"],
    tooltip_bg=GRAY["100"],
    tooltip_text=GRAY["black"],
    button_pressed=BLUE["500"],
    button_disabled_bg=BLUE["900"],
    ghost_hover=GRAY["800"],
    tertiary_hover_bg=GRAY["900"],
    nav_checked_bg=BLUE["1000"],
    input_disabled_bg=GRAY["900"],
    tab_hover_bg=GRAY["900"],
    scrollbar_handle=GRAY["700"],
    scrollbar_handle_hover=GRAY["600"],
)

HmcTheme.default = HmcTheme.LIGHT
