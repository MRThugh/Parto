# parto/ui/widgets/crop_bar.py
"""
Parto v0.3.0 - Theme-Aware Floating Crop Control Bar
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QPushButton,
)
from parto.themes.manager import get_theme_manager


class CropBar(QWidget):
    """
    Floating or docked control bar for crop tool aspect ratio constraints and execution.
    Completely theme-aware with crisp button states.
    """
    aspect_ratio_changed = Signal(str)
    apply_clicked = Signal()
    cancel_clicked = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("CropBar")
        self._init_ui()
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        title_label = QLabel("Crop:", self)
        title_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(title_label)

        self.ratio_combo = QComboBox(self)
        self.ratio_combo.addItems([
            "Free",
            "1:1 (Square)",
            "4:3 (Standard)",
            "16:9 (Widescreen)",
            "3:2 (Photo)",
        ])
        self.ratio_combo.currentTextChanged.connect(self._on_ratio_changed)
        layout.addWidget(self.ratio_combo)

        self.size_label = QLabel("", self)
        self.size_label.setStyleSheet("font-size: 11px; opacity: 0.8;")
        layout.addWidget(self.size_label)

        layout.addSpacing(6)

        self.apply_btn = QPushButton("Apply", self)
        self.apply_btn.setObjectName("PrimaryAction")
        self.apply_btn.setToolTip("Apply Crop (Enter)")
        self.apply_btn.clicked.connect(self.apply_clicked.emit)
        layout.addWidget(self.apply_btn)

        self.cancel_btn = QPushButton("Cancel", self)
        self.cancel_btn.setToolTip("Cancel Crop (Esc)")
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self.cancel_btn)

    def set_dimension_text(self, text: str):
        self.size_label.setText(text)

    def _on_ratio_changed(self, text: str):
        ratio_key = text.split(" ")[0].lower()
        self.aspect_ratio_changed.emit(ratio_key)

    def _on_theme_changed(self, _: str):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
