# parto/ui/dialogs/filter_gallery.py
"""
Parto v0.3.0 - Photographic Filter Gallery with Live Preview & Compare
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QFrame,
    QWidget,
)
from parto.image.filters import apply_filter, SUPPORTED_FILTERS
from parto.utils.conversions import pil_to_qpixmap


class FilterDialog(QDialog):
    """
    Interactive photographic filter browser with instant thumbnail preview
    and before/after comparison.
    """

    def __init__(self, source_image: Image.Image, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Filter Gallery — Parto")
        self.setModal(True)
        self.setFixedSize(540, 400)

        # Generate a lightweight preview thumbnail
        thumb = source_image.copy()
        thumb.thumbnail((320, 240), Image.Resampling.BILINEAR)
        self.orig_thumbnail = thumb
        self.current_preview = thumb
        self.selected_filter: str = "grayscale"

        self._init_ui()
        self._update_preview()

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        # Left Column: Filter list
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)

        list_label = QLabel("Available Filters:", self)
        list_label.setStyleSheet("font-weight: 600; font-size: 12px;")
        left_layout.addWidget(list_label)

        self.filter_list = QListWidget(self)
        for f_id in SUPPORTED_FILTERS:
            item = QListWidgetItem(f_id.replace("_", " ").title())
            item.setData(Qt.UserRole, f_id)
            self.filter_list.addItem(item)

        self.filter_list.setCurrentRow(0)
        self.filter_list.currentItemChanged.connect(self._on_filter_selection_changed)
        left_layout.addWidget(self.filter_list)

        layout.addLayout(left_layout, stretch=1)

        # Right Column: Preview and controls
        right_layout = QVBoxLayout()
        right_layout.setSpacing(12)

        # Preview Frame
        preview_frame = QFrame(self)
        preview_frame.setFrameShape(QFrame.StyledPanel)
        preview_frame.setMinimumSize(280, 220)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setAlignment(Qt.AlignCenter)

        self.preview_label = QLabel(self)
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)

        right_layout.addWidget(preview_frame, stretch=1)

        # Compare Button
        self.compare_btn = QPushButton("Hold to View Original", self)
        self.compare_btn.pressed.connect(self._show_original)
        self.compare_btn.released.connect(self._show_filtered)
        right_layout.addWidget(self.compare_btn)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        cancel_btn = QPushButton("Cancel", self)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        apply_btn = QPushButton("Apply Filter", self)
        apply_btn.setObjectName("PrimaryAction")
        apply_btn.clicked.connect(self.accept)
        btn_layout.addWidget(apply_btn)

        right_layout.addLayout(btn_layout)

        layout.addLayout(right_layout, stretch=2)

    def _on_filter_selection_changed(self, current: Optional[QListWidgetItem], _: Optional[QListWidgetItem]):
        if current:
            self.selected_filter = current.data(Qt.UserRole)
            self._update_preview()

    def _update_preview(self):
        filtered = apply_filter(self.orig_thumbnail.copy(), self.selected_filter)
        self.current_preview = filtered
        self._set_pixmap(filtered)

    def _show_original(self):
        self._set_pixmap(self.orig_thumbnail)

    def _show_filtered(self):
        self._set_pixmap(self.current_preview)

    def _set_pixmap(self, img: Image.Image):
        pix = pil_to_qpixmap(img)
        self.preview_label.setPixmap(pix)

    def get_filter_name(self) -> str:
        return self.selected_filter
