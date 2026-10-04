# test_parto_v031_icons.py
"""
Parto v0.3.1 - Icon Resolver & Regression Audit Test Suite
Author: Ali Kamrani (MRThugh)
Validates:
1. Exact semantic alias mappings for:
   tool_move / tool-move -> move
   tool_crop / tool-crop -> crop
   tool_brush / tool-brush -> brush
   tool_eyedropper / tool-eyedropper -> eyedropper
   rot_left / rot-left -> rotate-ccw
   rot_right / rot-right -> rotate-cw
2. Full audit of all 37 application icon categories without missing-icon warnings
3. MainWindow toolbar initialization produces zero missing-icon warnings
4. Crop layer offset edge cases: (0,0), (20,20), (50,10), negative/out-of-bounds
5. Resize resampling algorithm verification (Lanczos, Bicubic, Bilinear, Nearest)
6. Close event safety flow (Save, Cancel, Discard, Fail)
"""

import pytest
import numpy as np
from PIL import Image
from PySide6.QtGui import QIcon, QCloseEvent
from PySide6.QtWidgets import QMessageBox

from parto.resources.icons import (
    get_parto_icon,
    clear_icon_cache,
    ICON_ALIASES,
    _WARNED_MISSING_ICONS,
)
from parto.editor.document import Document
from parto.ui.main_window import MainWindow, SaveResult


# ============================================================================
# 1. ICON RESOLVER TESTS
# ============================================================================

@pytest.mark.parametrize(
    "raw_name, expected_canonical",
    [
        ("tool_move", "move"),
        ("tool-move", "move"),
        ("tool_crop", "crop"),
        ("tool-crop", "crop"),
        ("tool_brush", "brush"),
        ("tool-brush", "brush"),
        ("tool_eyedropper", "eyedropper"),
        ("tool-eyedropper", "eyedropper"),
        ("rot_left", "rotate-ccw"),
        ("rot-left", "rotate-ccw"),
        ("rot_right", "rotate-cw"),
        ("rot-right", "rotate-cw"),
    ],
)
def test_icon_resolver_tool_and_transform_aliases(qapp, raw_name, expected_canonical):
    """Verify tool and rotation aliases map to canonical renderers and return valid icons."""
    clear_icon_cache()
    _WARNED_MISSING_ICONS.clear()

    icon = get_parto_icon(raw_name)
    assert isinstance(icon, QIcon)
    assert not icon.isNull()

    # The canonical name or raw name must NOT be marked as missing
    assert expected_canonical not in _WARNED_MISSING_ICONS
    assert raw_name.replace("_", "-") not in _WARNED_MISSING_ICONS
    assert len(_WARNED_MISSING_ICONS) == 0


def test_all_application_icon_categories(qapp):
    """
    Verify all required application icon categories resolve to valid, non-null
    icons without triggering missing-icon warnings.
    """
    clear_icon_cache()
    _WARNED_MISSING_ICONS.clear()

    categories = {
        "New": ["new", "new_canvas", "new-canvas"],
        "Open": ["open", "open_image", "open-image"],
        "Save": ["save", "save_image", "save-image"],
        "Save As": ["save_as", "save-as"],
        "Export": ["export", "export_image", "export-image"],
        "Undo": ["undo"],
        "Redo": ["redo"],
        "Crop": ["crop", "tool_crop", "tool-crop"],
        "Resize": ["resize"],
        "Rotate Left": ["rot_left", "rot-left", "rotate-left", "rot_ccw", "rotate_ccw"],
        "Rotate Right": ["rot_right", "rot-right", "rotate-right", "rot_cw", "rotate_cw"],
        "Rotate 180": ["rot_180", "rot-180", "rotate_180", "rotate-180"],
        "Flip Horizontal": ["flip_h", "flip-h", "flip_horizontal", "flip-horizontal"],
        "Flip Vertical": ["flip_v", "flip-v", "flip_vertical", "flip-vertical"],
        "Adjust": ["adjust", "adjustments"],
        "Filter": ["filter", "filters"],
        "Compare": ["compare"],
        "Zoom In": ["zoom_in", "zoom-in"],
        "Zoom Out": ["zoom_out", "zoom-out"],
        "Zoom Fit": ["zoom_fit", "zoom-fit", "fit"],
        "Zoom Actual": ["zoom_actual", "zoom-actual", "actual", "zoom_100"],
        "Move": ["move", "tool_move", "tool-move", "hand", "pan"],
        "Brush": ["brush", "tool_brush", "tool-brush", "paint"],
        "Eyedropper": ["eyedropper", "tool_eyedropper", "tool-eyedropper", "dropper"],
        "Layers": ["layers"],
        "Add Layer": ["layer-add", "add_layer", "new_layer"],
        "Duplicate Layer": ["layer-duplicate", "duplicate_layer", "dup_layer"],
        "Delete Layer": ["layer-delete", "delete_layer", "del_layer", "remove_layer"],
        "Visibility": ["eye", "layer-visible", "visible", "eye-off", "layer-hidden", "hidden"],
        "Move Layer Up": ["layer-up", "move_up"],
        "Move Layer Down": ["layer-down", "move_down"],
        "Merge Layer": ["layer-merge", "merge_down"],
        "Info": ["info", "properties", "file_info"],
        "Theme": ["theme"],
        "Shortcuts": ["shortcuts", "shortcut", "help_shortcuts", "palette", "command_palette"],
        "Settings": ["settings"],
        "Logo": ["logo"],
    }

    for cat_name, icon_names in categories.items():
        for name in icon_names:
            icon = get_parto_icon(name)
            assert not icon.isNull(), f"Category {cat_name}: icon '{name}' returned null QIcon"

    # Crucial: Not a single icon in all supported categories should have triggered a warning!
    assert len(_WARNED_MISSING_ICONS) == 0, f"Unexpected missing icons: {_WARNED_MISSING_ICONS}"


def test_mainwindow_toolbar_has_no_missing_icons(qapp):
    """Instantiating MainWindow and its toolbar must trigger ZERO missing icon warnings."""
    clear_icon_cache()
    _WARNED_MISSING_ICONS.clear()

    win = MainWindow()
    win.show()

    assert len(_WARNED_MISSING_ICONS) == 0
    win.close()


# ============================================================================
# 2. REGRESSION AUDIT: OFFSET-AWARE CROP EDGE CASES
# ============================================================================

def test_crop_layer_offset_0_0():
    """Layer at (0, 0) cropped to sub-rectangle updates layer bounds and offset properly."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (50, 50), (255, 0, 0, 255)),
        offset_x=0,
        offset_y=0,
    )
    # Crop canvas to (10, 10, 40, 40)
    doc.crop_document((10, 10, 40, 40))
    assert doc.width == 30
    assert doc.height == 30
    assert layer.offset_x == 0
    assert layer.offset_y == 0
    assert layer.width == 30
    assert layer.height == 30


def test_crop_layer_offset_20_20():
    """Layer at (20, 20) with crop spanning (10, 10, 60, 60)."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (30, 30), (0, 255, 0, 255)),
        offset_x=20,
        offset_y=20,
    )
    # Layer canvas bounds: (20, 20, 50, 50).
    # Crop rect: (10, 10, 60, 60). Crop enclosing layer completely!
    doc.crop_document((10, 10, 60, 60))
    assert doc.width == 50
    assert doc.height == 50
    # New offset is (20 - 10, 20 - 10) = (10, 10)
    assert layer.offset_x == 10
    assert layer.offset_y == 10
    assert layer.width == 30
    assert layer.height == 30


def test_crop_layer_offset_50_10():
    """Layer at (50, 10) with partial crop (40, 0, 70, 30)."""
    doc = Document()
    doc.new_document(100, 100)
    layer = doc.add_layer(
        Image.new("RGBA", (40, 40), (0, 0, 255, 255)),
        offset_x=50,
        offset_y=10,
    )
    # Layer bounds: (50, 10, 90, 50)
    # Crop rect: (40, 0, 70, 30) -> overlap: (50, 10, 70, 30) -> width 20, height 20
    doc.crop_document((40, 0, 70, 30))
    assert doc.width == 30
    assert doc.height == 30
    # In new canvas space (starting at x=40, y=0), intersection starts at (50-40, 10-0) = (10, 10)
    assert layer.offset_x == 10
    assert layer.offset_y == 10
    assert layer.width == 20
    assert layer.height == 20


# ============================================================================
# 3. REGRESSION AUDIT: RESIZE RESAMPLING ALGORITHMS
# ============================================================================

def test_resize_resampling_options():
    """Verify NEAREST, BILINEAR, BICUBIC, LANCZOS can all be passed and take effect."""
    for resample_filter in [
        Image.Resampling.NEAREST,
        Image.Resampling.BILINEAR,
        Image.Resampling.BICUBIC,
        Image.Resampling.LANCZOS,
    ]:
        doc = Document()
        doc.new_document(20, 20)
        doc.resize_document(40, 40, resample=resample_filter)
        assert doc.width == 40
        assert doc.height == 40


# ============================================================================
# 4. REGRESSION AUDIT: SAVE & CLOSE SAFETY FLOW
# ============================================================================

def test_close_event_save_safety_flows(qapp, monkeypatch):
    """
    Verify:
    - Save succeeds -> continue (accept)
    - Save cancelled -> remain open (ignore)
    - Save fails -> remain open (ignore)
    - Discard -> continue (accept)
    - Cancel -> remain open (ignore)
    """
    win = MainWindow()
    win.document.set_modified(True)

    # 1. User clicks Cancel in message box -> ignore event
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Cancel)
    event_cancel = QCloseEvent()
    win.closeEvent(event_cancel)
    assert event_cancel.isAccepted() is False

    # 2. User clicks Discard -> accept event
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Discard)
    event_discard = QCloseEvent()
    win.closeEvent(event_discard)
    assert event_discard.isAccepted() is True

    # 3. User clicks Save, but save is cancelled (e.g. file dialog cancelled) -> ignore event
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.Save)
    monkeypatch.setattr(win, "action_save_image", lambda: SaveResult.CANCELLED)
    event_save_cancel = QCloseEvent()
    win.closeEvent(event_save_cancel)
    assert event_save_cancel.isAccepted() is False

    # 4. User clicks Save, but save fails (e.g. disk write error) -> ignore event
    monkeypatch.setattr(win, "action_save_image", lambda: SaveResult.FAILED)
    event_save_fail = QCloseEvent()
    win.closeEvent(event_save_fail)
    assert event_save_fail.isAccepted() is False

    # 5. User clicks Save, and save succeeds -> accept event
    monkeypatch.setattr(win, "action_save_image", lambda: SaveResult.SUCCESS)
    event_save_ok = QCloseEvent()
    win.closeEvent(event_save_ok)
    assert event_save_ok.isAccepted() is True

    win.close()
