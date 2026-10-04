# tests/ui/test_shortcuts.py
"""
UI Tests — Centralized Shortcut Registry & Conflict Resolution
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PySide6.QtGui import QAction

from parto.shortcuts.manager import ShortcutManager, get_shortcut_manager
from parto.ui.main_window import MainWindow


def test_shortcut_manager_no_application_conflicts(qapp):
    """
    Verify the full MainWindow action setup has ZERO unresolved keyboard shortcut conflicts.
    """
    sm = get_shortcut_manager()
    win = MainWindow()

    conflicts = sm.find_conflicts()
    assert len(conflicts) == 0, f"Detected shortcut collisions: {conflicts}"

    win.close()


def test_shortcut_conflict_detection_policies():
    """Verify track, override, and reject conflict policies."""
    # 1. Track policy (default)
    mgr = ShortcutManager(default_policy="track")
    mgr.register("act1", "Action 1", "Cat", "Ctrl+Z", "Desc 1")
    mgr.register("act2", "Action 2", "Cat", "Ctrl+Z", "Desc 2")

    conflicts = mgr.find_conflicts()
    assert "ctrl+z" in conflicts
    assert len(conflicts["ctrl+z"]) == 2

    # 2. Reject policy
    mgr_strict = ShortcutManager(default_policy="reject")
    mgr_strict.register("act1", "Action 1", "Cat", "Ctrl+S", "Desc")
    with pytest.raises(ValueError, match="Shortcut conflict"):
        mgr_strict.register("act2", "Action 2", "Cat", "Ctrl+S", "Desc")

    # 3. Override policy
    mgr_override = ShortcutManager(default_policy="override")
    mgr_override.register("act1", "Action 1", "Cat", "Ctrl+O", "Desc 1")
    mgr_override.register("act2", "Action 2", "Cat", "Ctrl+O", "Desc 2")
    # act1 should have key cleared
    assert mgr_override.get("act1").key_sequence == ""
    assert mgr_override.get("act2").key_sequence == "Ctrl+O"
