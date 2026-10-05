# parto/brush/models/stroke.py
"""
Parto Brush System — Stroke Domain Representation
Represents an editing stroke operation, decoupled from Qt events.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Optional
from .settings import BrushSettings


@dataclass(frozen=True)
class StrokePoint:
    """
    Normalized spatial point within a stroke trajectory.
    """
    x: float
    y: float
    pressure: float = 1.0
    tilt_x: float = 0.0
    tilt_y: float = 0.0
    timestamp: float = field(default_factory=time.time)


class Stroke:
    """
    Encapsulates a logical stroke operation containing sampled trajectory points,
    snapshot of brush configuration at execution time, and outcome metrics.
    """

    def __init__(self, settings_snapshot: Optional[BrushSettings] = None):
        self.points: List[StrokePoint] = []
        self.settings_snapshot: Optional[BrushSettings] = (
            settings_snapshot.copy() if settings_snapshot else None
        )
        self.start_time: float = time.time()
        self.end_time: Optional[float] = None
        self.is_active: bool = True
        self.pixels_modified: bool = False

    def add_point(
        self,
        x: float,
        y: float,
        pressure: float = 1.0,
        tilt_x: float = 0.0,
        tilt_y: float = 0.0,
        timestamp: Optional[float] = None,
    ) -> StrokePoint:
        pt = StrokePoint(
            x=float(x),
            y=float(y),
            pressure=float(pressure),
            tilt_x=float(tilt_x),
            tilt_y=float(tilt_y),
            timestamp=timestamp if timestamp is not None else time.time(),
        )
        self.points.append(pt)
        return pt

    def close(self) -> None:
        self.is_active = False
        self.end_time = time.time()

    @property
    def point_count(self) -> int:
        return len(self.points)

    @property
    def first_point(self) -> Optional[StrokePoint]:
        return self.points[0] if self.points else None

    @property
    def last_point(self) -> Optional[StrokePoint]:
        return self.points[-1] if self.points else None
