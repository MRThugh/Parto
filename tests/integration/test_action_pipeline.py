# tests/integration/test_action_pipeline.py
"""
Integration Tests — Action + Command + History Architecture 2.0 Pipeline
Author: Ali Kamrani (MRThugh)
Validates the complete interaction chain:
UI Action -> Controller / Command -> Domain State -> History Tracking -> Undo/Redo.
"""

import pytest
from PIL import Image
from parto.ui.main_window import MainWindow
from parto.actions.registry import get_action_registry
from parto.actions.context import get_context_manager
from parto.commands.layers import CreateLayerCommand
from parto.commands.brush import PaintStrokeCommand


def test_action_to_command_to_history_pipeline(qapp):
    """
    Verify complete architectural pipeline:
    1. UI triggers Action
    2. Action coordinates Command
    3. Command modifies Domain
    4. HistoryManager tracks command for Undo/Redo
    """
    win = MainWindow()
    doc = win.document
    doc.new_document(120, 80, (255, 255, 255, 255))
    reg = get_action_registry()
    ctx_mgr = get_context_manager()
    ctx_mgr.set_environment(win, doc)

    # 1. Action: layer.create
    action_create_layer = reg.get("layer.create")
    assert action_create_layer is not None
    assert action_create_layer.is_enabled(ctx_mgr.create_context()) is True

    # Execute action
    action_create_layer.execute(ctx_mgr.create_context())
    assert len(doc.layers) == 2
    assert doc.history.can_undo is True

    # 2. Action: history.undo
    action_undo = reg.get("history.undo")
    assert action_undo is not None
    action_undo.execute(ctx_mgr.create_context())
    assert len(doc.layers) == 1

    # 3. Action: history.redo
    action_redo = reg.get("history.redo")
    assert action_redo is not None
    action_redo.execute(ctx_mgr.create_context())
    assert len(doc.layers) == 2

    doc.set_modified(False)
    win.close()


def test_brush_painting_to_command_history_pipeline(qapp):
    """
    Verify brush painting executes PaintStrokeCommand and commits to HistoryManager cleanly.
    """
    win = MainWindow()
    doc = win.document
    doc.new_document(100, 100, (200, 200, 200, 255))
    layer = doc.active_layer

    initial_bytes = layer.image.tobytes()

    # Activate brush tool
    win.action_tool_brush()
    brush = win.tool_brush
    brush.set_size(15)
    brush.set_color((255, 0, 0, 255))

    from PySide6.QtCore import QPointF
    brush.start_stroke(QPointF(10, 10), doc)
    brush.continue_stroke(QPointF(50, 50), doc)
    committed = brush.end_stroke(doc)
    assert committed is True

    # Domain state changed
    stroked_bytes = layer.image.tobytes()
    assert stroked_bytes != initial_bytes
    assert doc.history.can_undo is True

    # Undo
    assert doc.undo() is True
    assert layer.image.tobytes() == initial_bytes

    # Redo
    assert doc.redo() is True
    assert layer.image.tobytes() == stroked_bytes

    doc.set_modified(False)
    win.close()
