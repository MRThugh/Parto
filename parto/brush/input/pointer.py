# parto/brush/input/pointer.py
"""
Parto Brush System — Normalized Pointer Input State
Pure Python, zero UI dependencies.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from ..models.enums import PointerType


@dataclass(frozen=True)
class PointerState:
    """
    Standardized, platform-agnostic pointer input sample.
    Decouples brush controllers from specific GUI framework event classes.
    """
    x: float
    y: float
    pressure: float = 1.0
    tilt_x: float = 0.0
    tilt_y: float = 0.0
    buttons: int = 1
    timestamp: float = field(default_factory=time.time)
    pointer_type: PointerType = PointerType.MOUSE
