# parto/brush/__init__.py
"""
Parto Brush System — Dedicated, Modular Subsystem
Author & Maintainer: Ali Kamrani (علی کامرانی)

Exports primary domain models, engine interfaces, controllers, presets, and tool integration.
"""

from .models.enums import BlendMode, BrushShapeType, PointerType
from .models.settings import BrushSettings
from .models.preset import BrushPreset
from .models.stroke import StrokePoint, Stroke

from .engine.dab import DabGenerator
from .engine.renderer import BrushRenderer
from .engine.brush_engine import IBrushEngine, RasterBrushEngine

from .input.pointer import PointerState
from .input.normalizer import InputNormalizer

from .presets.builtin import get_builtin_presets
from .presets.storage import PresetStorage, get_default_presets_path
from .presets.preset_manager import BrushPresetManager

from .document_adapter import BrushDocumentAdapter

from .controller.stroke_controller import StrokeController
from .controller.brush_controller import BrushController

from .tools.brush_tool import BrushTool

__all__ = [
    # Models
    "BlendMode",
    "BrushShapeType",
    "PointerType",
    "BrushSettings",
    "BrushPreset",
    "StrokePoint",
    "Stroke",
    # Engine
    "DabGenerator",
    "BrushRenderer",
    "IBrushEngine",
    "RasterBrushEngine",
    # Input
    "PointerState",
    "InputNormalizer",
    # Presets
    "get_builtin_presets",
    "PresetStorage",
    "get_default_presets_path",
    "BrushPresetManager",
    # Document Adapter
    "BrushDocumentAdapter",
    # Controller
    "StrokeController",
    "BrushController",
    # Tool
    "BrushTool",
]
