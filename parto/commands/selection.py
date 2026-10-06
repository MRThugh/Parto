# parto/commands/selection.py
"""
Parto Architecture 2.0 — Selection Commands (Preparation)
Author: Ali Kamrani (MRThugh)

Reversible commands preparing the architecture for future Selection 2.0 subsystem.
Maintains selection mask / region state transitions.
"""

from __future__ import annotations
from typing import Optional, Any
from .base import Command


class SelectionCommand(Command):
    """Base class for reversible selection modifications."""

    def __init__(
        self,
        name: str = "Modify Selection",
        id: str = "selection.modify",
        description: str = "",
        before_state: Optional[Any] = None,
        after_state: Optional[Any] = None,
        target: Optional[Any] = None,
    ):
        super().__init__(name=name, id=id, description=description or name)
        self.before_state = before_state
        self.after_state = after_state
        self.target = target

    def execute(self) -> None:
        if self.target and hasattr(self.target, "set_selection"):
            self.target.set_selection(self.after_state)

    def redo(self) -> None:
        self.execute()

    def undo(self) -> None:
        if self.target and hasattr(self.target, "set_selection"):
            self.target.set_selection(self.before_state)


class SelectAllCommand(SelectionCommand):
    """Command that selects the entire canvas area."""

    def __init__(self, target: Optional[Any] = None, before_state: Optional[Any] = None):
        super().__init__(
            name="Select All",
            id="selection.select_all",
            description="Select entire canvas",
            before_state=before_state,
            after_state="all",
            target=target,
        )


class DeselectCommand(SelectionCommand):
    """Command that clears current selection."""

    def __init__(self, target: Optional[Any] = None, before_state: Optional[Any] = None):
        super().__init__(
            name="Deselect",
            id="selection.deselect",
            description="Deselect active selection",
            before_state=before_state,
            after_state=None,
            target=target,
        )


class InvertSelectionCommand(SelectionCommand):
    """Command that inverts current selection."""

    def __init__(self, target: Optional[Any] = None, before_state: Optional[Any] = None):
        super().__init__(
            name="Invert Selection",
            id="selection.invert",
            description="Invert current selection bounds",
            before_state=before_state,
            after_state="inverted",
            target=target,
        )
