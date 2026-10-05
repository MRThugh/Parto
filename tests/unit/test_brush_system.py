# tests/unit/test_brush_system.py
"""
Unit Tests — Brush Settings, Preset Model & Preset Manager Architecture
Author & Maintainer: Ali Kamrani (علی کامرانی)

Verifies:
1. Authoritative BrushSettings state and constraint clamping (size 1-500, flow, spacing, etc.).
2. BrushSettings listener notification lifecycle.
3. BrushPreset data model serialization and deserialization.
4. BrushPresetManager built-in preset immutability and user preset CRUD.
5. Safe filesystem persistence and loading of user brush presets.
6. Non-overlapping numeric spinner styling and asset validity.
"""

import os
import json
import tempfile
import pytest
from PySide6.QtWidgets import QSpinBox, QDoubleSpinBox
from PySide6.QtCore import Qt

from parto.tools.brush import BrushSettings, BrushPreset, BrushPresetManager, BrushRenderer
from parto.themes.palettes import get_spinbox_arrow_icons, get_theme_stylesheet, THEME_PALETTES


def test_brush_settings_clamping_and_defaults():
    """Verify BrushSettings enforces authoritative boundary clamping."""
    s = BrushSettings()
    assert s.size == 8
    assert s.opacity == 1.0
    assert s.hardness == 0.8
    assert s.flow == 1.0
    assert s.spacing == 0.25
    assert not s.is_eraser

    # Test size boundaries (1 to 500)
    s.set_size(0)
    assert s.size == 1
    s.set_size(1000)
    assert s.size == 500
    s.set_size(42)
    assert s.size == 42

    # Test opacity boundaries (0.0 to 1.0)
    s.set_opacity(-0.5)
    assert s.opacity == 0.0
    s.set_opacity(1.5)
    assert s.opacity == 1.0

    # Test flow boundaries (0.0 to 1.0)
    s.set_flow(-0.1)
    assert s.flow == 0.0
    s.set_flow(2.0)
    assert s.flow == 1.0

    # Test spacing boundaries (0.05 to 2.0)
    s.set_spacing(0.01)
    assert s.spacing == 0.05
    s.set_spacing(5.0)
    assert s.spacing == 2.0


def test_brush_settings_listener_notifications():
    """Verify listener callbacks are reliably invoked when settings mutate."""
    s = BrushSettings()
    notifications = []

    def callback():
        notifications.append(s.size)

    s.add_listener(callback)
    s.set_size(16)
    assert len(notifications) == 1
    assert notifications[-1] == 16

    # Redundant set should NOT trigger listener
    s.set_size(16)
    assert len(notifications) == 1

    # Remove listener
    s.remove_listener(callback)
    s.set_size(24)
    assert len(notifications) == 1


def test_brush_settings_color_operations():
    """Verify foreground/background color swapping and reset to defaults."""
    s = BrushSettings(
        color=(255, 0, 0, 255),
        background_color=(0, 255, 0, 255)
    )
    s.swap_colors()
    assert s.color == (0, 255, 0, 255)
    assert s.background_color == (255, 0, 0, 255)

    s.reset_default_colors()
    assert s.color == (0, 0, 0, 255)
    assert s.background_color == (255, 255, 255, 255)


def test_brush_preset_model_and_apply():
    """Verify BrushPreset serialization, deserialization, and applying to settings."""
    preset = BrushPreset(
        name="Test Inker",
        size=14,
        opacity=0.9,
        flow=0.85,
        hardness=0.95,
        spacing=0.15,
        is_eraser=False,
        is_builtin=False,
        description="Crisp inking line",
    )
    d = preset.to_dict()
    assert d["name"] == "Test Inker"
    assert d["size"] == 14
    assert d["spacing"] == 0.15

    restored = BrushPreset.from_dict(d, is_builtin=False)
    assert restored.name == preset.name
    assert restored.size == preset.size
    assert restored.flow == preset.flow

    s = BrushSettings()
    restored.apply_to(s)
    assert s.size == 14
    assert abs(s.opacity - 0.9) < 1e-4
    assert abs(s.flow - 0.85) < 1e-4
    assert abs(s.hardness - 0.95) < 1e-4
    assert abs(s.spacing - 0.15) < 1e-4


def test_brush_preset_manager_builtins():
    """Verify built-in presets exist and cannot be deleted."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "presets.json")
        mgr = BrushPresetManager(storage_path=storage_path)

        builtins = mgr.get_builtin_presets()
        assert len(builtins) >= 5
        builtin_names = [p.name.lower() for p in builtins]
        assert "basic round" in builtin_names
        assert "soft round" in builtin_names
        assert "hard round" in builtin_names
        assert "eraser" in builtin_names

        # Attempting to delete a built-in preset must fail
        deleted = mgr.delete_user_preset("Basic Round")
        assert not deleted
        assert mgr.get_preset("Basic Round") is not None


def test_brush_preset_manager_user_presets_persistence():
    """Verify creating, persisting, and deleting user presets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "presets.json")
        mgr = BrushPresetManager(storage_path=storage_path)

        s = BrushSettings(size=33, opacity=0.75, flow=0.6, hardness=0.5, spacing=0.18)
        created = mgr.create_user_preset("My Custom Watercolor", s, description="Soft wash")
        assert created.name == "My Custom Watercolor"
        assert created.size == 33
        assert not created.is_builtin

        # File should have been saved
        assert os.path.exists(storage_path)
        with open(storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1
        assert data[0]["name"] == "My Custom Watercolor"

        # Instantiate a fresh manager pointing to the same file
        mgr2 = BrushPresetManager(storage_path=storage_path)
        user_presets = mgr2.get_user_presets()
        assert len(user_presets) == 1
        assert user_presets[0].name == "My Custom Watercolor"
        assert user_presets[0].size == 33

        # Apply to new settings
        s2 = BrushSettings()
        assert mgr2.apply_preset("My Custom Watercolor", s2)
        assert s2.size == 33

        # Delete user preset
        assert mgr2.delete_user_preset("My Custom Watercolor")
        assert len(mgr2.get_user_presets()) == 0


def test_spinner_styling_and_assets(qapp):
    """Verify global numeric spinner CSS and SVG arrow assets exist."""
    arrows = get_spinbox_arrow_icons("dark", THEME_PALETTES["dark"])
    for key, path in arrows.items():
        assert os.path.exists(path), f"Missing arrow asset: {key} -> {path}"
        assert os.path.getsize(path) > 50

    dark_qss = get_theme_stylesheet("dark")
    light_qss = get_theme_stylesheet("light")

    assert "QSpinBox, QDoubleSpinBox" in dark_qss
    assert "padding-right: 22px" in dark_qss
    assert "up-button" in dark_qss
    assert "down-button" in dark_qss

    # Verify QSpinBox geometry layout
    sb = QSpinBox()
    sb.setRange(1, 500)
    sb.setValue(250)
    sb.setSuffix(" px")
    sb.setStyleSheet(dark_qss)
    sb.resize(100, 30)
    sb.show()
    qapp.processEvents()

    # The line edit inside spin box must leave space on the right for up/down buttons
    line_edit = sb.findChild(type(sb.lineEdit()))
    assert line_edit is not None
    assert line_edit.width() <= sb.width() - 16
    sb.close()
