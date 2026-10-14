# parto/ui/dialogs/image_info.py
"""
Parto v0.3.0 - Technical Properties Inspector Dialog
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Dict, Any, Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QApplication,
    QWidget,
)
from parto.localization import t


class ImageInfoDialog(QDialog):
    """
    Detailed image metadata dialog with one-click clipboard copying.
    """

    def __init__(self, metadata: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(t("dialog.info.title", default="Image Properties — Parto"))
        self.setModal(True)
        self.setMinimumSize(480, 380)
        self.resize(520, 420)
        self.metadata = metadata

        self._init_ui()

        try:
            from parto.localization import get_localization_manager
            self._lm = get_localization_manager()
            if hasattr(self._lm, "locale_changed"):
                self._lm.locale_changed.connect(self.retranslate_ui)
                self.finished.connect(self._on_finished)
        except Exception:
            pass

    def _on_finished(self, *_) -> None:
        try:
            if hasattr(self, "_lm") and hasattr(self._lm, "locale_changed"):
                self._lm.locale_changed.disconnect(self.retranslate_ui)
        except Exception:
            pass

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Properties Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels([
            t("dialog.info.prop", default="Property"),
            t("dialog.info.value", default="Value"),
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        self._populate_properties()
        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.copy_path_btn = QPushButton(t("dialog.info.copy_path", default="Copy File Path"), self)
        self.copy_path_btn.clicked.connect(self._copy_path)
        btn_layout.addWidget(self.copy_path_btn)

        btn_layout.addStretch()

        self.close_btn = QPushButton(t("dialog.common.close", default="Close"), self)
        self.close_btn.setObjectName("PrimaryAction")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _populate_properties(self):
        has_alpha = self.metadata.get("has_alpha")
        transparency_str = (
            t("dialog.info.alpha_yes", default="Yes (Alpha Channel)")
            if has_alpha
            else t("dialog.info.alpha_no", default="None (Opaque)")
        )

        rows = [
            (t("dialog.info.dimensions", default="Dimensions"), self.metadata.get("dimensions", "N/A")),
            (t("dialog.info.aspect_ratio", default="Aspect Ratio"), self.metadata.get("aspect_ratio", "N/A")),
            (t("dialog.info.megapixels", default="Megapixels"), self.metadata.get("megapixels", "N/A")),
            (t("dialog.info.color_mode", default="Color Mode"), self.metadata.get("color_mode", "N/A")),
            (t("dialog.info.transparency", default="Transparency"), transparency_str),
            (t("dialog.info.file_format", default="File Format"), str(self.metadata.get("file_format", "N/A"))),
            (t("dialog.info.file_size", default="File Size"), str(self.metadata.get("file_size", "N/A"))),
            (t("dialog.info.file_path", default="File Path"), str(self.metadata.get("file_path", "N/A"))),
        ]

        self.table.setRowCount(len(rows))
        for i, (prop, val) in enumerate(rows):
            item_p = QTableWidgetItem(prop)
            item_v = QTableWidgetItem(val)
            self.table.setItem(i, 0, item_p)
            self.table.setItem(i, 1, item_v)

    def retranslate_ui(self):
        from parto.localization import t, get_localization_manager
        lm = get_localization_manager()
        self.setWindowTitle(t("dialog.info.title", default="Image Properties — Parto"))
        self.setLayoutDirection(Qt.RightToLeft if lm.is_rtl else Qt.LeftToRight)
        if hasattr(self, "table"):
            self.table.setHorizontalHeaderLabels([
                t("dialog.info.prop", default="Property"),
                t("dialog.info.value", default="Value"),
            ])
            self._populate_properties()
        if hasattr(self, "copy_path_btn"):
            self.copy_path_btn.setText(t("dialog.info.copy_path", default="Copy File Path"))
        if hasattr(self, "close_btn"):
            self.close_btn.setText(t("dialog.common.close", default="Close"))

    def _copy_path(self):
        path = str(self.metadata.get("file_path", ""))
        if path:
            QApplication.clipboard().setText(path)
