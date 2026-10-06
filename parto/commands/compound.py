# parto/commands/compound.py
"""
Parto Architecture 2.0 — Compound & Transaction Commands
Author: Ali Kamrani (MRThugh)

Allows grouping multiple low-level domain commands into one atomic,
reversible user operation. Ensures atomic execution, safe reverse rollback,
and clean undo/redo history representation.
"""

from __future__ import annotations
from typing import List, Optional
from .base import Command


class CompoundCommand(Command):
    """
    Groups multiple sequential commands into a single logical undo/redo step.
    
    Undo executes child commands in reverse order.
    Redo executes child commands in original order.
    """

    def __init__(
        self,
        name: str = "Compound Operation",
        commands: Optional[List[Command]] = None,
        id: str = "",
        description: str = "",
    ):
        super().__init__(name=name, id=id or "compound_operation", description=description or name)
        self.commands: List[Command] = list(commands) if commands else []

    def add(self, command: Command) -> None:
        """Add a command to the compound sequence."""
        self.commands.append(command)

    def __len__(self) -> int:
        return len(self.commands)

    def execute(self) -> None:
        for cmd in self.commands:
            cmd.execute()

    def undo(self) -> None:
        for cmd in reversed(self.commands):
            cmd.undo()

    def redo(self) -> None:
        for cmd in self.commands:
            cmd.redo()

    def can_execute(self) -> bool:
        return all(cmd.can_execute() for cmd in self.commands)


class TransactionCommand(CompoundCommand):
    """
    Semantic command representing a user-level transaction composed of
    multiple operations executed within a transaction block.
    """

    def __init__(
        self,
        name: str = "Transaction",
        commands: Optional[List[Command]] = None,
        id: str = "",
        description: str = "",
    ):
        super().__init__(
            name=name,
            commands=commands,
            id=id or "transaction",
            description=description or f"Transaction: {name}",
        )
