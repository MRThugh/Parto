# parto/ui/dialogs/about.py
"""
Parto v0.3.0 - About Dialog
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)
from parto.resources.icons import get_parto_icon


class AboutDialog(QDialog):
    """About Parto v0.3.0 modal dialog."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("About Parto")
        self.setModal(True)
        self.setFixedSize(440, 360)

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignCenter)

        # Logo
        logo_label = QLabel(self)
        logo_icon = get_parto_icon("logo", "#0284c7", size=56)
        logo_label.setPixmap(logo_icon.pixmap(56, 56))
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        # Title & Version
        title_label = QLabel("Parto (پرتو) v0.3.0", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; margin-top: 4px;")
        layout.addWidget(title_label)

        desc_label = QLabel(
            "A fast, modern, and lightweight desktop image editor\n"
            "built with Python, PySide6, and Pillow.",
            self,
        )
        desc_label.setAlignment(Qt.AlignCenter)
        desc_label.setStyleSheet("font-size: 12px; color: #a1a1aa; line-height: 1.4;")
        layout.addWidget(desc_label)

        # Author & Repo info
        author_label = QLabel(
            "<b>Author:</b> Ali Kamrani (MRThugh)<br>"
            "<b>License:</b> MIT Open Source<br>"
            "<b>Repository:</b> <a style='color: #0284c7;' href='https://github.com/MRThugh/Parto'>github.com/MRThugh/Parto</a>",
            self,
        )
        author_label.setOpenExternalLinks(True)
        author_label.setAlignment(Qt.AlignCenter)
        author_label.setStyleSheet("font-size: 12px; margin-top: 6px;")
        layout.addWidget(author_label)

        layout.addSpacing(10)

        # Close
        close_btn = QPushButton("Close", self)
        close_btn.setObjectName("PrimaryAction")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)
