# parto/ui/panels/brush_panel.py
"""
Parto Brush Studio — Backward Compatibility Facade
Re-exports BrushStudioDock, BrushDock, and BrushPanel from parto.ui.panels.brush.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from .brush.dock import BrushStudioDock, BrushDock, BrushPanel
from .brush.header import BrushStudioHeader
from .brush.presets import BrushPresetsSection
from .brush.properties import BrushTipPropertiesSection
from .brush.dynamics import BrushDynamicsSection
from .brush.color import BrushColorSection
from .brush.blend import BrushBlendSection
from .brush.advanced import BrushAdvancedSection

__all__ = [
    "BrushStudioDock",
    "BrushDock",
    "BrushPanel",
    "BrushStudioHeader",
    "BrushPresetsSection",
    "BrushTipPropertiesSection",
    "BrushDynamicsSection",
    "BrushColorSection",
    "BrushBlendSection",
    "BrushAdvancedSection",
]
