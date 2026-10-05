# parto/ui/panels/brush/__init__.py
"""
Parto Brush Studio Subsystem
Professional modular dock panel, header, preset grid, tip properties,
dynamics, color management, and blend controls.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from .dock import BrushStudioDock, BrushDock, BrushPanel
from .header import BrushStudioHeader
from .presets import BrushPresetsSection
from .properties import BrushTipPropertiesSection
from .dynamics import BrushDynamicsSection
from .color import BrushColorSection
from .blend import BrushBlendSection
from .advanced import BrushAdvancedSection

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
