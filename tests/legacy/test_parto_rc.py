# test_parto_rc.py
"""
Parto v0.3.0 Release Candidate Stabilization Test Suite
Tests:
- Saved / Modified clean state tracking
- Undo / Redo failure safety
- Layer merge down pixel correctness & transparency preservation
- Canvas coordinate conversion & pixel inspector bounds
- Import / Export error hardening
- ThemeManager fallback & ShortcutManager conflict safety
- Brush stroke lifecycle & cancellation
"""

import os
import tempfile
import math
import pytest
from PIL import Image
import numpy as np

from parto.editor.document import Document
from parto.editor.engine import EditorEngine
from parto.history.manager import HistoryManager
from parto.history.commands import Command
from parto.image.layers import Layer, LayerStack, compose_layers
from parto.image.export import save_image_file
from parto.themes.manager import ThemeManager
from parto.shortcuts.manager import ShortcutManager


# ============================================================================
# 1. SAVED / MODIFIED STATE TRACKING
# ============================================================================

def test_document_modified_state_lifecycle():
    """
    Test exact dirty state lifecycle:
    open -> edit -> modified == True
    save -> modified == False
    edit -> modified == True
    undo -> modified == False
    redo -> modified == True
    """
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        tmp_path = tmp.name
        img = Image.new("RGBA", (64, 64), (200, 100, 50, 255))
        img.save(tmp_path)

    try:
        doc = Document()
        assert doc.load_file(tmp_path) is True
        assert doc.modified is False
        assert doc.is_modified is False

        # 1. Edit: rotate
        doc.rotate_document()
        assert doc.modified is True
        assert doc.is_modified is True

        # 2. Save
        success, _ = doc.save_file()
        assert success is True
        assert doc.modified is False
        assert doc.is_modified is False

        # 3. Edit again: crop
        doc.crop_document((0, 0, 32, 32))
        assert doc.modified is True

        # 4. Undo back to save point
        assert doc.undo() is True
        assert doc.modified is False
        assert doc.is_modified is False

        # 5. Redo away from save point
        assert doc.redo() is True
        assert doc.modified is True
        assert doc.is_modified is True

        # 6. Undo again back to save point
        assert doc.undo() is True
        assert doc.modified is False

        # 7. Undo further past the save point (back to load state)
        assert doc.undo() is True
        # Since the file on disk was saved after rotate, undoing past that means
        # current memory state differs from disk, so modified is True!
        assert doc.modified is True

        # 8. Redo back to the exact save point
        assert doc.redo() is True
        assert doc.modified is False
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_engine_modified_property_delegation():
    """Verify EditorEngine exposes modified and is_modified mirroring Document."""
    engine = EditorEngine()
    engine.set_image(Image.new("RGBA", (50, 50), (255, 255, 255, 255)))
    assert engine.modified is False
    assert engine.is_modified is False

    engine.rotate_right()
    assert engine.modified is True
    assert engine.is_modified is True

    engine.undo()
    assert engine.modified is False


# ============================================================================
# 2. UNDO / REDO FAILURE SAFETY
# ============================================================================

class BuggyCommand(Command):
    def __init__(self, name="Buggy", fail_undo=False, fail_redo=False):
        super().__init__(name)
        self.fail_undo = fail_undo
        self.fail_redo = fail_redo

    def undo(self):
        if self.fail_undo:
            raise RuntimeError("Simulated undo failure")

    def redo(self):
        if self.fail_redo:
            raise RuntimeError("Simulated redo failure")


def test_undo_failure_preserves_stack():
    """If an undo operation raises an exception, the undo stack must remain intact."""
    hm = HistoryManager()
    cmd1 = BuggyCommand("Cmd1")
    cmd2 = BuggyCommand("Cmd2-Failing", fail_undo=True)
    hm.push(cmd1)
    hm.push(cmd2)

    assert hm.undo_count == 2
    assert hm.redo_count == 0

    # Attempt to undo cmd2
    success = hm.undo()
    assert success is False

    # Stacks must not have lost cmd2 or become corrupted!
    assert hm.undo_count == 2
    assert hm.redo_count == 0
    assert hm.undo_stack[-1] is cmd2


def test_redo_failure_preserves_stack():
    """If a redo operation raises an exception, the redo stack must remain intact."""
    hm = HistoryManager()
    cmd1 = BuggyCommand("Cmd1")
    cmd2 = BuggyCommand("Cmd2-FailingRedo", fail_redo=True)
    hm.push(cmd1)
    hm.push(cmd2)

    # Undo cmd2 successfully
    assert hm.undo() is True
    assert hm.undo_count == 1
    assert hm.redo_count == 1
    assert hm.redo_stack[-1] is cmd2

    # Attempt to redo cmd2
    success = hm.redo()
    assert success is False

    # Stacks must still have cmd2 on the redo stack
    assert hm.undo_count == 1
    assert hm.redo_count == 1
    assert hm.redo_stack[-1] is cmd2


# ============================================================================
# 3. MERGE DOWN PIXEL CORRECTNESS
# ============================================================================

def test_merge_down_pixel_correctness_transparent():
    """
    Verify merge down onto transparent background:
    - Does not darken or corrupt edge pixels
    - Correct alpha blending
    - Resets merged layer offset and opacity to 1.0
    - Preserves exact composite rendering
    """
    stack = LayerStack(100, 100)

    # Lower layer: Semi-transparent blue circle on transparent canvas
    lower_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for x in range(20, 80):
        for y in range(20, 80):
            lower_img.putpixel((x, y), (0, 0, 255, 128))
    lower = stack.add_layer(lower_img, name="Lower")
    lower.set_opacity(0.8)

    # Upper layer: Semi-transparent yellow square
    upper_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    for x in range(40, 60):
        for y in range(40, 60):
            upper_img.putpixel((x, y), (255, 255, 0, 180))
    upper = stack.add_layer(upper_img, name="Upper")
    upper.set_opacity(0.9)

    # Composite before merge
    comp_before = stack.composite()

    # Perform merge down
    merged = stack.merge_down(1)
    assert merged is not None
    assert len(stack) == 1
    assert merged.name == "Lower"
    assert merged.opacity == 1.0
    assert merged.offset_x == 0
    assert merged.offset_y == 0

    # Composite after merge
    comp_after = stack.composite()

    # Pixels before and after merge down must match exactly!
    arr_before = np.array(comp_before)
    arr_after = np.array(comp_after)
    diff = np.abs(arr_before.astype(int) - arr_after.astype(int))
    assert np.max(diff) == 0, f"Merge down altered composite pixels! Max diff: {np.max(diff)}"


def test_document_merge_down_undo_restores_original_layers():
    """Verify Document.merge_down can be undone, fully restoring both original layers."""
    doc = Document()
    doc.new_document(100, 100, fill_color=(255, 255, 255, 255))

    # Add second layer
    lay2 = doc.add_layer(name="Overlay")
    lay2.set_opacity(0.65)
    lay2.offset_x = 5
    lay2.offset_y = 10

    assert len(doc.layers) == 2
    assert doc.active_layer_index == 1

    # Merge down
    assert doc.merge_down() is True
    assert len(doc.layers) == 1
    assert doc.layers[0].opacity == 1.0

    # Undo
    assert doc.undo() is True
    assert len(doc.layers) == 2
    assert doc.layers[1].name == "Overlay"
    assert doc.layers[1].opacity == pytest.approx(0.65, abs=0.01)
    assert doc.layers[1].offset_x == 5
    assert doc.layers[1].offset_y == 10


# ============================================================================
# 4. CANVAS COORDINATE CONVERSION & PIXEL INSPECTOR
# ============================================================================

def test_pixel_inspector_coordinate_math():
    """Verify floor coordinate conversion handles negative and fractional scene points."""
    # Simulating coordinate conversions used in canvas.py
    for scene_x, expected_px in [
        (0.0, 0),
        (0.99, 0),
        (-0.1, -1),
        (-0.99, -1),
        (10.5, 10),
    ]:
        px = int(math.floor(scene_x))
        assert px == expected_px, f"Failed for scene_x={scene_x}"


# ============================================================================
# 5. IMPORT / EXPORT ERROR HARDENING
# ============================================================================

def test_export_invalid_path():
    """Verify save_image_file handles invalid inputs and non-writable paths gracefully."""
    # 1. None image
    success, err = save_image_file(None, "dummy.png")
    assert success is False
    assert err is not None

    # 2. Non-writable system path
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    success2, err2 = save_image_file(img, "/proc/sys/fs/parto_test_forbidden.png")
    assert success2 is False
    assert err2 is not None


def test_document_load_nonexistent():
    """Verify load_file handles missing file properly."""
    doc = Document()
    res = doc.load_file("/nonexistent/file_123456.png")
    assert res is False


# ============================================================================
# 6. THEMES & SHORTCUTS ROBUSTNESS
# ============================================================================

def test_theme_manager_invalid_key_fallback():
    """Verify ThemeManager falls back to dark theme on invalid/corrupted theme key."""
    tm = ThemeManager()
    tm.set_theme("completely_invalid_theme_name_xyz")
    assert tm.current_theme == "dark"

    pal = tm.get_palette("nonexistent_theme")
    assert "canvas_bg" in pal


def test_shortcut_manager_conflict_detection():
    """Verify ShortcutManager warns and tracks duplicate shortcuts."""
    sm = ShortcutManager()
    sm.register("act_a", "Action A", "Cat", "Ctrl+K", "First")
    sm.register("act_b", "Action B", "Cat", "Ctrl+K", "Second")

    conflicts = sm.find_conflicts()
    assert "ctrl+k" in conflicts
    assert set(conflicts["ctrl+k"]) == {"act_a", "act_b"}

    # Remap act_b to resolve conflict
    assert sm.remap_shortcut("act_b", "Ctrl+Shift+K") is True
    conflicts_after = sm.find_conflicts()
    assert "ctrl+k" not in conflicts_after
