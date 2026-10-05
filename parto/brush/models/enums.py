# parto/brush/models/enums.py
"""
Parto Brush System — Domain Enumerations
Pure Python, zero UI dependencies.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from enum import Enum, auto


class BlendMode(Enum):
    """Supported brush blending modes."""
    NORMAL = "normal"
    MULTIPLY = "multiply"
    SCREEN = "screen"
    OVERLAY = "overlay"
    DARKEN = "darken"
    LIGHTEN = "lighten"


class BrushShapeType(Enum):
    """Base brush tip geometry types."""
    ROUND = "round"
    SQUARE = "square"
    CUSTOM = "custom"


class PointerType(Enum):
    """Input device source classification."""
    MOUSE = "mouse"
    PEN = "pen"
    ERASER = "eraser"
    TOUCH = "touch"
