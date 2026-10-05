# parto/brush/presets/builtin.py
"""
Parto Brush System — Built-in Presets
Immutable factory for Parto standard factory brush presets.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from typing import List
from ..models.preset import BrushPreset


def get_builtin_presets() -> List[BrushPreset]:
    """
    Returns the authoritative list of factory built-in brush presets.
    Each preset is marked is_builtin=True to guard against deletion.
    """
    return [
        BrushPreset(
            name="Basic Round",
            size=12,
            opacity=1.0,
            flow=1.0,
            hardness=0.8,
            spacing=0.25,
            is_eraser=False,
            is_builtin=True,
            description="Standard general-purpose brush",
        ),
        BrushPreset(
            name="Soft Round",
            size=24,
            opacity=0.8,
            flow=0.8,
            hardness=0.15,
            spacing=0.20,
            is_eraser=False,
            is_builtin=True,
            description="Soft feathered edges for blending",
        ),
        BrushPreset(
            name="Hard Round",
            size=16,
            opacity=1.0,
            flow=1.0,
            hardness=1.0,
            spacing=0.20,
            is_eraser=False,
            is_builtin=True,
            description="Crisp, sharp solid round brush",
        ),
        BrushPreset(
            name="Pencil",
            size=2,
            opacity=0.95,
            flow=1.0,
            hardness=0.95,
            spacing=0.15,
            is_eraser=False,
            is_builtin=True,
            description="Fine line sketching tool",
        ),
        BrushPreset(
            name="Ink",
            size=6,
            opacity=1.0,
            flow=1.0,
            hardness=0.9,
            spacing=0.10,
            is_eraser=False,
            is_builtin=True,
            description="Fluid continuous inking line",
        ),
        BrushPreset(
            name="Marker",
            size=22,
            opacity=0.55,
            flow=0.75,
            hardness=0.7,
            spacing=0.18,
            is_eraser=False,
            is_builtin=True,
            description="Semi-transparent layering marker",
        ),
        BrushPreset(
            name="Airbrush",
            size=40,
            opacity=0.35,
            flow=0.45,
            hardness=0.02,
            spacing=0.15,
            is_eraser=False,
            is_builtin=True,
            description="Diffuse soft aerosol spray",
        ),
        BrushPreset(
            name="Eraser",
            size=20,
            opacity=1.0,
            flow=1.0,
            hardness=0.85,
            spacing=0.20,
            is_eraser=True,
            is_builtin=True,
            description="Erases pixels from the active layer",
        ),
    ]
