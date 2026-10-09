# tests/integration/test_locale_state_preservation.py
"""
Integration Tests — Document and Editor State Preservation During Locale Switching
Author & Maintainer: Ali Kamrani (علی کامرانی)

Verifies that switching application language (or attempting a failed language switch)
strictly preserves all domain, document, and editor states:
1. Current document instance identity
2. Unsaved document modification flag (is_modified)
3. Layer count, order, naming, visibility, and opacity
4. Active layer index and active layer reference
5. Undo and redo history capacity, stack state, and ability to undo/redo after switch
6. Brush tool parameters (size, opacity, hardness, color)
7. Active tool selection (e.g., BrushTool)
8. Canvas zoom factor and viewport geometry
9. Active theme selection
10. UI localization and RTL/LTR direction application without side-effect corruption
"""

import pytest
from PySide6.QtCore import Qt
from PIL import Image

from parto.ui.main_window import MainWindow
from parto.localization import get_localization_manager
from parto.themes import get_theme_manager


def test_editor_state_preservation_across_successful_locale_switch(qapp):
    """
    Comprehensive integration test verifying that changing language from English
    to Persian (LTR -> RTL) preserves all critical document, layer, history, brush,
    tool, zoom, and theme states.
    """
    lm = get_localization_manager()
    lm.set_locale("en", persist=False)

    win = MainWindow()

    # 1. Initialize Document
    win.document.new_document(300, 200, fill_color=(255, 255, 255, 255))
    doc_ref = win.document
    assert doc_ref.has_image is True

    # 2. Add multiple layers with distinct properties
    layer2 = doc_ref.add_layer(name="Foreground Layer", image=Image.new("RGBA", (300, 200), (255, 0, 0, 180)))
    layer3 = doc_ref.add_layer(name="Accent Layer", image=Image.new("RGBA", (300, 200), (0, 255, 0, 120)))

    doc_ref.set_layer_opacity(1, 0.75)
    doc_ref.set_layer_visible(2, False)  # Layer 3 invisible
    doc_ref.set_active_layer_index(1)  # Layer 2 active

    # Make document dirty / modified
    doc_ref._state.is_modified = True

    # 3. Configure Brush Tool and settings
    win.action_tool_brush()
    win.tool_brush.set_size(48)
    win.tool_brush.set_opacity(0.85)
    win.tool_brush.set_hardness(0.65)
    win.tool_brush.set_color((255, 128, 0, 255))

    # 4. Configure Zoom
    win.canvas.zoom_in()
    win.canvas.zoom_in()
    initial_zoom = win.canvas.zoom_factor
    assert initial_zoom > 1.0

    # 5. Configure Theme
    tm = get_theme_manager()
    tm.set_theme("midnight")
    assert tm.current_theme == "midnight"

    # Capture complete pre-switch snapshot
    pre_doc_id = id(win.document)
    pre_is_modified = win.document.is_modified
    pre_layer_count = len(win.document.layers)
    pre_layer_names = [l.name for l in win.document.layers]
    pre_layer_opacities = [l.opacity for l in win.document.layers]
    pre_layer_visibilities = [l.visible for l in win.document.layers]
    pre_active_layer_idx = win.document.active_layer_index
    pre_active_layer_name = win.document.active_layer.name
    pre_can_undo = win.document.history.can_undo
    pre_can_redo = win.document.history.can_redo
    pre_undo_count = len(win.document.history._undo_stack)
    pre_brush_size = win.tool_brush.size
    pre_brush_opacity = win.tool_brush.opacity
    pre_brush_hardness = win.tool_brush.hardness
    pre_brush_color = win.tool_brush.color
    pre_active_tool = win.canvas.active_tool
    pre_theme = tm.current_theme

    # --- EXECUTE LOCALE SWITCH TO PERSIAN ---
    switch_success = lm.set_locale("fa", persist=False)
    assert switch_success is True
    assert lm.current_locale == "fa"
    assert lm.is_rtl is True

    # --- VERIFY STATE PRESERVATION POST-SWITCH ---

    # 1. Document Identity & Dirty Flag
    assert id(win.document) == pre_doc_id
    assert win.document is doc_ref
    assert win.document.is_modified == pre_is_modified
    assert win.document.width == 300
    assert win.document.height == 200

    # 2. Layers State
    assert len(win.document.layers) == pre_layer_count
    assert [l.name for l in win.document.layers] == pre_layer_names
    assert [l.opacity for l in win.document.layers] == pre_layer_opacities
    assert [l.visible for l in win.document.layers] == pre_layer_visibilities
    assert win.document.active_layer_index == pre_active_layer_idx
    assert win.document.active_layer.name == pre_active_layer_name

    # 3. History State & Undo/Redo Capability
    assert win.document.history.can_undo == pre_can_undo
    assert win.document.history.can_redo == pre_can_redo
    assert len(win.document.history._undo_stack) == pre_undo_count

    # Execute Undo in new locale
    undo_result = win.document.undo()
    assert undo_result is True
    assert win.document.history.can_redo is True

    # Execute Redo in new locale
    redo_result = win.document.redo()
    assert redo_result is True
    assert win.document.active_layer_index == pre_active_layer_idx

    # 4. Brush Tool & Settings
    assert win.canvas.active_tool is pre_active_tool
    assert win.tb_tool_brush.isChecked() is True
    assert win.tool_brush.size == pre_brush_size
    assert win.tool_brush.opacity == pre_brush_opacity
    assert win.tool_brush.hardness == pre_brush_hardness
    assert win.tool_brush.color == pre_brush_color

    # 5. Zoom & Viewport
    assert win.canvas.zoom_factor == initial_zoom

    # 6. Theme
    assert tm.current_theme == pre_theme

    # 7. UI Retranslation & Layout Direction
    assert win.layoutDirection() == Qt.RightToLeft
    assert win.menu_file.title() == "پرونده"

    # Reset modified flag to avoid closeEvent QMessageBox prompt in headless tests
    win.document._state.is_modified = False
    win.close()


def test_editor_state_preservation_across_failed_locale_switch(qapp):
    """
    Verifies that a failed locale switch preserves all document, layer,
    and editor states without partial corruption.
    """
    lm = get_localization_manager()
    lm.set_locale("en", persist=False)

    win = MainWindow()
    win.document.new_document(150, 150, fill_color=(100, 100, 100, 255))
    win.document.add_layer(name="Test Layer")
    win.document.set_layer_opacity(0, 0.45)

    pre_doc_id = id(win.document)
    pre_layer_count = len(win.document.layers)
    pre_layer_opacities = [l.opacity for l in win.document.layers]

    # Attempt switch to an invalid locale
    fail_result = lm.set_locale("invalid_nonexistent_locale", persist=False)
    assert fail_result is False

    # Verify everything remains English and intact
    assert lm.current_locale == "en"
    assert lm.is_rtl is False
    assert win.layoutDirection() == Qt.LeftToRight
    assert id(win.document) == pre_doc_id
    assert len(win.document.layers) == pre_layer_count
    assert [l.opacity for l in win.document.layers] == pre_layer_opacities
    assert win.menu_file.title() == "&File"

    win.document._state.is_modified = False
    win.close()
