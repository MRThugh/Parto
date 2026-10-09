# parto/ui/dialogs/command_palette.py
"""
Parto Architecture 2.0 - Action-Driven Searchable Command Palette (Ctrl+Shift+P)
Author: Ali Kamrani (MRThugh)

Provides quick keyboard discovery and execution across all registered actions.
Supports Action objects with rich search (name, description, category, shortcut)
and backward-compatible tuple command lists.
"""

from __future__ import annotations
from typing import List, Tuple, Callable, Optional, Union, Any
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
from parto.localization import t


class CommandPalette(QDialog):
    """Quick-search command palette for fast keyboard access to all editor actions."""

    def __init__(
        self,
        commands: Optional[Union[List[Any], List[Tuple[str, str, str, Callable[[], None]]]]] = None,
        parent: Optional[QWidget] = None,
    ):
        """
        commands: list of Action objects or tuples (action_id, display_name, shortcut_str, callback)
        """
        super().__init__(parent)
        self.setWindowTitle(t("dialog.palette.title", default="Command Palette — Parto"))
        self.setModal(True)
        self.setMinimumSize(480, 320)
        self.resize(560, 360)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)

        # Normalize incoming commands into standardized descriptor entries
        self._entries: List[Tuple[str, str, str, str, str, Callable[[], None]]] = []

        if commands is None:
            from ...actions.registry import get_action_registry
            from ...actions.context import get_context_manager
            reg = get_action_registry()
            ctx_mgr = get_context_manager()
            ctx = ctx_mgr.create_context()
            for act in reg.get_all():
                if act.is_enabled(ctx):
                    self._entries.append((
                        act.id,
                        act.name,
                        act.description,
                        act.category,
                        act.shortcut,
                        lambda a=act, c=ctx: a.execute(c),
                    ))
        else:
            for item in commands:
                if hasattr(item, "id") and hasattr(item, "name"):
                    # Action object
                    from ...actions.context import get_context_manager
                    ctx = get_context_manager().create_context()
                    self._entries.append((
                        item.id,
                        item.name,
                        getattr(item, "description", ""),
                        getattr(item, "category", ""),
                        getattr(item, "shortcut", ""),
                        lambda a=item, c=ctx: a.execute(c),
                    ))
                elif isinstance(item, (tuple, list)) and len(item) == 4:
                    # Tuple: (action_id, display_name, shortcut_str, callback)
                    cid, name, sc, cb = item
                    self._entries.append((cid, name, "", "", sc, cb))

        self.commands = [
            (eid, ename, esc, ecb) for (eid, ename, _, _, esc, ecb) in self._entries
        ]
        self._filtered_indices: List[int] = []

        self._init_ui()
        self._filter_commands("")

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText(t("dialog.palette.placeholder", default="Type a command or search action..."))
        self.search_input.textChanged.connect(self._filter_commands)
        layout.addWidget(self.search_input)

        self.list_widget = QListWidget(self)
        self.list_widget.itemDoubleClicked.connect(self._execute_selected)
        layout.addWidget(self.list_widget)

    def _filter_commands(self, query: str):
        self.list_widget.clear()
        self._filtered_indices.clear()
        q = query.lower().strip()

        for idx, (cid, name, desc, cat, shortcut, _) in enumerate(self._entries):
            matched = (
                not q
                or q in name.lower()
                or q in desc.lower()
                or q in cat.lower()
                or q in cid.lower()
                or (shortcut and q in shortcut.lower())
            )
            if matched:
                parts = []
                if cat:
                    parts.append(f"[{cat}] ")
                parts.append(name)
                if shortcut:
                    display_text = f"{''.join(parts):<40}    ({shortcut})"
                else:
                    display_text = ''.join(parts)

                item = QListWidgetItem(display_text)
                self.list_widget.addItem(item)
                self._filtered_indices.append(idx)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _execute_selected(self):
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._filtered_indices):
            original_idx = self._filtered_indices[row]
            _, _, _, _, _, callback = self._entries[original_idx]
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
