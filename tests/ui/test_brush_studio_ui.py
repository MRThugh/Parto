# tests/ui/test_brush_studio_ui.py
"""
Parto Brush Studio UI Integration & Widget Tests
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from parto.brush.models.settings import BrushSettings
from parto.brush.presets.preset_manager import BrushPresetManager
from parto.ui.panels.brush.dock import BrushStudioDock
from parto.ui.main_window import MainWindow


def test_brush_studio_dock_composition(qapp):
    """Verify BrushStudioDock initializes all 7 studio sections properly."""
    settings = BrushSettings()
    mgr = BrushPresetManager()
    dock = BrushStudioDock(settings, mgr)

    assert dock.header is not None
    assert dock.presets_section is not None
    assert dock.properties_section is not None
    assert dock.color_section is not None
    assert dock.blend_section is not None
    assert dock.dynamics_section is not None
    assert dock.advanced_section is not None
    assert dock.btn_reset_defaults is not None

    dock.close()


def test_brush_studio_property_widgets_interaction(qapp):
    """Verify interacting with TipPropertiesSection sliders & spinboxes updates settings."""
    settings = BrushSettings()
    dock = BrushStudioDock(settings)

    # Size change
    dock.properties_section.row_size.spin.setValue(64)
    qapp.processEvents()
    assert settings.size == 64
    assert dock.properties_section.row_size.slider.value() == 64

    # Hardness change
    dock.properties_section.row_hardness.spin.setValue(40)
    qapp.processEvents()
    assert abs(settings.hardness - 0.40) < 1e-3

    # Angle change
    dock.properties_section.row_angle.spin.setValue(45)
    qapp.processEvents()
    assert abs(settings.angle - 45.0) < 1e-3

    # Roundness change
    dock.properties_section.row_roundness.spin.setValue(75)
    qapp.processEvents()
    assert abs(settings.roundness - 0.75) < 1e-3

    # Opacity change
    dock.blend_section.row_opacity.spin.setValue(80)
    qapp.processEvents()
    assert abs(settings.opacity - 0.80) < 1e-3

    dock.close()


def test_brush_studio_color_swapping_and_palette(qapp):
    """Verify BrushColorSection color swap and reset buttons."""
    settings = BrushSettings()
    settings.color = (255, 0, 0, 255)
    settings.background_color = (0, 0, 255, 255)

    dock = BrushStudioDock(settings)
    qapp.processEvents()

    # Swap
    dock.color_section.btn_swap.click()
    qapp.processEvents()
    assert settings.color == (0, 0, 255, 255)
    assert settings.background_color == (255, 0, 0, 255)

    # Reset (D)
    dock.color_section.btn_reset.click()
    qapp.processEvents()
    assert settings.color == (0, 0, 0, 255)
    assert settings.background_color == (255, 255, 255, 255)

    dock.close()


def test_brush_studio_category_filtering(qapp):
    """Verify category filtering in Presets section."""
    settings = BrushSettings()
    mgr = BrushPresetManager()
    dock = BrushStudioDock(settings, mgr)

    # Filter to Pencil category
    dock.presets_section.category_combo.setCurrentText("Pencil")
    qapp.processEvents()

    visible_items = [
        dock.preset_list.item(i).text()
        for i in range(dock.preset_list.count())
        if not dock.preset_list.item(i).isHidden()
    ]
    assert any("Pencil" in name for name in visible_items)

    # Reset to All
    dock.presets_section.category_combo.setCurrentText("All")
    qapp.processEvents()
    assert sum(1 for i in range(dock.preset_list.count()) if not dock.preset_list.item(i).isHidden()) == dock.preset_list.count()

    dock.close()


def test_main_window_brush_shortcuts_and_actions(qapp):
    """Verify brush studio shortcut action triggers in MainWindow."""
    win = MainWindow()
    win.document.new_document(300, 300)
    win.show()
    qapp.processEvents()

    # Select Brush
    win.action_tool_brush()
    qapp.processEvents()
    assert win.brush_dock.isVisible()

    # Cycle Brush Mode (Shift+B)
    assert not win.tool_brush.is_eraser
    win.action_cycle_brush_mode()
    qapp.processEvents()
    assert win.tool_brush.is_eraser
    win.action_cycle_brush_mode()
    qapp.processEvents()
    assert not win.tool_brush.is_eraser

    # Reset Brush Settings (Shift+F9)
    win.tool_brush.set_size(150)
    assert win.tool_brush.size == 150
    win.action_reset_brush()
    qapp.processEvents()
    assert win.tool_brush.size == 8

    win.close()
