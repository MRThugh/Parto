# parto/brush/models/settings.py
"""
Parto Brush System — Authoritative Brush Configuration State
Pure Python, zero UI dependencies.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Tuple, List, Callable, Dict, Any
from .enums import BlendMode


class BrushSettings:
    """
    Encapsulates brush configuration parameters and constraints.
    Authoritative range: 1 to 500 pixels.
    Zero Qt dependencies; pure Python domain model.
    """

    MIN_SIZE: int = 1
    MAX_SIZE: int = 500
    MIN_OPACITY: float = 0.0
    MAX_OPACITY: float = 1.0
    MIN_FLOW: float = 0.0
    MAX_FLOW: float = 1.0
    MIN_HARDNESS: float = 0.0
    MAX_HARDNESS: float = 1.0
    MIN_SPACING: float = 0.05
    MAX_SPACING: float = 2.0

    def __init__(
        self,
        size: int = 8,
        opacity: float = 1.0,
        hardness: float = 0.8,
        color: Tuple[int, int, int, int] = (0, 0, 0, 255),
        background_color: Tuple[int, int, int, int] = (255, 255, 255, 255),
        flow: float = 1.0,
        spacing: float = 0.25,
        is_eraser: bool = False,
        blend_mode: BlendMode | str = BlendMode.NORMAL,
    ):
        self._size: int = self._clamp_int(size, self.MIN_SIZE, self.MAX_SIZE)
        self._opacity: float = self._clamp_float(opacity, self.MIN_OPACITY, self.MAX_OPACITY)
        self._flow: float = self._clamp_float(flow, self.MIN_FLOW, self.MAX_FLOW)
        self._hardness: float = self._clamp_float(hardness, self.MIN_HARDNESS, self.MAX_HARDNESS)
        self._spacing: float = self._clamp_float(spacing, self.MIN_SPACING, self.MAX_SPACING)
        self._color: Tuple[int, int, int, int] = self._validate_color(color)
        self._background_color: Tuple[int, int, int, int] = self._validate_color(background_color)
        self._is_eraser: bool = bool(is_eraser)
        self._blend_mode: BlendMode = (
            blend_mode if isinstance(blend_mode, BlendMode) else BlendMode(str(blend_mode).lower())
        )
        self._listeners: List[Callable[[], None]] = []

    # --- Validation Utilities ---

    @staticmethod
    def _clamp_int(val: Any, low: int, high: int) -> int:
        try:
            return max(low, min(high, int(val)))
        except (ValueError, TypeError):
            return low

    @staticmethod
    def _clamp_float(val: Any, low: float, high: float) -> float:
        try:
            return max(low, min(high, float(val)))
        except (ValueError, TypeError):
            return low

    @staticmethod
    def _validate_color(c: Any) -> Tuple[int, int, int, int]:
        try:
            r, g, b, a = c[:4]
            return (
                max(0, min(255, int(r))),
                max(0, min(255, int(g))),
                max(0, min(255, int(b))),
                max(0, min(255, int(a))),
            )
        except (TypeError, ValueError, IndexError):
            return (0, 0, 0, 255)

    # --- Observer Pattern ---

    def add_listener(self, callback: Callable[[], None]) -> None:
        """Register an observer callback to be invoked on configuration change."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[], None]) -> None:
        """Remove a previously registered observer callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_changed(self) -> None:
        """Dispatch change notifications to all registered observers."""
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:
                pass

    # --- Properties with Change Detection ---

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, val: int) -> None:
        self.set_size(val)

    def set_size(self, size: int) -> None:
        clamped = self._clamp_int(size, self.MIN_SIZE, self.MAX_SIZE)
        if self._size != clamped:
            self._size = clamped
            self.notify_changed()

    @property
    def radius(self) -> int:
        return max(1, self._size // 2)

    @radius.setter
    def radius(self, value: int) -> None:
        self.set_size(max(1, min(self.MAX_SIZE, int(value) * 2)))

    @property
    def opacity(self) -> float:
        return self._opacity

    @opacity.setter
    def opacity(self, val: float) -> None:
        self.set_opacity(val)

    def set_opacity(self, opacity: float) -> None:
        clamped = self._clamp_float(opacity, self.MIN_OPACITY, self.MAX_OPACITY)
        if abs(self._opacity - clamped) > 1e-6:
            self._opacity = clamped
            self.notify_changed()

    @property
    def flow(self) -> float:
        return self._flow

    @flow.setter
    def flow(self, val: float) -> None:
        self.set_flow(val)

    def set_flow(self, flow: float) -> None:
        clamped = self._clamp_float(flow, self.MIN_FLOW, self.MAX_FLOW)
        if abs(self._flow - clamped) > 1e-6:
            self._flow = clamped
            self.notify_changed()

    @property
    def hardness(self) -> float:
        return self._hardness

    @hardness.setter
    def hardness(self, val: float) -> None:
        self.set_hardness(val)

    def set_hardness(self, hardness: float) -> None:
        clamped = self._clamp_float(hardness, self.MIN_HARDNESS, self.MAX_HARDNESS)
        if abs(self._hardness - clamped) > 1e-6:
            self._hardness = clamped
            self.notify_changed()

    @property
    def spacing(self) -> float:
        return self._spacing

    @spacing.setter
    def spacing(self, val: float) -> None:
        self.set_spacing(val)

    def set_spacing(self, spacing: float) -> None:
        clamped = self._clamp_float(spacing, self.MIN_SPACING, self.MAX_SPACING)
        if abs(self._spacing - clamped) > 1e-6:
            self._spacing = clamped
            self.notify_changed()

    @property
    def is_eraser(self) -> bool:
        return self._is_eraser

    @is_eraser.setter
    def is_eraser(self, val: bool) -> None:
        self.set_is_eraser(val)

    def set_is_eraser(self, is_eraser: bool) -> None:
        b = bool(is_eraser)
        if self._is_eraser != b:
            self._is_eraser = b
            self.notify_changed()

    @property
    def color(self) -> Tuple[int, int, int, int]:
        return self._color

    @color.setter
    def color(self, val: Tuple[int, int, int, int]) -> None:
        self.set_color(val)

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        validated = self._validate_color(color)
        if self._color != validated:
            self._color = validated
            self.notify_changed()

    @property
    def background_color(self) -> Tuple[int, int, int, int]:
        return self._background_color

    @background_color.setter
    def background_color(self, val: Tuple[int, int, int, int]) -> None:
        self.set_background_color(val)

    def set_background_color(self, color: Tuple[int, int, int, int]) -> None:
        validated = self._validate_color(color)
        if self._background_color != validated:
            self._background_color = validated
            self.notify_changed()

    @property
    def blend_mode(self) -> BlendMode:
        return self._blend_mode

    @blend_mode.setter
    def blend_mode(self, mode: BlendMode | str) -> None:
        new_mode = mode if isinstance(mode, BlendMode) else BlendMode(str(mode).lower())
        if self._blend_mode != new_mode:
            self._blend_mode = new_mode
            self.notify_changed()

    # --- Convenience Operations ---

    def increase_size(self, delta: int = 2) -> None:
        """Increase brush diameter by delta pixels."""
        self.set_size(self._size + delta)

    def decrease_size(self, delta: int = 2) -> None:
        """Decrease brush diameter by delta pixels."""
        self.set_size(self._size - delta)

    def swap_colors(self) -> None:
        """Swap foreground and background colors."""
        self._color, self._background_color = self._background_color, self._color
        self.notify_changed()

    def reset_default_colors(self) -> None:
        """Reset foreground to black and background to white."""
        self._color = (0, 0, 0, 255)
        self._background_color = (255, 255, 255, 255)
        self.notify_changed()

    # --- Serialization ---

    def to_dict(self) -> Dict[str, Any]:
        """Serialize configuration to a pure JSON-compatible dictionary."""
        return {
            "size": self._size,
            "opacity": self._opacity,
            "flow": self._flow,
            "hardness": self._hardness,
            "spacing": self._spacing,
            "color": list(self._color),
            "background_color": list(self._background_color),
            "is_eraser": self._is_eraser,
            "blend_mode": self._blend_mode.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BrushSettings:
        """Construct a validated BrushSettings instance from dictionary."""
        return cls(
            size=data.get("size", 8),
            opacity=data.get("opacity", 1.0),
            flow=data.get("flow", 1.0),
            hardness=data.get("hardness", 0.8),
            spacing=data.get("spacing", 0.25),
            color=tuple(data.get("color", [0, 0, 0, 255])),
            background_color=tuple(data.get("background_color", [255, 255, 255, 255])),
            is_eraser=data.get("is_eraser", False),
            blend_mode=data.get("blend_mode", BlendMode.NORMAL.value),
        )

    def copy(self) -> BrushSettings:
        """Create an independent copy of current settings."""
        return BrushSettings(
            size=self._size,
            opacity=self._opacity,
            hardness=self._hardness,
            color=self._color,
            background_color=self._background_color,
            flow=self._flow,
            spacing=self._spacing,
            is_eraser=self._is_eraser,
            blend_mode=self._blend_mode,
        )
