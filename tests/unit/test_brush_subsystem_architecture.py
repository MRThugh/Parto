# tests/unit/test_brush_subsystem_architecture.py
"""
Unit Tests — Dedicated Brush Subsystem Domain Architecture
Verifies pure domain models, engine, input normalizer, preset storage,
controller, and document boundary without UI coupling.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

import os
import json
import tempfile
import pytest
from PIL import Image

from parto.brush.models.enums import BlendMode, BrushShapeType, PointerType
from parto.brush.models.settings import BrushSettings
from parto.brush.models.preset import BrushPreset
from parto.brush.models.stroke import StrokePoint, Stroke
from parto.brush.engine.dab import DabGenerator
from parto.brush.engine.renderer import BrushRenderer
from parto.brush.engine.brush_engine import RasterBrushEngine, IBrushEngine
from parto.brush.input.pointer import PointerState
from parto.brush.input.normalizer import InputNormalizer
from parto.brush.presets.builtin import get_builtin_presets
from parto.brush.presets.storage import PresetStorage
from parto.brush.presets.preset_manager import BrushPresetManager
from parto.brush.document_adapter import BrushDocumentAdapter
from parto.brush.controller.stroke_controller import StrokeController
from parto.brush.controller.brush_controller import BrushController
from parto.brush.tools.brush_tool import BrushTool
from parto.editor.document import Document


# --- 1. Domain Models ---

def test_brush_settings_pure_python():
    """Verify BrushSettings functions without Qt imports and respects boundaries."""
    s = BrushSettings()
    assert s.size == 8
    assert s.opacity == 1.0
    assert s.hardness == 0.8
    assert s.flow == 1.0
    assert s.spacing == 0.25
    assert not s.is_eraser
    assert s.blend_mode == BlendMode.NORMAL

    # Bounds
    s.size = -10
    assert s.size == BrushSettings.MIN_SIZE
    s.size = 9999
    assert s.size == BrushSettings.MAX_SIZE

    s.opacity = -0.5
    assert s.opacity == 0.0
    s.opacity = 2.0
    assert s.opacity == 1.0

    s.spacing = 0.01
    assert s.spacing == 0.05
    s.spacing = 5.0
    assert s.spacing == 2.0

    # Serialization and cloning
    d = s.to_dict()
    assert isinstance(d, dict)
    assert d["size"] == BrushSettings.MAX_SIZE

    clone = s.copy()
    assert clone.size == s.size
    assert clone.to_dict() == s.to_dict()

    restored = BrushSettings.from_dict(d)
    assert restored.size == s.size


def test_brush_settings_observer_notifications():
    """Verify listener observer pattern without Qt signals."""
    s = BrushSettings(size=10)
    fired = []

    def on_change():
        fired.append(s.size)

    s.add_listener(on_change)
    s.set_size(20)
    s.set_size(20)  # Redundant, should not fire
    s.set_opacity(0.5)

    assert len(fired) == 2
    assert fired == [20, 20]

    s.remove_listener(on_change)
    s.set_size(30)
    assert len(fired) == 2


def test_brush_preset_model_immutability():
    """Verify BrushPreset is a frozen immutable dataclass."""
    p = BrushPreset(name="Ink", size=6, opacity=1.0, is_builtin=True)
    assert p.name == "Ink"
    assert p.is_builtin

    with pytest.raises(Exception):
        p.size = 10  # Frozen dataclass mutation must raise


def test_stroke_domain_model():
    """Verify StrokePoint and Stroke tracking."""
    stroke = Stroke()
    assert stroke.is_active
    assert stroke.point_count == 0

    p1 = stroke.add_point(10.0, 20.0, pressure=0.8)
    p2 = stroke.add_point(15.0, 25.0, pressure=0.9)

    assert stroke.point_count == 2
    assert stroke.first_point == p1
    assert stroke.last_point == p2
    assert p1.x == 10.0 and p1.y == 20.0
    assert abs(p1.pressure - 0.8) < 1e-4

    stroke.close()
    assert not stroke.is_active
    assert stroke.end_time is not None


# --- 2. Input Normalization ---

def test_input_normalizer_from_tuples_and_objects():
    """Verify InputNormalizer normalizes raw points and custom objects."""
    pt1 = InputNormalizer.normalize_point((45.5, 92.3), pressure=0.75)
    assert isinstance(pt1, PointerState)
    assert pt1.x == 45.5
    assert pt1.y == 92.3
    assert abs(pt1.pressure - 0.75) < 1e-4
    assert pt1.pointer_type == PointerType.MOUSE

    # Object with x and y callables
    class DummyQtPoint:
        def x(self): return 120.0
        def y(self): return 80.0
        def pressure(self): return 0.5

    pt2 = InputNormalizer.normalize_point(DummyQtPoint())
    assert pt2.x == 120.0
    assert pt2.y == 80.0
    assert abs(pt2.pressure - 0.5) < 1e-4


# --- 3. Engine & Dab Generation ---

def test_dab_generator_and_renderer():
    """Verify dab generator creates valid RGBA image with radial falloff."""
    gen = DabGenerator()
    settings = BrushSettings(size=16, hardness=0.5, opacity=1.0, flow=1.0, color=(255, 0, 0, 255))
    dab = gen.generate_dab(settings)

    assert isinstance(dab, Image.Image)
    assert dab.mode == "RGBA"
    assert dab.size == (16, 16)

    # Caching
    dab2 = gen.generate_dab(settings)
    assert dab is dab2

    # Invalidate
    gen.invalidate()
    dab3 = gen.generate_dab(settings)
    assert dab3 is not dab

    # RasterBrushEngine adheres to IBrushEngine protocol
    engine = RasterBrushEngine()
    assert isinstance(engine, IBrushEngine)

    target = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
    stamped = engine.render_point(target, settings, StrokePoint(50.0, 50.0))
    assert stamped
    # Verify pixels were stamped in target
    assert any(p[3] > 0 for p in target.getdata())


def test_eraser_rendering():
    """Verify eraser mode reduces or removes alpha from target."""
    target = Image.new("RGBA", (40, 40), (255, 0, 0, 255))
    settings = BrushSettings(size=20, hardness=1.0, opacity=1.0, flow=1.0, is_eraser=True)
    engine = RasterBrushEngine()
    engine.render_point(target, settings, StrokePoint(20.0, 20.0))

    # Center pixel should now be fully erased (alpha == 0)
    center_alpha = target.getpixel((20, 20))[3]
    assert center_alpha == 0


# --- 4. Preset Persistence & Resilience ---

def test_preset_storage_resilience():
    """Verify PresetStorage handles missing and corrupted JSON gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "corrupt.json")
        storage = PresetStorage(path)

        # Missing file
        assert storage.load_presets() == []

        # Corrupted JSON syntax
        with open(path, "w", encoding="utf-8") as f:
            f.write("{ invalid json [ [")
        assert storage.load_presets() == []

        # Non-list JSON
        with open(path, "w", encoding="utf-8") as f:
            f.write('{"name": "Not a list"}')
        assert storage.load_presets() == []

        # Save and reload valid presets
        p = BrushPreset("Test Pencil", size=2, is_builtin=False)
        assert storage.save_presets([p])
        loaded = storage.load_presets()
        assert len(loaded) == 1
        assert loaded[0].name == "Test Pencil"


def test_preset_manager_immutability_and_crud():
    """Verify BrushPresetManager enforces built-in safety and user preset CRUD."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage_path = os.path.join(tmpdir, "presets.json")
        mgr = BrushPresetManager(storage_path)

        # Built-in presets cannot be deleted
        assert not mgr.delete_user_preset("Basic Round")
        assert mgr.get_preset("Basic Round") is not None

        # Create user preset
        s = BrushSettings(size=44)
        up = mgr.create_user_preset("Custom Wash", s)
        assert up.name == "Custom Wash"
        assert up.size == 44

        # Delete user preset
        assert mgr.delete_user_preset("Custom Wash")
        assert mgr.get_preset("Custom Wash") is None


# --- 5. Controller & Document Integration ---

def test_stroke_controller_no_op_protection(qapp):
    """Verify StrokeController records no history for strokes with no pixel modification."""
    doc = Document()
    doc.new_document(100, 100, (255, 255, 255, 255))
    initial_history_len = len(doc.history._undo_stack)

    settings = BrushSettings(size=10, opacity=0.0)  # 0 opacity = no pixel change
    controller = StrokeController(settings)

    controller.start_stroke((50, 50), doc)
    controller.continue_stroke((55, 55), doc)
    committed = controller.end_stroke(doc)

    assert not committed
    assert len(doc.history._undo_stack) == initial_history_len


def test_stroke_controller_successful_commit_and_undo(qapp):
    """Verify meaningful strokes commit to history and undo restores exact pixels."""
    doc = Document()
    doc.new_document(100, 100, (255, 255, 255, 255))
    before_bytes = doc.active_layer.image.tobytes()

    settings = BrushSettings(size=12, opacity=1.0, color=(0, 0, 0, 255))
    controller = StrokeController(settings)

    controller.start_stroke((50, 50), doc)
    controller.continue_stroke((60, 60), doc)
    committed = controller.end_stroke(doc)

    assert committed
    assert doc.active_layer.image.tobytes() != before_bytes

    # Undo must restore exact initial pixels
    doc.history.undo()
    assert doc.active_layer.image.tobytes() == before_bytes


# --- 6. BrushTool Adapter ---

def test_brush_tool_adapter(qapp):
    """Verify BrushTool delegates to BrushController and conforms to BaseTool."""
    tool = BrushTool()
    assert tool.name == "Brush"
    assert tool.controller is not None

    tool.size = 25
    assert tool.settings.size == 25
    assert tool.controller.settings.size == 25

    tool.increase_size(4)
    assert tool.size == 29

    tool.decrease_size(2)
    assert tool.size == 27
