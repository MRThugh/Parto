# parto/history/manager.py
"""
Parto Architecture 2.0 - Centralized History & Undo/Redo Manager
Author: Ali Kamrani (MRThugh)

Manages undo/redo stacks, reversible commands, command coalescing (merging),
transaction grouping, and clean-state dirty tracking.
"""

from __future__ import annotations
from typing import Any, List, Optional
from contextlib import contextmanager
import logging
from PySide6.QtCore import QObject, Signal
from .commands import Command
from ..commands.compound import TransactionCommand


_CLEAN_MARKER = object()
_UNREACHABLE_MARKER = object()
_logger = logging.getLogger("parto.history")


class HistoryManager(QObject):
    """
    Manages undo/redo stacks, operation limits, command merging,
    transactions, and state notifications.
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

        # Transaction state
        self._transaction_depth: int = 0
        self._active_transaction_name: str = ""
        self._active_transaction_commands: List[Command] = []

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
        return len(self._undo_stack) > 0 and self._transaction_depth == 0

    @property
    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0 and self._transaction_depth == 0

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
    def undo_stack(self) -> List[Command]:
        return self._undo_stack

    @property
    def redo_stack(self) -> List[Command]:
        return self._redo_stack

    @property
    def is_in_transaction(self) -> bool:
        """Return True if an open transaction is currently active."""
        return self._transaction_depth > 0

    def execute(self, command: Command) -> bool:
        """
        Validate, execute, and record a command into history or the active transaction.
        Supports command merging for coalescing continuous interactions.
        """
        if not command.can_execute():
            _logger.warning(f"Command {command.name} failed preconditions check")
            return False

        # If inside an active transaction, execute and append to transaction buffer
        if self._transaction_depth > 0:
            command.execute()
            self._active_transaction_commands.append(command)
            return True

        # Check if incoming command can merge into the command on top of undo stack
        if self._undo_stack and self._undo_stack[-1].can_merge(command):
            if self._undo_stack[-1].merge_with(command):
                command.execute()
                self._current_revision += 1
                setattr(self._undo_stack[-1], "_revision", self._current_revision)
                self._redo_stack.clear()
                self.history_changed.emit()
                return True

        # Standard execution & push
        command.execute()
        self.push(command)
        return True

    def push(self, command: Command) -> None:
        """Add an already executed command to the undo history stack."""
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
        if not self._undo_stack or self._transaction_depth > 0:
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
            _logger.error(f"Undo failed for {cmd.name}: {e}")
            return False

    def redo(self) -> bool:
        """Redo top command on the redo stack."""
        if not self._redo_stack or self._transaction_depth > 0:
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
            _logger.error(f"Redo failed for {cmd.name}: {e}")
            return False

    def clear(self) -> None:
        """Clear all undo and redo history and active transactions."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._clean_marker = _CLEAN_MARKER
        self._current_revision = 0
        self._base_revision = 0
        self._clean_revision = 0
        self._transaction_depth = 0
        self._active_transaction_commands.clear()
        self._active_transaction_name = ""
        self.history_changed.emit()

    # --- Transaction Management ---

    def begin_transaction(self, name: str = "Transaction") -> None:
        """
        Begin a logical transaction grouping multiple commands into one history entry.
        Supports nesting.
        """
        if self._transaction_depth == 0:
            self._active_transaction_name = name
            self._active_transaction_commands = []
        self._transaction_depth += 1

    def commit_transaction(self) -> bool:
        """
        Commit open transaction. If nesting depth reaches 0, records
        a TransactionCommand onto the history stack.
        """
        if self._transaction_depth <= 0:
            return False

        self._transaction_depth -= 1
        if self._transaction_depth == 0:
            name = self._active_transaction_name or "Transaction"
            cmds = self._active_transaction_commands
            self._active_transaction_commands = []
            self._active_transaction_name = ""

            if cmds:
                tx_cmd = TransactionCommand(name=name, commands=cmds)
                self.push(tx_cmd)
                return True
        return False

    def rollback_transaction(self) -> bool:
        """
        Roll back all operations in the active transaction in reverse order.
        Leaves no partial state behind.
        """
        if self._transaction_depth <= 0:
            return False

        cmds = list(self._active_transaction_commands)
        self._active_transaction_commands = []
        self._active_transaction_name = ""
        self._transaction_depth = 0

        for cmd in reversed(cmds):
            try:
                cmd.undo()
            except Exception as e:
                _logger.error(f"Rollback failed for child command {cmd.name}: {e}")

        self.history_changed.emit()
        return True

    @contextmanager
    def transaction(self, name: str = "Transaction"):
        """Context manager for nest-safe transaction grouping."""
        self.begin_transaction(name)
        try:
            yield
            self.commit_transaction()
        except Exception:
            self.rollback_transaction()
            raise
