# test_parto_v03_stabilization.py
"""
Parto v0.3.0 - Comprehensive Stabilization & Regression Test Suite
Validates:
1. Brush undo/redo exact pixel restoration.
2. Programmatic and mouse stroke lifecycle symmetry.
3. Strict pixel-level no-op stroke detection.
4. Decoupled Brush architecture (BrushSettings, BrushRenderer, StrokeController).
5. Saved-state robustness under history stack trimming.
6. ShortcutManager deterministic conflict resolution.
7. BrushBar preview widget and ergonomic controls.
8. Pixel-accurate layer merge-down operations.
"""

import pytest
import numpy as np
from PIL import Image
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QAction

from parto.editor.document import Document
from parto.tools.brush import BrushTool, BrushSettings, BrushRenderer, StrokeController
from parto.history.manager import HistoryManager, _CLEAN_MARKER
from parto.history.commands import Command
from parto.shortcuts.manager import ShortcutManager
from parto.ui.widgets.brush_bar import BrushBar, BrushPreviewWidget


def test_brush_undo_exact_pixel_restoration():
    """Verify brush undo restores the exact original pixel values before the first modification."""
    doc = Document()
    doc.new_document(100, 100, (240, 200, 180, 255))
    layer = doc.active_layer
    assert layer is not None

    # Snapshot original layer pixel bytes
    original_bytes = layer.image.tobytes()
    original_composite = doc.get_composite().tobytes()

    tool = BrushTool()
    tool.set_size(20)
    tool.set_color((20, 50, 220, 255))
    tool.set_opacity(1.0)
    tool.set_hardness(0.9)

    # Execute a stroke across the center
    tool.start_stroke(QPointF(20, 50), doc)
    tool.continue_stroke(QPointF(50, 50), doc)
    tool.continue_stroke(QPointF(80, 50), doc)
    committed = tool.end_stroke(doc)
    assert committed is True

    # Pixels must have changed
    stroked_bytes = layer.image.tobytes()
    assert stroked_bytes != original_bytes
    assert doc.history.can_undo is True
    assert doc.modified is True

    # Undo must restore EXACT original pixel buffer
    assert doc.undo() is True
    undone_bytes = layer.image.tobytes()
    assert undone_bytes == original_bytes
    assert doc.get_composite().tobytes() == original_composite

    # Redo must restore EXACT stroked pixel buffer
    assert doc.redo() is True
    redone_bytes = layer.image.tobytes()
    assert redone_bytes == stroked_bytes


def test_programmatic_stroke_lifecycle_and_cancellation():
    """Verify programmatic stroke sequences with cancellation and layer targeting."""
    doc = Document()
    doc.new_document(64, 64, (255, 255, 255, 255))
    layer = doc.active_layer
    baseline_bytes = layer.image.tobytes()

    tool = BrushTool()
    tool.set_size(10)
    tool.set_color((255, 0, 0, 255))

    # Stroke started and cancelled mid-way
    tool.start_stroke(QPointF(10, 10), layer, doc=doc)
    tool.continue_stroke(QPointF(20, 20), layer)
    assert layer.image.tobytes() != baseline_bytes

    tool.cancel_stroke(doc=doc)
    assert layer.image.tobytes() == baseline_bytes
    assert doc.history.can_undo is False

    # Now complete a stroke targeting layer directly with doc parameter
    tool.start_stroke(QPointF(10, 10), layer, doc=doc)
    tool.continue_stroke(QPointF(30, 30), layer)
    committed = tool.end_stroke(doc)
    assert committed is True
    assert doc.history.can_undo is True

    # Undo restores baseline
    doc.undo()
    assert layer.image.tobytes() == baseline_bytes


def test_brush_noop_stroke_detection():
    """Verify strokes that do not modify pixels are cleanly discarded without history pollution."""
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

    # Case 3: Completely outside image boundaries
    tool.set_opacity(1.0)
    tool.set_size(10)
    tool.start_stroke(QPointF(-100, -100), doc)
    tool.continue_stroke(QPointF(-80, -80), doc)
    committed = tool.end_stroke(doc)
    assert committed is False
    assert doc.history.undo_count == 0
    assert doc.modified is False

    # Case 4: Drawing identical color over existing identical pixels
    # Target image is pure blue (0, 0, 255, 255)
    tool.set_color((0, 0, 255, 255))
    tool.set_opacity(1.0)
    tool.set_hardness(1.0)
    tool.start_stroke(QPointF(25, 25), doc)
    tool.continue_stroke(QPointF(30, 30), doc)
    committed = tool.end_stroke(doc)
    # Target pixels did not change because blue was stamped over blue
    assert committed is False
    assert doc.history.undo_count == 0
    assert doc.modified is False


def test_brush_architecture_decoupling():
    """Verify BrushSettings, BrushRenderer, and StrokeController work cohesively and independently."""
    settings = BrushSettings(size=12, opacity=0.75, hardness=0.6, color=(10, 20, 30, 255))
    assert settings.size == 12
    assert settings.radius == 6
    settings.increase_size(4)
    assert settings.size == 16
    assert settings.radius == 8
    settings.decrease_size(2)
    assert settings.size == 14

    settings.swap_colors()
    assert settings.color == (255, 255, 255, 255)
    assert settings.background_color == (10, 20, 30, 255)
    settings.reset_default_colors()
    assert settings.color == (0, 0, 0, 255)

    renderer = BrushRenderer()
    dab = renderer.get_dab(settings)
    assert dab.mode == "RGBA"
    assert dab.width == settings.size
    assert dab.height == settings.size

    # Cache hit
    dab2 = renderer.get_dab(settings)
    assert dab is dab2

    # Invalidate cache
    renderer.invalidate_cache()
    assert renderer._cached_dab is None

    # Stamping on target image
    target = Image.new("RGBA", (40, 40), (0, 0, 0, 0))
    stamped = renderer.render_segment(target, settings, 10, 10, 30, 30)
    assert stamped is True
    # Non-zero alpha must exist in stamped region
    arr = np.array(target)
    assert arr[:, :, 3].max() > 0


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

    # Undo all the way to empty
    while hm.can_undo:
        hm.undo()

    # Even when stack is emptied, is_clean MUST remain False because clean state was lost
    assert hm.is_clean is False

    # A new save updates clean marker
    hm.set_clean()
    assert hm.is_clean is True


def test_shortcut_manager_deterministic_resolution(qapp):
    """Verify deterministic shortcut conflict handling and resolution policies."""
    sm = ShortcutManager(default_policy="track")

    a1 = QAction("Open")
    a2 = QAction("Options")
    sm.register("open", "Open", "File", "Ctrl+O", "Open file", action=a1)
    sm.register("options", "Options", "Tools", "Ctrl+O", "App options", action=a2)

    # Track policy registers both and detects collision
    conflicts = sm.find_conflicts()
    assert "ctrl+o" in conflicts
    assert set(conflicts["ctrl+o"]) == {"open", "options"}

    # Deterministic resolve: keep 'open', unbind 'options'
    assert sm.resolve_conflict("Ctrl+O", "open") is True
    assert len(sm.find_conflicts()) == 0
    assert sm.get("options").key_sequence == ""
    assert a2.shortcut().toString() == ""

    # Override policy: automatically strips collision
    a3 = QAction("Other")
    sm.register("other", "Other", "Edit", "Ctrl+O", "Other", action=a3, policy="override")
    assert sm.get("other").key_sequence == "Ctrl+O"
    assert sm.get("open").key_sequence == ""
    assert len(sm.find_conflicts()) == 0
    assert sm.assert_no_conflicts() is True

    # Reject policy: raises ValueError
    with pytest.raises(ValueError, match="Shortcut conflict"):
        sm.register("forbidden", "Forbidden", "Edit", "Ctrl+O", "Forbidden", policy="reject")


def test_brush_bar_preview_and_controls(qapp):
    """Verify BrushBar real-time preview widget, compact layout, and signal synchronization."""
    bar = BrushBar()
    assert isinstance(bar.preview, BrushPreviewWidget)

    # Check initial values
    assert bar.slider_size.value() == 8
    assert bar.slider_hardness.value() == 80
    assert bar.slider_opacity.value() == 100

    # Changing controls updates preview widget
    bar.slider_size.setValue(36)
    assert bar.preview._size == 36

    bar.slider_opacity.setValue(50)
    assert abs(bar.preview._opacity - 0.5) < 0.01

    bar.slider_hardness.setValue(25)
    assert abs(bar.preview._hardness - 0.25) < 0.01

    bar.set_color((255, 128, 0, 255))
    assert bar.preview._color == (255, 128, 0, 255)

    # Swap and Reset buttons
    bar.swap_btn.click()
    assert bar.preview._color == (255, 255, 255, 255)

    bar.reset_btn.click()
    assert bar.preview._color == (0, 0, 0, 255)


def test_merge_down_pixel_compositing():
    """Verify merge down operation correctly blends layers with offsets and opacity."""
    doc = Document()
    doc.new_document(100, 100, (0, 0, 0, 0))

    # Layer 1: Solid blue square at (0, 0)
    lay1 = doc.active_layer
    lay1.name = "Background"
    img1 = Image.new("RGBA", (100, 100), (0, 0, 255, 255))
    lay1.image = img1

    # Layer 2: Red rectangle at offset (20, 20) with 50% opacity
    lay2 = doc.add_layer("Foreground", (255, 0, 0, 255))
    assert lay2 is not None
    img2 = Image.new("RGBA", (50, 50), (255, 0, 0, 255))
    lay2.image = img2
    lay2.offset_x = 20
    lay2.offset_y = 20
    lay2.opacity = 0.5

    # Target composite before merge
    pre_composite = doc.get_composite().copy()

    # Perform merge down
    success = doc.merge_down()
    assert success is True
    assert len(doc.layers) == 1
    post_composite = doc.get_composite()

    # The visual composite must match before and after merge down
    diff = np.max(np.abs(np.array(pre_composite, dtype=int) - np.array(post_composite, dtype=int)))
    assert diff <= 1  # Within 1 rounding level

    # Undo merge down restores both layers
    assert doc.undo() is True
    assert len(doc.layers) == 2
    assert doc.layers[1].name == "Foreground"
    assert doc.layers[1].offset_x == 20
    assert doc.layers[1].offset_y == 20
    assert abs(doc.layers[1].opacity - 0.5) < 0.01
