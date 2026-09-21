# parto/ui/widgets/welcome.py
"""
Parto v0.3.0 - Modern Welcome Screen with Drag-and-Drop
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)
from parto.resources.icons import get_parto_icon
from parto.themes.manager import get_theme_manager


class WelcomeScreen(QWidget):
    """
    Empty-state landing screen inviting users to open, drag-and-drop, or create new images.
    """
    open_requested = Signal()
    new_requested = Signal()
    file_dropped = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)

        # Drop Zone Card Frame
        card = QFrame(self)
        card.setObjectName("WelcomeCard")
        card.setMinimumSize(480, 360)
        card.setMaximumSize(620, 460)

        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setContentsMargins(36, 36, 36, 36)
        card_layout.setSpacing(16)

        # Parto Logo Icon
        logo_label = QLabel(self)
        logo_icon = get_parto_icon("logo", "#0284c7", size=64)
        logo_label.setPixmap(logo_icon.pixmap(64, 64))
        logo_label.setAlignment(Qt.AlignCenter)
        card_layout.addWidget(logo_label)

        # App Title & Subtitle
        title_label = QLabel("Parto (پرتو)", self)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: 700; margin-top: 4px;")
        card_layout.addWidget(title_label)

        subtitle_label = QLabel("Fast, modern, and lightweight desktop image editor", self)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("font-size: 13px; color: #a1a1aa; margin-bottom: 8px;")
        card_layout.addWidget(subtitle_label)

        # Drag-and-drop prompt
        drop_prompt = QLabel("Drop an image file here to start editing", self)
        drop_prompt.setAlignment(Qt.AlignCenter)
        drop_prompt.setStyleSheet("font-size: 13px; font-weight: 500;")
        card_layout.addWidget(drop_prompt)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        btn_layout.setAlignment(Qt.AlignCenter)

        open_btn = QPushButton("Open Image...", self)
        open_btn.setObjectName("PrimaryAction")
        open_btn.setIcon(get_parto_icon("open", "#ffffff", 18))
        open_btn.clicked.connect(self.open_requested.emit)
        btn_layout.addWidget(open_btn)

        new_btn = QPushButton("New Canvas...", self)
        new_btn.clicked.connect(self.new_requested.emit)
        btn_layout.addWidget(new_btn)

        card_layout.addLayout(btn_layout)

        # Supported Format Badges
        formats_layout = QHBoxLayout()
        formats_layout.setSpacing(8)
        formats_layout.setAlignment(Qt.AlignCenter)

        for fmt in ("PNG", "JPEG", "WebP", "BMP", "TIFF", "HEIC"):
            badge = QLabel(fmt, self)
            badge.setStyleSheet(
                "font-size: 10px; font-weight: 600; padding: 3px 7px; "
                "border-radius: 4px; background-color: rgba(120, 120, 130, 0.18); color: #a1a1aa;"
            )
            formats_layout.addWidget(badge)

        card_layout.addSpacing(8)
        card_layout.addLayout(formats_layout)

        main_layout.addWidget(card)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].isLocalFile():
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls and urls[0].isLocalFile():
            local_path = urls[0].toLocalFile()
            self.file_dropped.emit(local_path)
            event.acceptProposedAction()
