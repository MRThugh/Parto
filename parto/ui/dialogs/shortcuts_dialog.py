# parto/ui/dialogs/shortcuts_dialog.py
"""
Parto v0.3.0 - Keyboard Shortcuts Reference Cheat Sheet
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
    QWidget,
)
from parto.shortcuts.manager import get_shortcut_manager


class ShortcutsDialog(QDialog):
    """
    Searchable cheat sheet reference of all registered application keyboard shortcuts.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts — Parto")
        self.setModal(True)
        self.setFixedSize(580, 460)

        self._init_ui()
        self._populate_table("")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Search Bar
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Filter shortcuts by action, key, or category...")
        self.search_input.textChanged.connect(self._populate_table)
        layout.addWidget(self.search_input)

        # Table
        self.table = QTableWidget(self)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Action", "Shortcut", "Category"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        layout.addWidget(self.table)

        # Close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close", self)
        close_btn.setObjectName("PrimaryAction")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _populate_table(self, query: str):
        self.table.setRowCount(0)
        q = query.lower().strip()
        all_shortcuts = get_shortcut_manager().get_all()

        matching = []
        for defn in all_shortcuts:
            if not defn.key_sequence:
                continue
            if not q or (
                q in defn.name.lower()
                or q in defn.key_sequence.lower()
                or q in defn.category.lower()
            ):
                matching.append(defn)

        self.table.setRowCount(len(matching))
        for row, defn in enumerate(matching):
            self.table.setItem(row, 0, QTableWidgetItem(defn.name))
            self.table.setItem(row, 1, QTableWidgetItem(defn.key_sequence))
            self.table.setItem(row, 2, QTableWidgetItem(defn.category))
