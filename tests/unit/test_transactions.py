# tests/unit/test_transactions.py
"""
Unit Tests — History Architecture 2.0 & Transactions
Author: Ali Kamrani (MRThugh)
Validates transaction grouping, nested transactions, safe exception rollback,
and history coalescing.
"""

import pytest
from parto.editor.document import Document
from parto.commands.base import Command
from parto.commands.compound import CompoundCommand, TransactionCommand


class ValueTarget:
    def __init__(self, val=0):
        self.val = val


class SetValueCommand(Command):
    def __init__(self, target: ValueTarget, old_val: int, new_val: int, name: str = "Set Val"):
        super().__init__(name=name)
        self.target = target
        self.old_val = old_val
        self.new_val = new_val

    def execute(self):
        self.target.val = self.new_val

    def undo(self):
        self.target.val = self.old_val

    def redo(self):
        self.target.val = self.new_val


def test_transaction_grouping_and_undo():
    """Verify multiple operations executed within a transaction undo in one step."""
    doc = Document()
    history = doc.history
    target = ValueTarget(0)

    history.begin_transaction("Multi Step Operation")
    history.execute(SetValueCommand(target, 0, 10, "Step 1"))
    assert target.val == 10
    history.execute(SetValueCommand(target, 10, 20, "Step 2"))
    assert target.val == 20
    committed = history.commit_transaction()
    assert committed is True

    # Shows as 1 entry in history
    assert history.undo_count == 1
    assert history.undo_description() == "Undo Multi Step Operation"

    # Single undo rolls back both steps
    assert history.undo() is True
    assert target.val == 0
    assert history.can_undo is False
    assert history.can_redo is True

    # Single redo re-applies both steps
    assert history.redo() is True
    assert target.val == 20


def test_transaction_context_manager():
    """Verify 'with history.transaction()' grouping."""
    doc = Document()
    history = doc.history
    target = ValueTarget(100)

    with history.transaction("Batch Update"):
        history.execute(SetValueCommand(target, 100, 200))
        history.execute(SetValueCommand(target, 200, 300))

    assert target.val == 300
    assert history.undo_count == 1

    history.undo()
    assert target.val == 100


def test_transaction_exception_safe_rollback():
    """Verify an exception raised inside a transaction safely rolls back prior steps."""
    doc = Document()
    history = doc.history
    target = ValueTarget(5)

    with pytest.raises(RuntimeError, match="Simulated Error"):
        with history.transaction("Failing Operation"):
            history.execute(SetValueCommand(target, 5, 50))
            assert target.val == 50
            raise RuntimeError("Simulated Error")

    # Target must be restored to initial value, and history stack must remain empty
    assert target.val == 5
    assert history.undo_count == 0
    assert history.is_in_transaction is False


def test_nested_transactions():
    """Verify nested transactions execute and commit cleanly at outer boundary."""
    doc = Document()
    history = doc.history
    target = ValueTarget(0)

    history.begin_transaction("Outer")
    history.execute(SetValueCommand(target, 0, 1))

    # Inner transaction
    history.begin_transaction("Inner")
    history.execute(SetValueCommand(target, 1, 2))
    history.commit_transaction()  # Decrements depth, doesn't commit to stack yet

    assert history.undo_count == 0
    assert target.val == 2

    # Commit outer
    history.commit_transaction()
    assert history.undo_count == 1
    assert history.undo_description() == "Undo Outer"

    # Undo
    history.undo()
    assert target.val == 0
