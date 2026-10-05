# tests/unit/test_brush_studio_subsystem.py
"""
Parto Brush Studio Subsystem Unit Tests
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import json
import pytest
from parto.brush.models.settings import BrushSettings
from parto.brush.models.preset import BrushPreset
from parto.brush.models.enums import DynamicsControl, BrushCategory, BlendMode
from parto.brush.presets.preset_manager import BrushPresetManager
from parto.brush.presets.builtin import get_builtin_presets
from parto.brush.engine.dab import DabGenerator
from parto.shortcuts.manager import get_shortcut_manager, ShortcutDefinition


def test_brush_settings_extended_properties():
    """Verify new BrushSettings properties (angle, roundness, smoothing, dynamics)."""
    s = BrushSettings()
    
    # Angle (modulo 360)
    s.set_angle(45.0)
    assert s.angle == 45.0
    s.set_angle(400.0)
    assert s.angle == 40.0
    s.set_angle(-10.0)
    assert s.angle == 350.0

    # Roundness
    s.set_roundness(0.5)
    assert abs(s.roundness - 0.5) < 1e-4
    s.set_roundness(1.5)
    assert s.roundness == 1.0
    s.set_roundness(0.001)
    assert s.roundness == 0.01

    # Smoothing & Scatter
    s.set_smoothing(0.8)
    assert abs(s.smoothing - 0.8) < 1e-4
    s.set_scatter(0.3)
    assert abs(s.scatter - 0.3) < 1e-4

    # Dynamics
    s.set_dynamics_size("pressure")
    assert s.dynamics_size == "pressure"
    s.set_dynamics_opacity("velocity")
    assert s.dynamics_opacity == "velocity"
    s.set_dynamics_flow("tilt")
    assert s.dynamics_flow == "tilt"
    s.set_dynamics_angle("random")
    assert s.dynamics_angle == "random"


def test_brush_settings_reset_to_defaults():
    """Verify reset_to_defaults restores standard factory values."""
    s = BrushSettings()
    s.size = 200
    s.opacity = 0.2
    s.set_angle(90.0)
    s.set_roundness(0.3)
    s.set_smoothing(0.9)
    s.set_dynamics_size("pressure")

    s.reset_to_defaults()
    assert s.size == 8
    assert s.opacity == 1.0
    assert s.angle == 0.0
    assert s.roundness == 1.0
    assert s.smoothing == 0.0
    assert s.dynamics_size == "off"


def test_brush_settings_serialization_roundtrip():
    """Verify to_dict and from_dict preserve all properties."""
    s1 = BrushSettings(
        size=42,
        opacity=0.65,
        flow=0.75,
        hardness=0.45,
        spacing=0.15,
        angle=30.0,
        roundness=0.6,
        smoothing=0.5,
        scatter=0.2,
    )
    s1.set_dynamics_size("pressure")
    s1.set_dynamics_opacity("velocity")

    d = s1.to_dict()
    s2 = BrushSettings.from_dict(d)

    assert s2.size == 42
    assert abs(s2.opacity - 0.65) < 1e-4
    assert abs(s2.flow - 0.75) < 1e-4
    assert abs(s2.hardness - 0.45) < 1e-4
    assert abs(s2.spacing - 0.15) < 1e-4
    assert abs(s2.angle - 30.0) < 1e-4
    assert abs(s2.roundness - 0.6) < 1e-4
    assert abs(s2.smoothing - 0.5) < 1e-4
    assert abs(s2.scatter - 0.2) < 1e-4
    assert s2.dynamics_size == "pressure"
    assert s2.dynamics_opacity == "velocity"


def test_builtin_presets_rich_categories():
    """Verify built-in presets cover required categories and valid properties."""
    builtins = get_builtin_presets()
    assert len(builtins) >= 8

    categories = {p.category for p in builtins}
    assert "Basic" in categories
    assert "Pencil" in categories
    assert "Ink" in categories
    assert "Airbrush" in categories
    assert "Marker" in categories
    assert "Eraser" in categories

    for p in builtins:
        assert p.is_builtin is True
        assert 1 <= p.size <= 500
        assert 0.0 <= p.opacity <= 1.0
        assert 0.0 <= p.hardness <= 1.0
        assert 0.05 <= p.spacing <= 2.0


def test_preset_apply_to_settings():
    """Verify applying a preset configures BrushSettings completely."""
    preset = BrushPreset(
        name="Test Inker",
        size=14,
        opacity=0.9,
        flow=0.95,
        hardness=0.85,
        spacing=0.1,
        angle=25.0,
        roundness=0.7,
        smoothing=0.6,
        scatter=0.05,
        blend_mode="multiply",
        dynamics_size="pressure",
    )
    settings = BrushSettings()
    preset.apply_to(settings)

    assert settings.size == 14
    assert abs(settings.opacity - 0.9) < 1e-4
    assert abs(settings.flow - 0.95) < 1e-4
    assert abs(settings.hardness - 0.85) < 1e-4
    assert abs(settings.angle - 25.0) < 1e-4
    assert abs(settings.roundness - 0.7) < 1e-4
    assert abs(settings.smoothing - 0.6) < 1e-4
    assert settings.dynamics_size == "pressure"


def test_preset_manager_duplicate_and_export(tmp_path):
    """Verify preset duplication, renaming, export and import."""
    mgr = BrushPresetManager()
    
    # Duplicate built-in
    dup = mgr.duplicate_user_preset("Basic Round")
    assert dup is not None
    assert "Copy" in dup.name
    assert not dup.is_builtin

    # Toggle favorite
    assert mgr.toggle_favorite(dup.name) is True
    updated = mgr.get_preset(dup.name)
    assert updated.favorite is True

    # Export to json
    export_file = tmp_path / "custom_brush.json"
    assert mgr.export_preset(dup.name, str(export_file)) is True
    assert export_file.exists()

    with open(export_file, "r") as f:
        data = json.load(f)
    assert data["name"] == dup.name

    # Import
    imported = mgr.import_preset(str(export_file))
    assert imported is not None


def test_dab_generator_elliptical_and_angled():
    """Verify DabGenerator creates valid PIL images with roundness and angle."""
    gen = DabGenerator()
    s = BrushSettings(
        size=30,
        hardness=0.8,
        color=(255, 0, 0, 255),
        roundness=0.5,
        angle=45.0,
    )
    dab = gen.generate_dab(s)
    assert dab is not None
    assert dab.mode == "RGBA"
    assert dab.width == 30
    assert dab.height == 30


def test_shortcut_manager_query_and_categories():
    """Verify ShortcutManager groups and retrieves shortcuts cleanly."""
    sm = get_shortcut_manager()
    sm.register("test_brush_tool", "Brush", "Brush", "Ctrl+Alt+B", "Brush Tool")
    sm.register("test_move_tool", "Move", "Tools", "V", "Move Tool")

    categories = sm.categories()
    assert "Brush" in categories
    assert "Tools" in categories

    brush_shortcuts = sm.by_category("Brush")
    assert len(brush_shortcuts) >= 1

    keys = {d.key_sequence for d in brush_shortcuts}
    assert "Ctrl+Alt+B" in keys
