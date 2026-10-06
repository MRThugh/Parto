# parto/commands/base.py
"""
Parto Architecture 2.0 — Base Command System
Author: Ali Kamrani (MRThugh)

Provides the core abstract base class for reversible, atomic domain operations.
Defines execution, rollback (undo), re-application (redo), input validation,
and command coalescing (merging).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Any


class Command(ABC):
    """
    Abstract base class for all reversible operations in Parto.

    Invariants:
    - Performs one logical domain operation.
    - Knows how to execute, undo, and redo itself.
    - Validates inputs before execution via can_execute().
    - Never manipulates UI widgets or depends on GUI layout.
    - Supports command merging via can_merge() and merge_with().
    """

    def __init__(self, name: str = "Action", id: str = "", description: str = ""):
        self.name: str = name
        self.id: str = id or name.lower().replace(" ", "_")
        self.description: str = description or name
        self._revision: int = 0

    def execute(self) -> None:
        """
        Execute domain operation.
        Default implementation delegates to redo() for backward compatibility.
        """
        self.redo()

    @abstractmethod
    def undo(self) -> None:
        """Roll back the domain operation to the prior state."""
        pass

    @abstractmethod
    def redo(self) -> None:
        """Re-apply the domain operation."""
        pass

    def can_execute(self) -> bool:
        """
        Validate domain preconditions before execution.
        Returns True if the command is safe to execute, False otherwise.
        """
        return True

    def can_merge(self, other: Command) -> bool:
        """
        Determine if another command can be merged into this one.
        Override in subclasses that support coalescing (e.g., slider adjustments).
        """
        return False

    def merge_with(self, other: Command) -> bool:
        """
        Merge state from an incoming command into this command.
        Returns True if merge succeeded, False otherwise.
        """
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r} id={self.id!r}>"


class MergeableCommand(Command):
    """
    Base class for commands that naturally coalesce consecutive changes
    (e.g., continuous slider drags, opacity changes, property adjustments).
    """

    def __init__(self, name: str = "Adjustment", id: str = "", description: str = ""):
        super().__init__(name=name, id=id, description=description)
        self.merge_count: int = 1
