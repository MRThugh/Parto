# parto/tools/brush.py
"""
Parto v0.3.0 - Freehand Brush Compatibility Module
Re-exports from dedicated, self-contained subsystem 'parto.brush'.
Author: Ali Kamrani (MRThugh / علی کامرانی)
"""

from __future__ import annotations

from ..brush import (
    BrushSettings,
    BrushRenderer,
    StrokeController,
    BrushTool,
    BrushPreset,
    BrushPresetManager,
    get_default_presets_path,
    IBrushEngine,
    RasterBrushEngine,
    DabGenerator,
    Stroke,
    StrokePoint,
    PointerState,
    InputNormalizer,
    BrushDocumentAdapter,
    BrushController,
)

__all__ = [
    "BrushSettings",
    "BrushRenderer",
    "StrokeController",
    "BrushTool",
    "BrushPreset",
    "BrushPresetManager",
    "get_default_presets_path",
    "IBrushEngine",
    "RasterBrushEngine",
    "DabGenerator",
    "Stroke",
    "StrokePoint",
    "PointerState",
    "InputNormalizer",
    "BrushDocumentAdapter",
    "BrushController",
]
