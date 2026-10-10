# parto/ui/dialogs/resize.py
"""
Parto v0.3.0 - Image Resizing Dialog with Aspect Lock & Percentage Presets
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Tuple, Optional
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QComboBox,
    QGroupBox,
    QWidget,
)


from parto.localization import t


class ResizeDialog(QDialog):
    """Dialog configuring image resize dimensions and resampling algorithms."""

    def __init__(self, current_width: int, current_height: int, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(t("dialog.resize.title", default="Resize Image — Parto"))
        self.setModal(True)
        self.setMinimumSize(420, 390)
        self.resize(440, 410)

        self.orig_w = max(1, current_width)
        self.orig_h = max(1, current_height)
        self.aspect_ratio = self.orig_w / float(self.orig_h)

        self._updating = False
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # Dimension Inputs Group
        self.dim_group = QGroupBox(t("dialog.resize.dimensions_group", default="Dimensions (Pixels)"), self)
        dim_layout = QVBoxLayout(self.dim_group)
        dim_layout.setSpacing(12)

        # Width
        w_row = QHBoxLayout()
        self.w_lbl = QLabel(t("dialog.resize.width", default="Width:"), self)
        w_row.addWidget(self.w_lbl)
        self.width_spin = QSpinBox(self)
        self.width_spin.setRange(1, 65536)
        self.width_spin.setValue(self.orig_w)
        self.width_spin.valueChanged.connect(self._on_width_changed)
        w_row.addWidget(self.width_spin)
        dim_layout.addLayout(w_row)

        # Height
        h_row = QHBoxLayout()
        self.h_lbl = QLabel(t("dialog.resize.height", default="Height:"), self)
        h_row.addWidget(self.h_lbl)
        self.height_spin = QSpinBox(self)
        self.height_spin.setRange(1, 65536)
        self.height_spin.setValue(self.orig_h)
        self.height_spin.valueChanged.connect(self._on_height_changed)
        h_row.addWidget(self.height_spin)
        dim_layout.addLayout(h_row)

        # Aspect lock checkbox
        self.lock_aspect_cb = QCheckBox(t("dialog.resize.proportions", default="Maintain Aspect Ratio"), self)
        self.lock_aspect_cb.setChecked(True)
        self.lock_aspect_cb.toggled.connect(self._on_lock_toggled)
        dim_layout.addWidget(self.lock_aspect_cb)

        layout.addWidget(self.dim_group)

        # Presets
        self.preset_group = QGroupBox(t("dialog.resize.quick_presets", default="Quick Presets"), self)
        preset_layout = QHBoxLayout(self.preset_group)
        preset_layout.setSpacing(6)

        for pct in (25, 50, 75, 100, 150, 200):
            btn = QPushButton(f"{pct}%", self)
            btn.clicked.connect(lambda _, p=pct: self._apply_preset(p))
            preset_layout.addWidget(btn)

        layout.addWidget(self.preset_group)

        # Resampling Filter
        resample_layout = QHBoxLayout()
        self.resample_lbl = QLabel(t("dialog.resize.resample", default="Resampling Quality:"), self)
        resample_layout.addWidget(self.resample_lbl)
        self.resample_combo = QComboBox(self)
        self.resample_combo.addItems([
            "Lanczos (Best Quality)",
            "Bicubic (Balanced)",
            "Bilinear (Fast)",
            "Nearest (Pixel Art)",
        ])
        resample_layout.addWidget(self.resample_combo)
        layout.addLayout(resample_layout)

        # Megapixels Info Label
        self.info_label = QLabel(self)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("color: #a1a1aa; font-size: 11px;")
        self._update_info()
        layout.addWidget(self.info_label)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.cancel_btn = QPushButton(t("dialog.common.cancel", default="Cancel"), self)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        self.apply_btn = QPushButton(t("dialog.common.apply", default="Apply"), self)
        self.apply_btn.setObjectName("PrimaryAction")
        self.apply_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.apply_btn)

        layout.addLayout(btn_layout)

    def retranslate_ui(self):
        """Refresh dialog texts on locale change."""
        self.setWindowTitle(t("dialog.resize.title", default="Resize Image"))
        if hasattr(self, "dim_group"):
            self.dim_group.setTitle(t("dialog.resize.dimensions_group", default="Dimensions (Pixels)"))
        if hasattr(self, "w_lbl"):
            self.w_lbl.setText(t("dialog.resize.width", default="Width:"))
        if hasattr(self, "h_lbl"):
            self.h_lbl.setText(t("dialog.resize.height", default="Height:"))
        if hasattr(self, "lock_aspect_cb"):
            self.lock_aspect_cb.setText(t("dialog.resize.proportions", default="Maintain Aspect Ratio"))
        if hasattr(self, "preset_group"):
            self.preset_group.setTitle(t("dialog.resize.quick_presets", default="Quick Presets"))
        if hasattr(self, "resample_lbl"):
            self.resample_lbl.setText(t("dialog.resize.resample", default="Resampling Quality:"))
        if hasattr(self, "cancel_btn"):
            self.cancel_btn.setText(t("dialog.common.cancel", default="Cancel"))
        if hasattr(self, "apply_btn"):
            self.apply_btn.setText(t("dialog.common.apply", default="Apply"))
        self._update_info()

    def _on_width_changed(self, w: int):
        if self._updating:
            return
        if self.lock_aspect_cb.isChecked():
            self._updating = True
            new_h = max(1, int(round(w / self.aspect_ratio)))
            self.height_spin.setValue(new_h)
            self._updating = False
        self._update_info()

    def _on_height_changed(self, h: int):
        if self._updating:
            return
        if self.lock_aspect_cb.isChecked():
            self._updating = True
            new_w = max(1, int(round(h * self.aspect_ratio)))
            self.width_spin.setValue(new_w)
            self._updating = False
        self._update_info()

    def _on_lock_toggled(self, checked: bool):
        if checked:
            self.aspect_ratio = self.width_spin.value() / float(max(1, self.height_spin.value()))

    def apply_preset(self, pct: int):
        """Public method for applying preset percentage."""
        self._apply_preset(pct)

    def _apply_preset(self, pct: int):
        self._updating = True
        scale = pct / 100.0
        w = max(1, int(round(self.orig_w * scale)))
        h = max(1, int(round(self.orig_h * scale)))
        self.width_spin.setValue(w)
        self.height_spin.setValue(h)
        self._updating = False
        self._update_info()

    def _update_info(self):
        w = self.width_spin.value()
        h = self.height_spin.value()
        mp = (w * h) / 1_000_000.0
        pct = (w / float(self.orig_w)) * 100.0
        self.info_label.setText(f"Result: {w} × {h} px ({mp:.2f} MP) — {pct:.0f}% of original")

    def get_dimensions(self) -> Tuple[int, int]:
        return self.width_spin.value(), self.height_spin.value()

    def get_resample_filter(self) -> int:
        idx = self.resample_combo.currentIndex()
        if idx == 0:
            return Image.Resampling.LANCZOS
        elif idx == 1:
            return Image.Resampling.BICUBIC
        elif idx == 2:
            return Image.Resampling.BILINEAR
        return Image.Resampling.NEAREST
