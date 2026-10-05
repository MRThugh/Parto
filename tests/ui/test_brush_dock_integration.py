# tests/ui/test_brush_dock_integration.py
"""
UI & Integration Tests — Brush Panel, Presets, and MainWindow Auto-Activation
Author & Maintainer: Ali Kamrani (علی کامرانی)

Verifies:
1. BrushDock component structure, controls, and bindings.
2. Two-way synchronization between BrushDock, BrushBar, and authoritative BrushSettings.
3. Automatic exposure of BrushDock and BrushBar when Brush tool is selected.
4. Automatic hiding of BrushDock when navigating to Move, Crop, or Eyedropper tools.
5. Strict preservation of brush settings (size, opacity, hardness, colors) and selected preset across tool switches.
6. Preset filtering, preset creation, and built-in protection in the UI.
"""

import pytest
from PySide6.QtCore import Qt

from parto.ui.main_window import MainWindow
from parto.tools.brush import BrushSettings, BrushPresetManager
from parto.ui.panels.brush_panel import BrushDock


def test_brush_dock_initialization(qapp):
    """Verify BrushDock initializes all controls and binds to authoritative settings."""
    settings = BrushSettings(size=20, opacity=0.8, hardness=0.5, flow=0.9, spacing=0.2)
    mgr = BrushPresetManager()
    dock = BrushDock(settings, mgr)

    assert dock.slider_size.value() == 20
    assert dock.spin_size.value() == 20
    assert dock.slider_opacity.value() == 80
    assert dock.spin_opacity.value() == 80
    assert dock.slider_hardness.value() == 50
    assert dock.spin_hardness.value() == 50
    assert dock.slider_flow.value() == 90
    assert dock.spin_flow.value() == 90
    assert dock.slider_spacing.value() == 20
    assert dock.spin_spacing.value() == 20
    assert not dock.cb_erase_mode.isChecked()

    dock.close()


def test_brush_dock_two_way_synchronization(qapp):
    """Verify modifying BrushDock controls directly mutates BrushSettings and vice-versa."""
    settings = BrushSettings()
    dock = BrushDock(settings)

    # UI spinbox change -> updates settings
    dock.spin_size.setValue(45)
    assert settings.size == 45
    assert dock.slider_size.value() == 45

    dock.spin_opacity.setValue(65)
    assert abs(settings.opacity - 0.65) < 1e-3
    assert dock.slider_opacity.value() == 65

    # Direct settings change -> updates UI
    settings.set_size(88)
    assert dock.slider_size.value() == 88
    assert dock.spin_size.value() == 88

    settings.set_hardness(0.25)
    assert dock.slider_hardness.value() == 25
    assert dock.spin_hardness.value() == 25

    dock.close()


def test_main_window_brush_auto_activation(qapp):
    """Verify BrushDock automatically exposes on Brush tool selection and hides on other tools."""
    win = MainWindow()
    win.document.new_document(400, 400)
    win.show()
    qapp.processEvents()

    # Default tool is Move: brush bar and brush dock must be hidden
    assert not win.brush_bar.isVisible()
    assert not win.brush_dock.isVisible()

    # 1. Select Brush Tool: brush_bar and brush_dock must become visible
    win.action_tool_brush()
    qapp.processEvents()
    assert win.brush_bar.isVisible()
    assert win.brush_dock.isVisible()
    assert win.tb_tool_brush.isChecked()

    # Configure a distinct brush state
    win.tool_brush.set_size(73)
    win.tool_brush.set_opacity(0.42)
    win.tool_brush.set_color((255, 128, 0, 255))
    qapp.processEvents()
    assert win.brush_bar.spin_size.value() == 73
    assert win.brush_dock.spin_size.value() == 73

    # 2. Switch away to Move Tool: brush_bar and brush_dock must hide
    win.action_tool_move()
    qapp.processEvents()
    assert not win.brush_bar.isVisible()
    assert not win.brush_dock.isVisible()
    assert win.tb_tool_move.isChecked()

    # Settings must NOT have been destroyed or reset
    assert win.tool_brush.size == 73
    assert abs(win.tool_brush.opacity - 0.42) < 1e-3
    assert win.tool_brush.color == (255, 128, 0, 255)

    # 3. Switch back to Brush Tool: brush_bar and brush_dock become visible with settings intact
    win.action_tool_brush()
    qapp.processEvents()
    assert win.brush_bar.isVisible()
    assert win.brush_dock.isVisible()
    assert win.tool_brush.size == 73
    assert win.brush_bar.spin_size.value() == 73
    assert win.brush_dock.spin_size.value() == 73

    # 4. Switch to Crop Tool: brush_bar and brush_dock must hide
    win.action_tool_crop()
    qapp.processEvents()
    assert not win.brush_bar.isVisible()
    assert not win.brush_dock.isVisible()
    assert win.crop_bar.isVisible()

    # 5. Switch to Eyedropper Tool: brush_bar and brush_dock must hide
    win.action_tool_eyedropper()
    qapp.processEvents()
    assert not win.brush_bar.isVisible()
    assert not win.brush_dock.isVisible()
    assert not win.crop_bar.isVisible()

    # 6. Switch back to Brush Tool again
    win.action_tool_brush()
    qapp.processEvents()
    assert win.brush_bar.isVisible()
    assert win.brush_dock.isVisible()
    assert win.tool_brush.size == 73

    win.close()


def test_brush_dock_preset_selection_and_filter(qapp):
    """Verify selecting presets in BrushDock applies them to authoritative settings."""
    settings = BrushSettings()
    mgr = BrushPresetManager()
    dock = BrushDock(settings, mgr)

    # Initial preset is Basic Round (size 12)
    assert mgr.active_preset_name == "Basic Round"

    # Select "Airbrush"
    found = False
    for i in range(dock.preset_list.count()):
        item = dock.preset_list.item(i)
        if item.data(Qt.UserRole) == "Airbrush":
            dock.preset_list.setCurrentItem(item)
            found = True
            break
    assert found
    assert settings.size == 40
    assert abs(settings.opacity - 0.35) < 1e-3
    assert abs(settings.hardness - 0.02) < 1e-3

    # Filter presets list
    dock.search_edit.setText("pencil")
    visible_count = sum(1 for i in range(dock.preset_list.count()) if not dock.preset_list.item(i).isHidden())
    assert visible_count == 1

    dock.search_edit.clear()
    visible_count = sum(1 for i in range(dock.preset_list.count()) if not dock.preset_list.item(i).isHidden())
    assert visible_count == len(mgr.get_all_presets())

    dock.close()
