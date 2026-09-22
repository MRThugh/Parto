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


class ImageInfoDialog(QDialog):
    """
    Detailed image metadata dialog with one-click clipboard copying.
    """

    def __init__(self, metadata: Dict[str, Any], parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Image Properties — Parto")
        self.setModal(True)
        self.setMinimumSize(480, 380)
        self.resize(520, 420)
        self.metadata = metadata

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        # Properties Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Property", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        rows = [
            ("Dimensions", self.metadata.get("dimensions", "N/A")),
            ("Aspect Ratio", self.metadata.get("aspect_ratio", "N/A")),
            ("Megapixels", self.metadata.get("megapixels", "N/A")),
            ("Color Mode", self.metadata.get("color_mode", "N/A")),
            ("Transparency", "Yes (Alpha Channel)" if self.metadata.get("has_alpha") else "None (Opaque)"),
            ("File Format", str(self.metadata.get("file_format", "N/A"))),
            ("File Size", str(self.metadata.get("file_size", "N/A"))),
            ("File Path", str(self.metadata.get("file_path", "N/A"))),
        ]

        self.table.setRowCount(len(rows))
        for i, (prop, val) in enumerate(rows):
            item_p = QTableWidgetItem(prop)
            item_v = QTableWidgetItem(val)
            self.table.setItem(i, 0, item_p)
            self.table.setItem(i, 1, item_v)

        layout.addWidget(self.table)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        copy_path_btn = QPushButton("Copy File Path", self)
        copy_path_btn.clicked.connect(self._copy_path)
        btn_layout.addWidget(copy_path_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close", self)
        close_btn.setObjectName("PrimaryAction")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _copy_path(self):
        path = str(self.metadata.get("file_path", ""))
        if path:
            QApplication.clipboard().setText(path)
