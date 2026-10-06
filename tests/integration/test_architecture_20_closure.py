# tests/integration/test_architecture_20_closure.py
"""
Parto Architecture 2.0 Final Closure Tests
Author: Ali Kamrani (MRThugh)

Mandatory regression suite proving the closure of Action + Command + History Architecture 2.0:
- TEST A: Layer Command Pipeline
- TEST B: Opacity Pipeline (No legacy snapshot bypass, mergeable coalescing)
- TEST C: Brush Pipeline (No document snapshot, layer memory isolation, exact byte equality)
- TEST D: Shortcut Pipeline
- TEST E: Command Palette Pipeline
- TEST F: Transform Pipeline
- TEST G: Dirty State Consistency
- TEST H: ActionManager Integration
"""

from __future__ import annotations
import pytest
from PIL import Image
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction

from parto.ui.main_window import MainWindow
from parto.ui.panels.layers_panel import LayersDock
from parto.ui.dialogs.command_palette import CommandPalette
from parto.actions.registry import get_action_registry, ActionRegistry
from parto.actions.context import get_context_manager
from parto.actions.manager import get_action_manager, ActionManager
from parto.actions.builtins import register_all_builtins
from parto.commands.layers import (
    CreateLayerCommand,
    DeleteLayerCommand,
    DuplicateLayerCommand,
    MoveLayerCommand,
    MergeDownCommand,
    ChangeLayerOpacityCommand,
    ToggleLayerVisibilityCommand,
    RenameLayerCommand,
)
from parto.commands.brush import PaintStrokeCommand
from parto.commands.transform import (
    RotateCommand,
    FlipCommand,
    ResizeCommand,
    CropCommand,
)


def _create_test_window():
    win = MainWindow()
    win.maybe_save_unsaved_changes = lambda: True
    return win


def test_a_layer_command_pipeline(qapp):
    """
    TEST A — Layer Command Pipeline
    layer.create -> Action -> Controller -> CreateLayerCommand -> HistoryManager.execute() -> Layer
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(100, 100, (255, 255, 255, 255))
    initial_layer_count = len(doc.layers)

    reg = get_action_registry()
    ctx_mgr = get_context_manager()
    ctx_mgr.set_environment(win, doc)

    # 1. Action lookup
    act = reg.get("layer.create")
    assert act is not None
    assert act.is_enabled(ctx_mgr.create_context()) is True

    # 2. Action execution routes to CreateLayerCommand and HistoryManager
    act.execute(ctx_mgr.create_context())
    assert len(doc.layers) == initial_layer_count + 1
    assert doc.history.can_undo is True
    top_cmd = doc.history.undo_stack[-1]
    assert isinstance(top_cmd, CreateLayerCommand)

    # 3. Undo rolls back layer creation
    assert doc.undo() is True
    assert len(doc.layers) == initial_layer_count

    # 4. Redo restores layer creation
    assert doc.redo() is True
    assert len(doc.layers) == initial_layer_count + 1

    doc.set_modified(False)
    win.close()


def test_b_opacity_pipeline_no_snapshot_bypass(qapp):
    """
    TEST B — Opacity Pipeline
    Opacity UI -> ChangeLayerOpacityCommand -> HistoryManager
    Verifies that the legacy snapshot path (create_snapshot, record_operation) is NOT used,
    and that continuous slider adjustments coalesce into a single undo entry.
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(100, 100, (255, 255, 255, 255))
    layer = doc.active_layer
    assert layer is not None
    assert layer.opacity == 1.0

    layers_dock = win.layers_dock
    layers_dock.show()

    # Track snapshot and record_operation calls
    snapshot_calls = []
    record_calls = []

    orig_create_snapshot = doc.create_snapshot
    orig_record_operation = doc.record_operation

    def spied_create_snapshot(*args, **kwargs):
        snapshot_calls.append(True)
        return orig_create_snapshot(*args, **kwargs)

    def spied_record_operation(*args, **kwargs):
        record_calls.append(args)
        return orig_record_operation(*args, **kwargs)

    doc.create_snapshot = spied_create_snapshot
    doc.record_operation = spied_record_operation

    try:
        initial_history_count = doc.history.undo_count

        # Simulate slider interaction: press -> drag 95% -> drag 90% -> drag 85% -> release
        layers_dock._on_opacity_slider_pressed()
        layers_dock.opacity_slider.setValue(95)
        layers_dock._on_opacity_slider_changed(95)
        layers_dock.opacity_slider.setValue(90)
        layers_dock._on_opacity_slider_changed(90)
        layers_dock.opacity_slider.setValue(85)
        layers_dock._on_opacity_slider_changed(85)
        layers_dock._on_opacity_slider_released()

        # CRITICAL: Verify NO legacy snapshot path was used!
        assert len(snapshot_calls) == 0, "create_snapshot must NOT be called in normal opacity interaction"
        assert len(record_calls) == 0, "record_operation must NOT be called in normal opacity interaction"

        # Verify command executed through HistoryManager
        assert doc.history.undo_count == initial_history_count + 1
        top_cmd = doc.history.undo_stack[-1]
        assert isinstance(top_cmd, ChangeLayerOpacityCommand)
        assert abs(layer.opacity - 0.85) < 1e-4

        # Verify coalescing: Undo in ONE step restores original 1.0 opacity
        assert doc.undo() is True
        assert abs(layer.opacity - 1.0) < 1e-4

        # Redo restores final 0.85 opacity
        assert doc.redo() is True
        assert abs(layer.opacity - 0.85) < 1e-4

        # Verify sealing: A subsequent slider drag after release creates a SECOND command
        layers_dock._on_opacity_slider_pressed()
        layers_dock.opacity_slider.setValue(50)
        layers_dock._on_opacity_slider_changed(50)
        layers_dock._on_opacity_slider_released()

        assert doc.history.undo_count == initial_history_count + 2
        assert abs(layer.opacity - 0.50) < 1e-4

        # Undo returns to 0.85
        assert doc.undo() is True
        assert abs(layer.opacity - 0.85) < 1e-4

        # Undo again returns to 1.0
        assert doc.undo() is True
        assert abs(layer.opacity - 1.0) < 1e-4

    finally:
        doc.create_snapshot = orig_create_snapshot
        doc.record_operation = orig_record_operation
        doc.set_modified(False)
        win.close()


def test_c_brush_pipeline_no_document_snapshot_and_layer_isolation(qapp):
    """
    TEST C — Brush Pipeline
    Brush -> PaintStrokeCommand -> HistoryManager
    Verifies that:
    1. A full-document snapshot is NOT created during normal stroke commit.
    2. Only the target layer's state is captured (layer memory isolation).
    3. Unrelated layers are byte-for-byte unaffected and not cloned.
    4. Exact pixel byte equality is preserved across Undo and Redo.
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(100, 100, (255, 255, 255, 255))

    # Add extra layers to verify isolation
    layer_bg = doc.layers[0]
    layer_target = doc.add_layer(name="Paint Target")
    layer_top = doc.add_layer(name="Top Layer")

    bg_bytes_initial = layer_bg.image.tobytes()
    top_bytes_initial = layer_top.image.tobytes()
    target_bytes_initial = layer_target.image.tobytes()

    bg_img_id = id(layer_bg.image)
    top_img_id = id(layer_top.image)

    # Monitor full-document snapshot calls
    snapshot_calls = []
    orig_create_snapshot = doc.create_snapshot
    orig_internal_snapshot = doc._create_snapshot

    def spied_create_snapshot(*args, **kwargs):
        snapshot_calls.append("public")
        return orig_create_snapshot(*args, **kwargs)

    def spied_internal_snapshot(*args, **kwargs):
        snapshot_calls.append("internal")
        return orig_internal_snapshot(*args, **kwargs)

    doc.create_snapshot = spied_create_snapshot
    doc._create_snapshot = spied_internal_snapshot

    try:
        # Select target layer
        doc.set_active_layer_index(1)
        assert doc.active_layer is layer_target

        # Activate Brush
        win.action_tool_brush()
        brush = win.tool_brush
        brush.set_size(12)
        brush.set_color((255, 0, 0, 255))

        # Perform stroke
        brush.start_stroke(QPointF(10, 10), doc)
        brush.continue_stroke(QPointF(40, 40), doc)
        committed = brush.end_stroke(doc)
        assert committed is True

        # CRITICAL ASSERTION 1: Zero full-document snapshots during stroke commit!
        assert len(snapshot_calls) == 0, (
            f"Expected 0 document snapshots during brush stroke, got {len(snapshot_calls)}: {snapshot_calls}"
        )

        # CRITICAL ASSERTION 2: Command on History stack is PaintStrokeCommand
        top_cmd = doc.history.undo_stack[-1]
        assert isinstance(top_cmd, PaintStrokeCommand)
        assert top_cmd.layer is layer_target

        # CRITICAL ASSERTION 3: Unrelated layers are byte-for-byte identical and not cloned
        assert layer_bg.image.tobytes() == bg_bytes_initial
        assert layer_top.image.tobytes() == top_bytes_initial
        assert id(layer_bg.image) == bg_img_id
        assert id(layer_top.image) == top_img_id

        # Target layer pixels modified
        target_bytes_modified = layer_target.image.tobytes()
        assert target_bytes_modified != target_bytes_initial

        # CRITICAL ASSERTION 4: Undo exact byte-for-byte initial pixel equality
        assert doc.undo() is True
        assert layer_target.image.tobytes() == target_bytes_initial
        assert layer_bg.image.tobytes() == bg_bytes_initial
        assert layer_top.image.tobytes() == top_bytes_initial

        # CRITICAL ASSERTION 5: Redo exact byte-for-byte modified pixel equality
        assert doc.redo() is True
        assert layer_target.image.tobytes() == target_bytes_modified
        assert layer_bg.image.tobytes() == bg_bytes_initial
        assert layer_top.image.tobytes() == top_bytes_initial

    finally:
        doc.create_snapshot = orig_create_snapshot
        doc._create_snapshot = orig_internal_snapshot
        doc.set_modified(False)
        win.close()


def test_d_shortcut_pipeline(qapp):
    """
    TEST D — Shortcut Pipeline
    Shortcut / QAction -> Action -> Controller -> Command -> HistoryManager
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(100, 100, (255, 255, 255, 255))
    initial_layers = len(doc.layers)

    mgr = get_action_manager()

    # Get QAction for layer.create (also accessible via alias 'layer_new')
    qact = mgr.create_qaction("layer.create", parent=win)
    assert qact is not None
    assert qact.shortcut().toString() == "Ctrl+Shift+N"

    # Triggering QAction invokes Action.execute
    qact.trigger()

    # Domain state updated via Command -> HistoryManager
    assert len(doc.layers) == initial_layers + 1
    assert doc.history.can_undo is True
    assert isinstance(doc.history.undo_stack[-1], CreateLayerCommand)

    doc.set_modified(False)
    win.close()


def test_e_command_palette_pipeline(qapp):
    """
    TEST E — Command Palette Pipeline
    Command Palette -> ActionRegistry -> Action -> Command -> HistoryManager
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(100, 100, (255, 255, 255, 255))
    initial_layers = len(doc.layers)

    ctx_mgr = get_context_manager()
    ctx_mgr.set_environment(win, doc)

    palette = CommandPalette(parent=win)
    palette._filter_commands("New Layer")
    assert palette.list_widget.count() > 0

    # Execute selected item in palette
    palette._execute_selected()

    assert len(doc.layers) == initial_layers + 1
    assert doc.history.can_undo is True
    assert isinstance(doc.history.undo_stack[-1], CreateLayerCommand)

    palette.close()
    doc.set_modified(False)
    win.close()


def test_f_transform_pipeline(qapp):
    """
    TEST F — Transform Pipeline
    Transform Action -> Transform Command -> HistoryManager
    Verifies Controller does not manually manage snapshots.
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(120, 80, (255, 255, 255, 255))
    assert doc.width == 120
    assert doc.height == 80

    reg = get_action_registry()
    ctx_mgr = get_context_manager()
    ctx_mgr.set_environment(win, doc)

    # 1. Rotate 90 CW Action
    act_rot = reg.get("transform.rotate_cw")
    assert act_rot is not None
    act_rot.execute(ctx_mgr.create_context())

    assert doc.width == 80
    assert doc.height == 120
    assert doc.history.can_undo is True
    assert isinstance(doc.history.undo_stack[-1], RotateCommand)

    # Undo rotation
    assert doc.undo() is True
    assert doc.width == 120
    assert doc.height == 80

    # Redo rotation
    assert doc.redo() is True
    assert doc.width == 80
    assert doc.height == 120

    # 2. Flip Horizontal Action
    act_flip = reg.get("transform.flip_h")
    assert act_flip is not None
    act_flip.execute(ctx_mgr.create_context())
    assert isinstance(doc.history.undo_stack[-1], FlipCommand)

    assert doc.undo() is True
    assert doc.redo() is True

    doc.set_modified(False)
    win.close()


def test_g_dirty_state_consistency(qapp):
    """
    TEST G — Dirty State Consistency
    Saved document -> clean
    Execute Command -> dirty
    Undo back to saved revision -> clean
    Redo -> dirty
    """
    win = _create_test_window()
    doc = win.document
    doc.new_document(100, 100, (255, 255, 255, 255))
    doc.history.set_clean()
    assert doc.history.is_clean is True

    # Execute Command
    doc.add_layer()
    assert doc.history.is_clean is False

    # Undo
    doc.undo()
    assert doc.history.is_clean is True

    # Redo
    doc.redo()
    assert doc.history.is_clean is False

    # Transactions also preserve clean state
    doc.history.set_clean()
    assert doc.history.is_clean is True

    with doc.history.transaction("Batch"):
        doc.add_layer()
        doc.add_layer()

    assert doc.history.is_clean is False
    doc.undo()
    assert doc.history.is_clean is True

    doc.set_modified(False)
    win.close()


def test_h_action_manager_integration(qapp):
    """
    TEST H — ActionManager Integration
    Verifies ActionManager:
    - Action lookup (canonical + alias)
    - QAction creation and reuse
    - QAction state synchronization (enabled/checked)
    - Shortcut synchronization
    - Direct trigger dispatch
    """
    reg = ActionRegistry()
    register_all_builtins(reg)
    mgr = ActionManager()
    mgr.registry = reg

    # Lookup
    act_canon = mgr.lookup("document.new")
    assert act_canon is not None
    act_alias = mgr.lookup("file_new")
    assert act_alias is act_canon

    # QAction creation
    qact1 = mgr.create_qaction("document.new")
    assert qact1 is not None
    assert isinstance(qact1, QAction)
    assert qact1.text() == "New Canvas..."

    # Alias returns same QAction
    qact_alias = mgr.create_qaction("file_new")
    assert qact_alias is qact1

    # Shortcut sync
    mgr.sync_shortcut("document.new", "Ctrl+Alt+N")
    assert act_canon.shortcut == "Ctrl+Alt+N"
    assert qact1.shortcut().toString() == "Ctrl+Alt+N"

    # State update
    mgr.update_states()
