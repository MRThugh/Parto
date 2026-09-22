# parto/history/manager.py
"""
Parto v0.3.0 - Centralized History & Undo/Redo Manager
Author: Ali Kamrani (MRThugh)
"""

from __future__ import annotations
from typing import Any, List, Optional
from PySide6.QtCore import QObject, Signal
from .commands import Command


_CLEAN_MARKER = object()
_UNREACHABLE_MARKER = object()


class HistoryManager(QObject):
    """
    Manages undo/redo stacks, operation limits, and state notifications.
    """
    history_changed = Signal()

    def __init__(self, max_history: int = 30, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.max_history: int = max_history
        self._undo_stack: List[Command] = []
        self._redo_stack: List[Command] = []
        self._clean_marker: Any = _CLEAN_MARKER
        self._current_revision: int = 0
        self._base_revision: int = 0
        self._clean_revision: int = 0

    @property
    def current_revision(self) -> int:
        return self._current_revision

    @property
    def is_clean(self) -> bool:
        """Return True if the current history state matches the clean save point."""
        if self._clean_marker is _UNREACHABLE_MARKER:
            return False
        if self._clean_revision < self._base_revision:
            return False
        return self._current_revision == self._clean_revision

    def set_clean(self) -> None:
        """Mark the current head of the undo stack as the clean save point."""
        self._clean_marker = self._undo_stack[-1] if self._undo_stack else _CLEAN_MARKER
        self._clean_revision = self._current_revision

    @property
    def can_undo(self) -> bool:
        return len(self._undo_stack) > 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0

    @property
    def undo_count(self) -> int:
        return len(self._undo_stack)

    @property
    def redo_count(self) -> int:
        return len(self._redo_stack)

    def undo_description(self) -> str:
        if self._undo_stack:
            return f"Undo {self._undo_stack[-1].name}"
        return "Undo"

    def redo_description(self) -> str:
        if self._redo_stack:
            return f"Redo {self._redo_stack[-1].name}"
        return "Redo"

    @property
    def undo_stack(self) -> list:
        return self._undo_stack

    @property
    def redo_stack(self) -> list:
        return self._redo_stack

    def execute(self, command: Command) -> None:
        """Execute command and push to history."""
        command.redo()
        self.push(command)

    def push(self, command: Command) -> None:
        """Add a newly executed command to history."""
        self._current_revision += 1
        setattr(command, "_revision", self._current_revision)
        self._undo_stack.append(command)
        self._redo_stack.clear()

        # Enforce history capacity safely while preserving clean marker integrity
        if len(self._undo_stack) > self.max_history:
            evicted = self._undo_stack.pop(0)
            self._base_revision = getattr(evicted, "_revision", self._base_revision + 1)
            if self._clean_marker is evicted or self._clean_marker is _CLEAN_MARKER:
                self._clean_marker = _UNREACHABLE_MARKER

        self.history_changed.emit()

    def undo(self) -> bool:
        """Undo top command on the stack."""
        if not self._undo_stack:
            return False

        cmd = self._undo_stack[-1]
        try:
            cmd.undo()
            self._undo_stack.pop()
            self._redo_stack.append(cmd)
            if self._undo_stack:
                self._current_revision = getattr(self._undo_stack[-1], "_revision", self._base_revision)
            else:
                self._current_revision = self._base_revision
            self.history_changed.emit()
            return True
        except Exception as e:
            import logging
            logging.getLogger("parto.history").error(f"Undo failed for {cmd.name}: {e}")
            return False

    def redo(self) -> bool:
        """Redo top command on the redo stack."""
        if not self._redo_stack:
            return False

        cmd = self._redo_stack[-1]
        try:
            cmd.redo()
            self._redo_stack.pop()
            self._undo_stack.append(cmd)
            self._current_revision = getattr(cmd, "_revision", self._current_revision)
            self.history_changed.emit()
            return True
        except Exception as e:
            import logging
            logging.getLogger("parto.history").error(f"Redo failed for {cmd.name}: {e}")
            return False

    def clear(self) -> None:
        """Clear all undo and redo history."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._clean_marker = _CLEAN_MARKER
        self._current_revision = 0
        self._base_revision = 0
        self._clean_revision = 0
        self.history_changed.emit()
