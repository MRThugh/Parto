# parto/ui/dialogs/command_palette.py
"""
Parto v0.3.0 - Searchable Command Palette (Ctrl+Shift+P)
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import List, Tuple, Callable, Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QWidget,
)


class CommandPalette(QDialog):
    """Quick-search command palette for fast keyboard access to all editor commands."""

    def __init__(
        self,
        commands: List[Tuple[str, str, str, Callable[[], None]]],
        parent: Optional[QWidget] = None,
    ):
        """
        commands: list of (action_id, display_name, shortcut_str, callback)
        """
        super().__init__(parent)
        self.setWindowTitle("Command Palette — Parto")
        self.setModal(True)
        self.setMinimumSize(480, 300)
        self.resize(540, 340)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        self.commands = commands
        self._filtered_indices: List[int] = []

        self._init_ui()
        self._filter_commands("")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Type a command or search action...")
        self.search_input.textChanged.connect(self._filter_commands)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self._execute_selected)
        layout.addWidget(self.list_widget)

    def _filter_commands(self, query: str):
        self.list_widget.clear()
        self._filtered_indices.clear()
        q = query.lower().strip()

        for idx, (cid, name, shortcut, _) in enumerate(self.commands):
            if not q or q in name.lower() or q in shortcut.lower():
                display_text = f"{name}    ({shortcut})" if shortcut else name
                item = QListWidgetItem(display_text)
                self.list_widget.addItem(item)
                self._filtered_indices.append(idx)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _execute_selected(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._filtered_indices):
            original_idx = self._filtered_indices[row]
            _, _, _, callback = self.commands[original_idx]
            self.accept()
            callback()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._execute_selected()
            event.accept()
        elif event.key() == Qt.Key_Escape:
            self.reject()
            event.accept()
        elif event.key() == Qt.Key_Down:
            cur = self.list_widget.currentRow()
            if cur < self.list_widget.count() - 1:
                self.list_widget.setCurrentRow(cur + 1)
            event.accept()
        elif event.key() == Qt.Key_Up:
            cur = self.list_widget.currentRow()
            if cur > 0:
                self.list_widget.setCurrentRow(cur - 1)
            event.accept()
        else:
            super().keyPressEvent(event)
