# tests/ui/test_contextual_brush_menu.py
"""
UI Tests — Contextual Brush Studio Menu & Active Tool Synchronization
Author: Ali Kamrani (MRThugh)

Verifies:
1. Brush Studio is removed from the global View menu.
2. Contextual Brush menu is only exposed when the Brush tool is active.
3. Switching to Move, Crop, or Eyedropper hides the contextual Brush menu and dock.
4. Brush settings (size, opacity, hardness, color, eraser mode) strictly survive tool switching.
5. Brush-specific shortcuts activate the Brush context when invoked from other tools.
"""

import pytest
from PySide6.QtCore import Qt

from parto.ui.main_window import MainWindow
from parto.shortcuts.manager import get_shortcut_manager


def test_view_menu_does_not_contain_brush_studio(qapp):
    """Verify Brush Studio is NOT a global View menu action."""
    win = MainWindow()
    win.show()
    qapp.processEvents()

    # Find the View menu in the menu bar
    view_menu = None
    for action in win.menuBar().actions():
        menu = action.menu()
        if menu and "&View" in menu.title():
            view_menu = menu
            break

    assert view_menu is not None, "View menu not found in menuBar"

    # Confirm Brush Studio is NOT an action in the View menu
    view_action_texts = [act.text().replace("&", "") for act in view_menu.actions()]
    assert "Brush Studio" not in view_action_texts

    win.close()


def test_contextual_brush_menu_tool_lifecycle(qapp):
    """Verify Brush menu visibility synchronizes strictly with active tool."""
    win = MainWindow()
    win.document.new_document(300, 300)
    win.show()
    qapp.processEvents()

    # 1. Default tool is Move: Brush menu and Brush dock must be hidden
    assert hasattr(win, "brush_menu")
    assert win.brush_menu.menuAction().isVisible() is False
    assert win.brush_dock.isVisible() is False

    # 2. Switch to Brush Tool: Brush menu and Brush dock become visible
    win.action_tool_brush()
    qapp.processEvents()
    assert win.brush_menu.menuAction().isVisible() is True
    assert win.brush_dock.isVisible() is True
    assert win.act_brush_studio.isChecked() is True

    # 3. Switch to Move Tool: Brush menu and Brush dock hide
    win.action_tool_move()
    qapp.processEvents()
    assert win.brush_menu.menuAction().isVisible() is False
    assert win.brush_dock.isVisible() is False

    # 4. Switch back to Brush Tool
    win.action_tool_brush()
    qapp.processEvents()
    assert win.brush_menu.menuAction().isVisible() is True
    assert win.brush_dock.isVisible() is True

    # 5. Switch to Crop Tool: Brush menu and dock hide, crop bar appears
    win.action_tool_crop()
    qapp.processEvents()
    assert win.brush_menu.menuAction().isVisible() is False
    assert win.brush_dock.isVisible() is False
    assert win.crop_bar.isVisible() is True

    # 6. Switch to Eyedropper Tool: Brush menu and dock remain hidden
    win.action_tool_eyedropper()
    qapp.processEvents()
    assert win.brush_menu.menuAction().isVisible() is False
    assert win.brush_dock.isVisible() is False

    win.close()


def test_brush_settings_survive_tool_switching(qapp):
    """Verify all brush properties survive switching through Move, Crop, and Eyedropper."""
    win = MainWindow()
    win.document.new_document(250, 250)
    win.show()
    qapp.processEvents()

    # Activate Brush and configure distinct custom state
    win.action_tool_brush()
    qapp.processEvents()
    win.tool_brush.set_size(83)
    win.tool_brush.set_opacity(0.47)
    win.tool_brush.set_hardness(0.68)
    win.tool_brush.color = (123, 45, 67, 255)
    win.tool_brush.background_color = (89, 101, 112, 255)
    win.tool_brush.is_eraser = True

    # Switch away to Move
    win.action_tool_move()
    qapp.processEvents()

    # Switch to Crop
    win.action_tool_crop()
    qapp.processEvents()

    # Switch to Eyedropper
    win.action_tool_eyedropper()
    qapp.processEvents()

    # Return to Brush
    win.action_tool_brush()
    qapp.processEvents()

    assert win.tool_brush.size == 83
    assert abs(win.tool_brush.opacity - 0.47) < 1e-3
    assert abs(win.tool_brush.hardness - 0.68) < 1e-3
    assert win.tool_brush.color == (123, 45, 67, 255)
    assert win.tool_brush.background_color == (89, 101, 112, 255)
    assert win.tool_brush.is_eraser is True

    win.close()


def test_brush_shortcuts_activate_brush_context(qapp):
    """Verify brush-specific focus shortcuts activate Brush context if called from other tools."""
    win = MainWindow()
    win.document.new_document(200, 200)
    win.show()
    qapp.processEvents()

    # Initially Move tool
    assert win.tb_tool_move.isChecked() is True
    assert win.brush_menu.menuAction().isVisible() is False

    # Focus Presets (Ctrl+Shift+B) switches to Brush and opens studio
    win.action_focus_brush_presets()
    qapp.processEvents()
    assert win.tb_tool_brush.isChecked() is True
    assert win.brush_menu.menuAction().isVisible() is True
    assert win.brush_dock.isVisible() is True

    # Switch to Move
    win.action_tool_move()
    qapp.processEvents()
    assert win.tb_tool_move.isChecked() is True

    # Focus Properties (Alt+B) switches to Brush and opens studio
    win.action_focus_brush_properties()
    qapp.processEvents()
    assert win.tb_tool_brush.isChecked() is True
    assert win.brush_menu.menuAction().isVisible() is True
    assert win.brush_dock.isVisible() is True

    win.close()
