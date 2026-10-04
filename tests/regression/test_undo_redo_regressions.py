# tests/regression/test_undo_redo_regressions.py
"""
Regression Tests — Undo/Redo Robustness, Pixel Restoration & History Boundaries
Author & Maintainer: Ali Kamrani (علی کامرانی)

Validates:
1. Brush undo/redo exact byte-for-byte pixel restoration.
2. Stroke no-op suppression: clicks or strokes that modify no pixels push zero undo steps.
3. Saved-state robustness after history capacity trimming.
4. Boundary safety: calling undo/redo at stack ends is safe and returns False.
"""

import pytest
from PIL import Image
from PySide6.QtCore import QPointF

from parto.editor.document import Document
from parto.tools.brush import BrushTool
from parto.history.manager import HistoryManager
from parto.history.commands import Command


def test_brush_undo_exact_pixel_restoration():
    """Verify brush undo restores original pixel bytes identically."""
    doc = Document()
    doc.new_document(50, 50, (200, 200, 200, 255))
    layer = doc.active_layer
    assert layer is not None

    orig_bytes = layer.image.tobytes()

    tool = BrushTool()
    tool.set_size(10)
    tool.set_color((255, 0, 0, 255))
    tool.set_opacity(1.0)
    tool.set_hardness(1.0)

    # Stroke across canvas
    tool.start_stroke(QPointF(10, 25), doc)
    tool.continue_stroke(QPointF(25, 25), doc)
    tool.continue_stroke(QPointF(40, 25), doc)
    committed = tool.end_stroke(doc)
    assert committed is True

    # Image changed
    assert layer.image.tobytes() != orig_bytes
    assert doc.history.can_undo is True

    # Undo
    assert doc.undo() is True
    assert layer.image.tobytes() == orig_bytes


def test_brush_noop_stroke_detection():
    """Verify stroke that draws identical color over existing pixels pushes no history."""
    doc = Document()
    doc.new_document(50, 50, (0, 0, 255, 255))
    doc.set_modified(False)
    assert doc.modified is False
    assert doc.history.undo_count == 0

    tool = BrushTool()

    # Case 1: Fully transparent color
    tool.set_color((255, 0, 0, 0))
    tool.start_stroke(QPointF(25, 25), doc)
    tool.continue_stroke(QPointF(35, 35), doc)
    committed = tool.end_stroke(doc)
    assert committed is False
    assert doc.history.undo_count == 0
    assert doc.modified is False

    # Case 2: Opacity 0.0
    tool.set_color((255, 0, 0, 255))
    tool.set_opacity(0.0)
    tool.start_stroke(QPointF(25, 25), doc)
    committed = tool.end_stroke(doc)
    assert committed is False
    assert doc.history.undo_count == 0
    assert doc.modified is False


def test_saved_state_robustness_after_trimming():
    """Verify is_clean logic remains correct when history stack trimming evicts save points."""
    hm = HistoryManager(max_history=5)
    assert hm.is_clean is True

    class DummyCmd(Command):
        def __init__(self, name: str):
            super().__init__(name)
        def redo(self): pass
        def undo(self): pass

    # Push 2 commands and mark clean save point
    hm.execute(DummyCmd("c1"))
    hm.execute(DummyCmd("c2"))
    assert hm.is_clean is False
    hm.set_clean()
    assert hm.is_clean is True

    # Push 5 more commands (total 7, capacity 5 -> c1 and c2 are evicted!)
    for i in range(3, 8):
        hm.execute(DummyCmd(f"c{i}"))

    # The clean save point (c2) was evicted from undo stack
    assert hm.is_clean is False


def test_undo_redo_boundary_safety():
    """Verify calling undo/redo at boundary returns False and does not crash."""
    doc = Document()
    doc.new_document(20, 20)

    assert doc.undo() is False
    assert doc.redo() is False

    doc.rotate_document()
    assert doc.undo() is True
    assert doc.undo() is False  # At boundary

    assert doc.redo() is True
    assert doc.redo() is False  # At boundary
