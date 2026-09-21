# parto/themes/manager.py
"""
Parto v0.3.0 - Centralized Theme Management System
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Dict, Optional, List, Any
from PySide6.QtCore import QObject, Signal, QPropertyAnimation, QEasingCurve, Qt
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QGraphicsOpacityEffect

from .palettes import THEME_PALETTES, get_theme_stylesheet, get_semantic_color
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

    def get_semantic_color(self, key: str, default: str = "#ffffff") -> str:
        return get_semantic_color(self.get_palette(), key, default)

    def get_color(self, key: str, default: str = "#ffffff") -> str:
        return self.get_semantic_color(key, default)

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

    def transition_theme(
        self,
        theme_key: str,
        window: Optional[QWidget] = None,
        duration_ms: int = 200,
        app: Optional[QApplication] = None,
    ) -> None:
        """
        Transition between themes with a 150-250ms crossfade animation.
        Captures the visual state of the window, applies the new theme immediately,
        and smoothly fades out the overlay.
        """
        if window is None or not window.isVisible():
            self.set_theme(theme_key, app)
            return

        try:
            # Capture current window appearance
            pixmap = window.grab()

            # Create overlay matching window rect
            overlay = QLabel(window)
            overlay.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            overlay.setPixmap(pixmap)
            overlay.setGeometry(window.rect())
            overlay.show()
            overlay.raise_()

            # Apply new theme immediately underneath overlay
            self.set_theme(theme_key, app)

            # Crossfade overlay to reveal new theme smoothly
            effect = QGraphicsOpacityEffect(overlay)
            overlay.setGraphicsEffect(effect)

            anim = QPropertyAnimation(effect, b"opacity", overlay)
            anim.setDuration(max(100, min(500, duration_ms)))
            anim.setStartValue(1.0)
            anim.setEndValue(0.0)
            anim.setEasingCurve(QEasingCurve.InOutQuad)

            def _cleanup():
                overlay.deleteLater()

            anim.finished.connect(_cleanup)
            overlay._theme_anim = anim
            anim.start()
        except Exception:
            # Fallback to direct theme setting if graphical grab/animation is unsupported
            self.set_theme(theme_key, app)


def get_theme_manager() -> ThemeManager:
    """Convenience accessor for ThemeManager singleton."""
    return ThemeManager.instance()
