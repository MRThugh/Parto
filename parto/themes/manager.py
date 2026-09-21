# parto/themes/manager.py
"""
Parto v0.3.0 - Centralized Theme Management System
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Dict, Optional, List
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from .palettes import THEME_PALETTES, get_theme_stylesheet
from ..resources.icons import clear_icon_cache


class ThemeManager(QObject):
    """
    Singleton ThemeManager coordinating theme selection, stylesheet generation,
    icon recoloring signals, and widget updates.
    """
    theme_changed = Signal(str)

    _instance: Optional[ThemeManager] = None

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_theme: str = "dark"

    @classmethod
    def instance(cls) -> ThemeManager:
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    @property
    def current_theme(self) -> str:
        return self._current_theme

    @property
    def current_theme_id(self) -> str:
        return self._current_theme

    def apply_to_application(self, app: Optional[QApplication] = None) -> None:
        self.set_theme(self._current_theme, app)

    def get_available_themes(self) -> List[str]:
        return list(THEME_PALETTES.keys())

    def get_palette(self, theme_key: Optional[str] = None) -> Dict[str, str]:
        key = theme_key or self._current_theme
        return THEME_PALETTES.get(key, THEME_PALETTES["dark"])

    def get_icon_color(self) -> str:
        return self.get_palette()["icon_color"]

    def get_canvas_bg(self) -> str:
        return self.get_palette()["canvas_bg"]

    def set_theme(self, theme_key: str, app: Optional[QApplication] = None) -> None:
        """
        Switch current theme, apply new stylesheet to application, and broadcast change.
        """
        if theme_key not in THEME_PALETTES:
            theme_key = "dark"

        self._current_theme = theme_key
        clear_icon_cache()

        stylesheet = get_theme_stylesheet(theme_key)
        target_app = app or QApplication.instance()
        if target_app is not None:
            target_app.setStyleSheet(stylesheet)

        self.theme_changed.emit(theme_key)


def get_theme_manager() -> ThemeManager:
    """Convenience accessor for ThemeManager singleton."""
    return ThemeManager.instance()
