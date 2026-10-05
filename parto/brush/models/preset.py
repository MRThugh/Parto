# parto/brush/models/preset.py
"""
Parto Brush System — Brush Preset Model
Pure Python, zero UI dependencies.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any
from .settings import BrushSettings


@dataclass(frozen=True)
class BrushPreset:
    """
    Immutable data representation of a brush configuration preset.
    Zero UI or tool dependencies.
    """
    name: str
    size: int = 12
    opacity: float = 1.0
    flow: float = 1.0
    hardness: float = 0.8
    spacing: float = 0.25
    is_eraser: bool = False
    is_builtin: bool = False
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert preset configuration to a JSON-compatible dictionary."""
        return {
            "name": self.name,
            "size": self.size,
            "opacity": self.opacity,
            "flow": self.flow,
            "hardness": self.hardness,
            "spacing": self.spacing,
            "is_eraser": self.is_eraser,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], is_builtin: bool = False) -> BrushPreset:
        """Construct a validated preset from dictionary data."""
        return cls(
            name=str(data.get("name", "Custom")).strip(),
            size=int(data.get("size", 12)),
            opacity=float(data.get("opacity", 1.0)),
            flow=float(data.get("flow", 1.0)),
            hardness=float(data.get("hardness", 0.8)),
            spacing=float(data.get("spacing", 0.25)),
            is_eraser=bool(data.get("is_eraser", False)),
            is_builtin=is_builtin,
            description=str(data.get("description", "")),
        )

    def apply_to(self, settings: BrushSettings) -> None:
        """Apply this preset's parameters to authoritative BrushSettings."""
        settings.size = self.size
        settings.opacity = self.opacity
        settings.flow = self.flow
        settings.hardness = self.hardness
        settings.spacing = self.spacing
        settings.is_eraser = self.is_eraser
        settings.notify_changed()
