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
    category: str = "Basic"
    angle: float = 0.0
    roundness: float = 1.0
    smoothing: float = 0.0
    scatter: float = 0.0
    size_jitter: float = 0.0
    angle_jitter: float = 0.0
    blend_mode: str = "normal"
    dynamics_size: str = "off"
    dynamics_opacity: str = "off"
    dynamics_flow: str = "off"
    dynamics_angle: str = "off"
    favorite: bool = False

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
            "category": self.category,
            "angle": self.angle,
            "roundness": self.roundness,
            "smoothing": self.smoothing,
            "scatter": self.scatter,
            "size_jitter": self.size_jitter,
            "angle_jitter": self.angle_jitter,
            "blend_mode": self.blend_mode,
            "dynamics_size": self.dynamics_size,
            "dynamics_opacity": self.dynamics_opacity,
            "dynamics_flow": self.dynamics_flow,
            "dynamics_angle": self.dynamics_angle,
            "favorite": self.favorite,
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
            category=str(data.get("category", "Basic")),
            angle=float(data.get("angle", 0.0)),
            roundness=float(data.get("roundness", 1.0)),
            smoothing=float(data.get("smoothing", 0.0)),
            scatter=float(data.get("scatter", 0.0)),
            size_jitter=float(data.get("size_jitter", 0.0)),
            angle_jitter=float(data.get("angle_jitter", 0.0)),
            blend_mode=str(data.get("blend_mode", "normal")),
            dynamics_size=str(data.get("dynamics_size", "off")),
            dynamics_opacity=str(data.get("dynamics_opacity", "off")),
            dynamics_flow=str(data.get("dynamics_flow", "off")),
            dynamics_angle=str(data.get("dynamics_angle", "off")),
            favorite=bool(data.get("favorite", False)),
        )

    def apply_to(self, settings: BrushSettings) -> None:
        """Apply this preset's parameters to authoritative BrushSettings."""
        settings.size = self.size
        settings.opacity = self.opacity
        settings.flow = self.flow
        settings.hardness = self.hardness
        settings.spacing = self.spacing
        settings.is_eraser = self.is_eraser
        if hasattr(settings, "set_angle"):
            settings.set_angle(self.angle)
        if hasattr(settings, "set_roundness"):
            settings.set_roundness(self.roundness)
        if hasattr(settings, "set_smoothing"):
            settings.set_smoothing(self.smoothing)
        if hasattr(settings, "set_scatter"):
            settings.set_scatter(self.scatter)
        if hasattr(settings, "set_size_jitter"):
            settings.set_size_jitter(self.size_jitter)
        if hasattr(settings, "set_angle_jitter"):
            settings.set_angle_jitter(self.angle_jitter)
        if hasattr(settings, "blend_mode") and self.blend_mode:
            settings.blend_mode = self.blend_mode
        if hasattr(settings, "set_dynamics_size"):
            settings.set_dynamics_size(self.dynamics_size)
        if hasattr(settings, "set_dynamics_opacity"):
            settings.set_dynamics_opacity(self.dynamics_opacity)
        if hasattr(settings, "set_dynamics_flow"):
            settings.set_dynamics_flow(self.dynamics_flow)
        if hasattr(settings, "set_dynamics_angle"):
            settings.set_dynamics_angle(self.dynamics_angle)
        settings.notify_changed()
