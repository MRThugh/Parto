# parto/themes/palettes.py
"""
Parto v0.3.0 - Theme Palettes and Dynamic QSS Generator
Author: Ali Kamrani (MRThugh)
"""

from typing import Dict, Any

THEME_PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "name": "Dark",
        "bg": "#18181b",
        "surface": "#27272a",
        "surface_raised": "#3f3f46",
        "surface_sunken": "#141416",
        "border": "#3f3f46",
        "border_subtle": "#2e2e33",
        "border_focus": "#0284c7",
        "text": "#f4f4f5",
        "text_secondary": "#a1a1aa",
        "text_muted": "#71717a",
        "primary": "#0284c7",
        "primary_hover": "#0369a1",
        "primary_pressed": "#075985",
        "primary_text": "#ffffff",
        "accent": "#38bdf8",
        "danger": "#ef4444",
        "danger_hover": "#dc2626",
        "icon_color": "#e4e4e7",
        "icon_dim": "#a1a1aa",
        "canvas_bg": "#121214",
        "canvas_checker_1": "#1a1a1c",
        "canvas_checker_2": "#222226",
    },
    "light": {
        "name": "Light",
        "bg": "#f4f4f6",
        "surface": "#ffffff",
        "surface_raised": "#e4e4e8",
        "surface_sunken": "#ebebef",
        "border": "#d4d4d8",
        "border_subtle": "#e4e4e7",
        "border_focus": "#0284c7",
        "text": "#18181b",
        "text_secondary": "#52525b",
        "text_muted": "#71717a",
        "primary": "#0284c7",
        "primary_hover": "#0369a1",
        "primary_pressed": "#075985",
        "primary_text": "#ffffff",
        "accent": "#0ea5e9",
        "danger": "#ef4444",
        "danger_hover": "#dc2626",
        "icon_color": "#27272a",
        "icon_dim": "#71717a",
        "canvas_bg": "#e4e4e8",
        "canvas_checker_1": "#f4f4f6",
        "canvas_checker_2": "#e2e2e6",
    },
    "graphite": {
        "name": "Graphite",
        "bg": "#24272c",
        "surface": "#2d3139",
        "surface_raised": "#3a3f4a",
        "surface_sunken": "#1e2125",
        "border": "#434956",
        "border_subtle": "#353a44",
        "border_focus": "#3b82f6",
        "text": "#eef1f6",
        "text_secondary": "#a6b0c2",
        "text_muted": "#7a8599",
        "primary": "#3b82f6",
        "primary_hover": "#2563eb",
        "primary_pressed": "#1d4ed8",
        "primary_text": "#ffffff",
        "accent": "#60a5fa",
        "danger": "#f87171",
        "danger_hover": "#ef4444",
        "icon_color": "#dce3ee",
        "icon_dim": "#9aa5b8",
        "canvas_bg": "#1c1f24",
        "canvas_checker_1": "#25282e",
        "canvas_checker_2": "#2e323a",
    },
    "midnight": {
        "name": "Midnight",
        "bg": "#0b0f19",
        "surface": "#111827",
        "surface_raised": "#1f2937",
        "surface_sunken": "#080c14",
        "border": "#1e293b",
        "border_subtle": "#172033",
        "border_focus": "#6366f1",
        "text": "#f8fafc",
        "text_secondary": "#94a3b8",
        "text_muted": "#64748b",
        "primary": "#6366f1",
        "primary_hover": "#4f46e5",
        "primary_pressed": "#4338ca",
        "primary_text": "#ffffff",
        "accent": "#818cf8",
        "danger": "#f43f5e",
        "danger_hover": "#e11d48",
        "icon_color": "#e2e8f0",
        "icon_dim": "#94a3b8",
        "canvas_bg": "#070a12",
        "canvas_checker_1": "#0d1322",
        "canvas_checker_2": "#131b2e",
    },
    "nord": {
        "name": "Nord",
        "bg": "#2e3440",
        "surface": "#3b4252",
        "surface_raised": "#434c5e",
        "surface_sunken": "#242933",
        "border": "#4c566a",
        "border_subtle": "#3b4252",
        "border_focus": "#88c0d0",
        "text": "#eceff4",
        "text_secondary": "#d8dee9",
        "text_muted": "#4c566a",
        "primary": "#88c0d0",
        "primary_hover": "#81a1c1",
        "primary_pressed": "#5e81ac",
        "primary_text": "#2e3440",
        "accent": "#8fbcbb",
        "danger": "#bf616a",
        "danger_hover": "#d08770",
        "icon_color": "#eceff4",
        "icon_dim": "#d8dee9",
        "canvas_bg": "#242933",
        "canvas_checker_1": "#2e3440",
        "canvas_checker_2": "#3b4252",
    },
}


def get_theme_stylesheet(theme_key: str = "dark") -> str:
    """
    Generate a complete, modern Qt stylesheet tailored to the selected theme palette.
    """
    p = THEME_PALETTES.get(theme_key, THEME_PALETTES["dark"])

    return f"""
    /* === BASE WINDOW & DIALOGS === */
    QMainWindow, QDialog, QWidget {{
        background-color: {p["bg"]};
        color: {p["text"]};
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
    }}

    /* === MENU BAR & MENUS === */
    QMenuBar {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border-bottom: 1px solid {p["border"]};
        padding: 2px 4px;
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 5px 10px;
        border-radius: 4px;
        margin: 1px;
    }}
    QMenuBar::item:selected {{
        background-color: {p["surface_raised"]};
        color: {p["text"]};
    }}
    QMenuBar::item:pressed {{
        background-color: {p["primary"]};
        color: {p["primary_text"]};
    }}
    QMenu {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        border-radius: 6px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 24px 6px 12px;
        border-radius: 4px;
        margin: 1px;
    }}
    QMenu::item:selected {{
        background-color: {p["primary"]};
        color: {p["primary_text"]};
    }}
    QMenu::item:disabled {{
        color: {p["text_muted"]};
        background-color: transparent;
    }}
    QMenu::separator {{
        height: 1px;
        background-color: {p["border"]};
        margin: 4px 8px;
    }}

    /* === TOOLBAR === */
    QToolBar {{
        background-color: {p["surface"]};
        border-bottom: 1px solid {p["border"]};
        padding: 3px 6px;
        spacing: 3px;
    }}
    QToolBar::separator {{
        width: 1px;
        background-color: {p["border"]};
        margin: 4px 6px;
    }}
    QToolButton {{
        background-color: transparent;
        color: {p["text"]};
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 4px;
        margin: 1px;
    }}
    QToolButton:hover {{
        background-color: {p["surface_raised"]};
        border: 1px solid {p["border"]};
    }}
    QToolButton:pressed, QToolButton:checked {{
        background-color: {p["primary"]};
        color: {p["primary_text"]};
        border: 1px solid {p["primary_hover"]};
    }}
    QToolButton:disabled {{
        opacity: 0.4;
    }}

    /* === STATUS BAR === */
    QStatusBar {{
        background-color: {p["surface"]};
        color: {p["text_secondary"]};
        border-top: 1px solid {p["border"]};
        min-height: 24px;
        padding: 0 4px;
    }}
    QStatusBar::item {{
        border: none;
        padding: 0 4px;
    }}
    QStatusBar QLabel {{
        color: {p["text_secondary"]};
        font-size: 11px;
    }}

    /* === BUTTONS === */
    QPushButton {{
        background-color: {p["surface_raised"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        border-radius: 5px;
        padding: 5px 14px;
        font-weight: 500;
        min-height: 20px;
    }}
    QPushButton:hover {{
        background-color: {p["border"]};
        border-color: {p["border_focus"]};
    }}
    QPushButton:pressed {{
        background-color: {p["primary"]};
        color: {p["primary_text"]};
        border-color: {p["primary_hover"]};
    }}
    QPushButton:disabled {{
        background-color: {p["surface_sunken"]};
        color: {p["text_muted"]};
        border-color: {p["border_subtle"]};
    }}
    QPushButton#PrimaryAction {{
        background-color: {p["primary"]};
        color: {p["primary_text"]};
        border: 1px solid {p["primary_hover"]};
    }}
    QPushButton#PrimaryAction:hover {{
        background-color: {p["primary_hover"]};
    }}
    QPushButton#PrimaryAction:pressed {{
        background-color: {p["primary_pressed"]};
    }}
    QPushButton#DangerAction {{
        background-color: {p["danger"]};
        color: #ffffff;
        border: 1px solid {p["danger_hover"]};
    }}
    QPushButton#DangerAction:hover {{
        background-color: {p["danger_hover"]};
    }}

    /* === INPUTS & CONTROLS === */
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        border-radius: 4px;
        padding: 4px 8px;
        selection-background-color: {p["primary"]};
        selection-color: {p["primary_text"]};
    }}
    QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
        border: 1px solid {p["border_focus"]};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 18px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        selection-background-color: {p["primary"]};
        selection-color: {p["primary_text"]};
        padding: 4px;
        border-radius: 4px;
    }}

    /* === SLIDERS === */
    QSlider::groove:horizontal {{
        height: 4px;
        background: {p["border"]};
        border-radius: 2px;
    }}
    QSlider::sub-page:horizontal {{
        background: {p["primary"]};
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        background: {p["accent"]};
        width: 14px;
        margin: -5px 0;
        border-radius: 7px;
        border: 1px solid {p["surface"]};
    }}
    QSlider::handle:horizontal:hover {{
        background: {p["text"]};
        border: 1px solid {p["primary"]};
    }}

    /* === DOCK WIDGETS === */
    QDockWidget {{
        color: {p["text"]};
        titlebar-close-icon: url(none);
        titlebar-normal-icon: url(none);
    }}
    QDockWidget::title {{
        background-color: {p["surface"]};
        border-bottom: 1px solid {p["border"]};
        padding: 6px 8px;
        font-weight: 600;
        font-size: 12px;
    }}

    /* === SCROLL BARS === */
    QScrollBar:vertical {{
        background-color: {p["bg"]};
        width: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {p["surface_raised"]};
        min-height: 20px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {p["border"]};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background-color: {p["bg"]};
        height: 10px;
        margin: 0px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {p["surface_raised"]};
        min-width: 20px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {p["border"]};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* === LISTS & TABLES === */
    QListWidget, QListView, QTableView {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        border-radius: 5px;
        outline: none;
        padding: 2px;
    }}
    QListWidget::item {{
        padding: 5px 8px;
        border-radius: 4px;
        margin: 1px;
    }}
    QListWidget::item:selected {{
        background-color: {p["surface_raised"]};
        color: {p["text"]};
        border: 1px solid {p["border_focus"]};
    }}
    QListWidget::item:hover {{
        background-color: {p["surface_sunken"]};
    }}

    /* === TOAST WIDGET === */
    QWidget#ToastWidget {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        padding: 10px 18px;
    }}

    /* === CROP BAR === */
    QWidget#CropBar {{
        background-color: {p["surface"]};
        border: 1px solid {p["border"]};
        border-radius: 8px;
        padding: 4px 10px;
    }}
    QWidget#CropBar QLabel {{
        color: {p["text"]};
        font-weight: 500;
    }}

    /* === TOOLTIPS === */
    QToolTip {{
        background-color: {p["surface"]};
        color: {p["text"]};
        border: 1px solid {p["border"]};
        border-radius: 4px;
        padding: 4px 8px;
        font-size: 11px;
    }}

    /* === GROUP BOX === */
    QGroupBox {{
        font-weight: 600;
        border: 1px solid {p["border"]};
        border-radius: 6px;
        margin-top: 12px;
        padding-top: 14px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        left: 10px;
        padding: 0 4px;
        color: {p["text_secondary"]};
    }}
    """


THEMES = THEME_PALETTES

