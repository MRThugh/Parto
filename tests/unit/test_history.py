# tests/unit/test_history.py
"""
Unit Tests — Command History & Undo/Redo Engine
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from parto.history.commands import Command, SnapshotCommand
from parto.history.manager import HistoryManager, _CLEAN_MARKER


class CounterTarget:
    def __init__(self):
        self.value = 0

    def restore(self, state):
        self.value = state


class ConcreteTestCommand(Command):
    def __init__(self, name="Test Op"):
        super().__init__(name)
        self.executed = False

    def undo(self):
        self.executed = False

    def redo(self):
        self.executed = True


def test_command_base_class():
    """Verify Command class properties."""
    cmd = ConcreteTestCommand("Test Op")
    assert cmd.name == "Test Op"
    cmd.redo()
    assert cmd.executed is True
    cmd.undo()
    assert cmd.executed is False


def test_snapshot_command_lifecycle():
    """Verify SnapshotCommand restores before and after states."""
    target = CounterTarget()
    target.value = 10

    cmd = SnapshotCommand(
        name="Increment",
        target_object=target,
        restore_fn=target.restore,
        before_state=10,
        after_state=20,
    )

    # Undo restores before_state
    cmd.undo()
    assert target.value == 10

    # Redo restores after_state
    cmd.redo()
    assert target.value == 20


def test_history_manager_push_undo_redo():
    """Verify push, can_undo, can_redo, and stack boundary behavior."""
    mgr = HistoryManager(max_history=5)
    assert mgr.can_undo is False
    assert mgr.can_redo is False

    target = CounterTarget()
    c1 = SnapshotCommand("Op1", target, target.restore, 0, 1)
    c2 = SnapshotCommand("Op2", target, target.restore, 1, 2)

    mgr.push(c1)
    assert mgr.can_undo is True
    assert mgr.can_redo is False
    assert mgr.undo_description() == "Undo Op1"

    mgr.push(c2)
    assert mgr.undo_description() == "Undo Op2"

    # Undo c2
    assert mgr.undo() is True
    assert target.value == 1
    assert mgr.can_undo is True
    assert mgr.can_redo is True
    assert mgr.redo_description() == "Redo Op2"

    # Undo c1
    assert mgr.undo() is True
    assert target.value == 0
    assert mgr.can_undo is False
    assert mgr.can_redo is True

    # Redo c1
    assert mgr.redo() is True
    assert target.value == 1

    # Redo c2
    assert mgr.redo() is True
    assert target.value == 2
    assert mgr.can_redo is False


def test_history_manager_clears_redo_on_new_push():
    """Verify pushing a new command after undo clears the redo branch."""
    mgr = HistoryManager(max_history=5)
    target = CounterTarget()

    mgr.push(SnapshotCommand("Op1", target, target.restore, 0, 1))
    mgr.push(SnapshotCommand("Op2", target, target.restore, 1, 2))

    mgr.undo()
    assert mgr.can_redo is True

    # Push Op3 -> Redo branch must be cleared
    mgr.push(SnapshotCommand("Op3", target, target.restore, 1, 3))
    assert mgr.can_redo is False
    assert mgr.undo_description() == "Undo Op3"


def test_history_manager_capacity_trimming():
    """Verify older commands are pruned when exceeding max_history."""
    mgr = HistoryManager(max_history=3)
    target = CounterTarget()

    for i in range(5):
        mgr.push(SnapshotCommand(f"Op{i}", target, target.restore, i, i + 1))

    assert mgr.undo_count == 3
    assert mgr.undo_description() == "Undo Op4"

    # Can only undo 3 times
    assert mgr.undo() is True
    assert mgr.undo() is True
    assert mgr.undo() is True
    assert mgr.can_undo is False
