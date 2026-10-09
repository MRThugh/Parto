# parto/ui/widgets/crop_bar.py
"""
Parto v0.4.0 - Theme-Aware Floating Crop Control Bar
Author: Ali Kamrani (MRThugh)
Integrated with Localization Subsystem.
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
from parto.localization import t


class CropBar(QWidget):
    """
    Floating or docked control bar for crop tool aspect ratio constraints and execution.
    Completely theme-aware and localized.
    """
    aspect_ratio_changed = Signal(str)
    apply_clicked = Signal()
    cancel_clicked = Signal()

    RATIO_SPECS = [
        ("crop.ratio.freeform", "free", "Free"),
        ("crop.ratio.square", "1:1", "1:1 (Square)"),
        ("crop.ratio.standard", "4:3", "4:3 (Standard)"),
        ("crop.ratio.widescreen", "16:9", "16:9 (Widescreen)"),
        ("crop.ratio.photo", "3:2", "3:2 (Photo)"),
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setObjectName("CropBar")
        self._init_ui()
        get_theme_manager().theme_changed.connect(self._on_theme_changed)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(10)

        self.title_label = QLabel(t("action.edit.crop", default="Crop:"), self)
        self.title_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        layout.addWidget(self.title_label)

        self.ratio_combo = QComboBox(self)
        self._populate_ratios()
        self.ratio_combo.currentIndexChanged.connect(self._on_index_changed)
        layout.addWidget(self.ratio_combo)

        self.size_label = QLabel("", self)
        self.size_label.setStyleSheet("font-size: 11px; opacity: 0.8;")
        layout.addWidget(self.size_label)

        layout.addSpacing(6)

        self.apply_btn = QPushButton(t("crop.apply"), self)
        self.apply_btn.setObjectName("PrimaryAction")
        self.apply_btn.setToolTip("Apply Crop (Enter)")
        self.apply_btn.clicked.connect(self.apply_clicked.emit)
        layout.addWidget(self.apply_btn)

        self.cancel_btn = QPushButton(t("crop.cancel"), self)
        self.cancel_btn.setToolTip("Cancel Crop (Esc)")
        self.cancel_btn.clicked.connect(self.cancel_clicked.emit)
        layout.addWidget(self.cancel_btn)

    def _populate_ratios(self):
        current_data = self.ratio_combo.currentData() if self.ratio_combo.count() > 0 else "free"
        self.ratio_combo.blockSignals(True)
        self.ratio_combo.clear()
        for key, code, default_txt in self.RATIO_SPECS:
            label = t(key, default=default_txt)
            self.ratio_combo.addItem(label, code)

        # Restore selected index
        for idx in range(self.ratio_combo.count()):
            if self.ratio_combo.itemData(idx) == current_data:
                self.ratio_combo.setCurrentIndex(idx)
                break
        self.ratio_combo.blockSignals(False)

    def retranslate_ui(self):
        """Refresh displayed texts on language change."""
        self.title_label.setText(t("action.edit.crop", default="Crop:"))
        self.apply_btn.setText(t("crop.apply"))
        self.cancel_btn.setText(t("crop.cancel"))
        self._populate_ratios()

    def set_dimension_text(self, text: str):
        self.size_label.setText(text)

    def _on_index_changed(self, index: int):
        data = self.ratio_combo.itemData(index)
        if data:
            self.aspect_ratio_changed.emit(str(data).lower())

    def _on_ratio_changed(self, text: str):
        ratio_key = text.split(" ")[0].lower()
        self.aspect_ratio_changed.emit(ratio_key)

    def _on_theme_changed(self, _: str):
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()
