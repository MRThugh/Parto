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
    MIN_ANGLE: float = 0.0
    MAX_ANGLE: float = 360.0
    MIN_ROUNDNESS: float = 0.01
    MAX_ROUNDNESS: float = 1.0

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
        angle: float = 0.0,
        roundness: float = 1.0,
        smoothing: float = 0.0,
        scatter: float = 0.0,
        size_jitter: float = 0.0,
        angle_jitter: float = 0.0,
        dynamics_size: str = "off",
        dynamics_opacity: str = "off",
        dynamics_flow: str = "off",
        dynamics_angle: str = "off",
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
        self._angle: float = float(angle) % 360.0
        self._roundness: float = self._clamp_float(roundness, self.MIN_ROUNDNESS, self.MAX_ROUNDNESS)
        self._smoothing: float = self._clamp_float(smoothing, 0.0, 1.0)
        self._scatter: float = self._clamp_float(scatter, 0.0, 1.0)
        self._size_jitter: float = self._clamp_float(size_jitter, 0.0, 1.0)
        self._angle_jitter: float = self._clamp_float(angle_jitter, 0.0, 1.0)
        self._dynamics_size: str = str(dynamics_size).lower()
        self._dynamics_opacity: str = str(dynamics_opacity).lower()
        self._dynamics_flow: str = str(dynamics_flow).lower()
        self._dynamics_angle: str = str(dynamics_angle).lower()
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

    @property
    def angle(self) -> float:
        return self._angle

    @angle.setter
    def angle(self, val: float) -> None:
        self.set_angle(val)

    def set_angle(self, angle: float) -> None:
        clamped = float(angle) % 360.0
        if abs(self._angle - clamped) > 1e-4:
            self._angle = clamped
            self.notify_changed()

    @property
    def roundness(self) -> float:
        return self._roundness

    @roundness.setter
    def roundness(self, val: float) -> None:
        self.set_roundness(val)

    def set_roundness(self, roundness: float) -> None:
        clamped = self._clamp_float(roundness, self.MIN_ROUNDNESS, self.MAX_ROUNDNESS)
        if abs(self._roundness - clamped) > 1e-4:
            self._roundness = clamped
            self.notify_changed()

    @property
    def smoothing(self) -> float:
        return self._smoothing

    @smoothing.setter
    def smoothing(self, val: float) -> None:
        self.set_smoothing(val)

    def set_smoothing(self, smoothing: float) -> None:
        clamped = self._clamp_float(smoothing, 0.0, 1.0)
        if abs(self._smoothing - clamped) > 1e-4:
            self._smoothing = clamped
            self.notify_changed()

    @property
    def scatter(self) -> float:
        return self._scatter

    @scatter.setter
    def scatter(self, val: float) -> None:
        self.set_scatter(val)

    def set_scatter(self, scatter: float) -> None:
        clamped = self._clamp_float(scatter, 0.0, 1.0)
        if abs(self._scatter - clamped) > 1e-4:
            self._scatter = clamped
            self.notify_changed()

    @property
    def size_jitter(self) -> float:
        return self._size_jitter

    @size_jitter.setter
    def size_jitter(self, val: float) -> None:
        self.set_size_jitter(val)

    def set_size_jitter(self, val: float) -> None:
        clamped = self._clamp_float(val, 0.0, 1.0)
        if abs(self._size_jitter - clamped) > 1e-4:
            self._size_jitter = clamped
            self.notify_changed()

    @property
    def angle_jitter(self) -> float:
        return self._angle_jitter

    @angle_jitter.setter
    def angle_jitter(self, val: float) -> None:
        self.set_angle_jitter(val)

    def set_angle_jitter(self, val: float) -> None:
        clamped = self._clamp_float(val, 0.0, 1.0)
        if abs(self._angle_jitter - clamped) > 1e-4:
            self._angle_jitter = clamped
            self.notify_changed()

    @property
    def dynamics_size(self) -> str:
        return self._dynamics_size

    @dynamics_size.setter
    def dynamics_size(self, val: str) -> None:
        self.set_dynamics_size(val)

    def set_dynamics_size(self, val: str) -> None:
        v = str(val).lower()
        if self._dynamics_size != v:
            self._dynamics_size = v
            self.notify_changed()

    @property
    def dynamics_opacity(self) -> str:
        return self._dynamics_opacity

    @dynamics_opacity.setter
    def dynamics_opacity(self, val: str) -> None:
        self.set_dynamics_opacity(val)

    def set_dynamics_opacity(self, val: str) -> None:
        v = str(val).lower()
        if self._dynamics_opacity != v:
            self._dynamics_opacity = v
            self.notify_changed()

    @property
    def dynamics_flow(self) -> str:
        return self._dynamics_flow

    @dynamics_flow.setter
    def dynamics_flow(self, val: str) -> None:
        self.set_dynamics_flow(val)

    def set_dynamics_flow(self, val: str) -> None:
        v = str(val).lower()
        if self._dynamics_flow != v:
            self._dynamics_flow = v
            self.notify_changed()

    @property
    def dynamics_angle(self) -> str:
        return self._dynamics_angle

    @dynamics_angle.setter
    def dynamics_angle(self, val: str) -> None:
        self.set_dynamics_angle(val)

    def set_dynamics_angle(self, val: str) -> None:
        v = str(val).lower()
        if self._dynamics_angle != v:
            self._dynamics_angle = v
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

    def reset_to_defaults(self) -> None:
        """Reset all parameters to standard basic defaults."""
        self._size = 8
        self._opacity = 1.0
        self._flow = 1.0
        self._hardness = 0.8
        self._spacing = 0.25
        self._is_eraser = False
        self._blend_mode = BlendMode.NORMAL
        self._angle = 0.0
        self._roundness = 1.0
        self._smoothing = 0.0
        self._scatter = 0.0
        self._size_jitter = 0.0
        self._angle_jitter = 0.0
        self._dynamics_size = "off"
        self._dynamics_opacity = "off"
        self._dynamics_flow = "off"
        self._dynamics_angle = "off"
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
            "angle": self._angle,
            "roundness": self._roundness,
            "smoothing": self._smoothing,
            "scatter": self._scatter,
            "size_jitter": self._size_jitter,
            "angle_jitter": self._angle_jitter,
            "dynamics_size": self._dynamics_size,
            "dynamics_opacity": self._dynamics_opacity,
            "dynamics_flow": self._dynamics_flow,
            "dynamics_angle": self._dynamics_angle,
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
            angle=data.get("angle", 0.0),
            roundness=data.get("roundness", 1.0),
            smoothing=data.get("smoothing", 0.0),
            scatter=data.get("scatter", 0.0),
            size_jitter=data.get("size_jitter", 0.0),
            angle_jitter=data.get("angle_jitter", 0.0),
            dynamics_size=data.get("dynamics_size", "off"),
            dynamics_opacity=data.get("dynamics_opacity", "off"),
            dynamics_flow=data.get("dynamics_flow", "off"),
            dynamics_angle=data.get("dynamics_angle", "off"),
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
            angle=self._angle,
            roundness=self._roundness,
            smoothing=self._smoothing,
            scatter=self._scatter,
            size_jitter=self._size_jitter,
            angle_jitter=self._angle_jitter,
            dynamics_size=self._dynamics_size,
            dynamics_opacity=self._dynamics_opacity,
            dynamics_flow=self._dynamics_flow,
            dynamics_angle=self._dynamics_angle,
        )
