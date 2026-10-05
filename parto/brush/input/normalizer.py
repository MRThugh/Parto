# parto/brush/input/normalizer.py
"""
Parto Brush System — Input Normalization Adapter
Converts platform GUI events or raw coordinates into normalized PointerState.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import time
from typing import Any
from ..models.enums import PointerType
from .pointer import PointerState


class InputNormalizer:
    """
    Normalizes coordinates and input events from PySide6 or abstract sources
    into uniform PointerState representations.
    """

    @staticmethod
    def normalize_point(
        pt: Any,
        pressure: float = 1.0,
        tilt_x: float = 0.0,
        tilt_y: float = 0.0,
        buttons: int = 1,
        pointer_type: PointerType = PointerType.MOUSE,
    ) -> PointerState:
        """
        Convert arbitrary point object (QPointF, QPoint, tuple, list, or object with x/y)
        into a canonical PointerState.
        """
        if hasattr(pt, "x") and hasattr(pt, "y"):
            px = float(pt.x() if callable(pt.x) else pt.x)
            py = float(pt.y() if callable(pt.y) else pt.y)
        elif isinstance(pt, (tuple, list)) and len(pt) >= 2:
            px = float(pt[0])
            py = float(pt[1])
        else:
            px = 0.0
            py = 0.0

        p_pressure = pressure
        if hasattr(pt, "pressure"):
            try:
                p_pressure = float(pt.pressure() if callable(pt.pressure) else pt.pressure)
            except Exception:
                pass

        return PointerState(
            x=px,
            y=py,
            pressure=max(0.0, min(1.0, p_pressure)),
            tilt_x=tilt_x,
            tilt_y=tilt_y,
            buttons=buttons,
            timestamp=time.time(),
            pointer_type=pointer_type,
        )

    @classmethod
    def from_mouse_event(cls, event: Any, scene_pos: Any) -> PointerState:
        """
        Normalize a Qt QMouseEvent and scene position into PointerState.
        """
        buttons = 1
        if hasattr(event, "buttons"):
            try:
                buttons = int(event.buttons())
            except Exception:
                buttons = 1

        return cls.normalize_point(
            scene_pos,
            pressure=1.0,
            buttons=buttons,
            pointer_type=PointerType.MOUSE,
        )

    @classmethod
    def from_tablet_event(cls, event: Any, scene_pos: Any) -> PointerState:
        """
        Normalize a Qt QTabletEvent and scene position into PointerState.
        """
        pressure = 1.0
        if hasattr(event, "pressure"):
            try:
                pressure = float(event.pressure())
            except Exception:
                pressure = 1.0

        tilt_x = 0.0
        tilt_y = 0.0
        if hasattr(event, "xTilt"):
            try:
                tilt_x = float(event.xTilt())
                tilt_y = float(event.yTilt())
            except Exception:
                pass

        p_type = PointerType.PEN
        if hasattr(event, "pointerType"):
            try:
                name = str(event.pointerType()).lower()
                if "eraser" in name:
                    p_type = PointerType.ERASER
            except Exception:
                pass

        return cls.normalize_point(
            scene_pos,
            pressure=pressure,
            tilt_x=tilt_x,
            tilt_y=tilt_y,
            pointer_type=p_type,
        )
