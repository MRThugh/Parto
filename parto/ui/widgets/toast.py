# parto/ui/widgets/toast.py
"""
Parto v0.3.0 - Floating Toast Feedback Notification
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtWidgets import QWidget, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from parto.themes.manager import get_theme_manager


class Toast(QWidget):
    """
    Floating banner providing subtle, non-intrusive action feedback.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("ToastWidget")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)

        self.label = QLabel("", self)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-weight: 500; font-size: 13px; background: transparent; border: none;")
        layout.addWidget(self.label)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity", self)
        self.anim.setDuration(220)
        self.anim.setEasingCurve(QEasingCurve.OutCubic)

        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._fade_out)

        self.hide()

    def show_message(self, text: str, duration_ms: int = 2400) -> None:
        """Display toast message centered at bottom of parent widget."""
        self.label.setText(text)
        self.adjustSize()

        if self.parentWidget():
            pw = self.parentWidget().width()
            ph = self.parentWidget().height()
            w = self.width()
            h = self.height()
            self.move((pw - w) // 2, ph - h - 50)

        self.show()
        self.raise_()
        self.anim.stop()
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.start()

        self.timer.start(duration_ms)

    def _fade_out(self):
        self.anim.stop()
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.finished.connect(self._on_fade_out_finished)
        self.anim.start()

    def _on_fade_out_finished(self):
        try:
            self.anim.finished.disconnect(self._on_fade_out_finished)
        except RuntimeError:
            pass
        self.hide()
