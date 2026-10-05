# parto/ui/panels/brush/widgets/section.py
"""
Parto Brush Studio — Collapsible Section Card Widget
Provides clean disclosure toggles with modern typography and theme awareness.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QToolButton,
    QFrame,
    QSizePolicy,
)
from parto.themes.manager import get_theme_manager


class CollapsibleSection(QWidget):
    """
    Accordion-style container with header title, toggle chevron, and collapsible body.
    """

    toggled = Signal(bool)

    def __init__(
        self,
        title: str,
        collapsed: bool = False,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self._collapsed = collapsed

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 4, 0, 4)
        main_layout.setSpacing(6)

        # Header bar
        self.header = QFrame(self)
        self.header.setObjectName("SectionHeader")
        self.header.setCursor(Qt.PointingHandCursor)
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(6, 4, 6, 4)
        header_layout.setSpacing(6)

        self.btn_toggle = QToolButton(self.header)
        self.btn_toggle.setText("▾" if not collapsed else "▸")
        self.btn_toggle.setFixedSize(16, 16)
        self.btn_toggle.setStyleSheet("border: none; background: transparent; font-size: 10px; font-weight: bold;")
        self.btn_toggle.clicked.connect(self.toggle)
        header_layout.addWidget(self.btn_toggle)

        self.lbl_title = QLabel(title.upper(), self.header)
        self.lbl_title.setStyleSheet("font-size: 11px; font-weight: 700; letter-spacing: 0.5px;")
        header_layout.addWidget(self.lbl_title)

        header_layout.addStretch()
        main_layout.addWidget(self.header)

        # Content container
        self.content_widget = QWidget(self)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(8, 0, 8, 4)
        self.content_layout.setSpacing(8)
        main_layout.addWidget(self.content_widget)

        if self._collapsed:
            self.content_widget.hide()

        self.header.mousePressEvent = self._on_header_clicked
        self._apply_theme()
        get_theme_manager().theme_changed.connect(lambda _: self._apply_theme())

    def _on_header_clicked(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.toggle()

    def toggle(self) -> None:
        self.set_collapsed(not self._collapsed)

    def set_collapsed(self, collapsed: bool) -> None:
        self._collapsed = collapsed
        self.btn_toggle.setText("▸" if collapsed else "▾")
        self.content_widget.setVisible(not collapsed)
        self.toggled.emit(collapsed)

    def is_collapsed(self) -> bool:
        return self._collapsed

    def add_widget(self, widget: QWidget) -> None:
        self.content_layout.addWidget(widget)

    def add_layout(self, layout: QHBoxLayout | QVBoxLayout) -> None:
        self.content_layout.addLayout(layout)

    def _apply_theme(self) -> None:
        pal = get_theme_manager().get_palette()
        border = pal.get("border_subtle", "#27272a")
        text_muted = pal.get("text_muted", "#a1a1aa")
        sunken = pal.get("surface_sunken", "#18181b")

        self.header.setStyleSheet(f"""
            QFrame#SectionHeader {{
                background-color: {sunken};
                border: 1px solid {border};
                border-radius: 4px;
            }}
            QFrame#SectionHeader:hover {{
                border-color: {pal.get('border', '#3f3f46')};
            }}
            QLabel {{
                color: {text_muted};
            }}
            QToolButton {{
                color: {text_muted};
            }}
        """)
