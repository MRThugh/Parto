# parto/brush/controller/brush_controller.py
"""
Parto Brush System — Central Brush Domain Controller
Coordinates settings, presets, stroke lifecycle, and engine operations.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Optional, Tuple
from ..models.settings import BrushSettings
from ..models.preset import BrushPreset
from ..presets.preset_manager import BrushPresetManager
from ..engine.renderer import BrushRenderer
from ..engine.brush_engine import RasterBrushEngine
from .stroke_controller import StrokeController


class BrushController:
    """
    High-level facade coordinating the brush subsystem.
    Owns authoritative settings, preset manager, stroke controller, and engine.
    """

    def __init__(
        self,
        settings: Optional[BrushSettings] = None,
        preset_manager: Optional[BrushPresetManager] = None,
    ):
        self.settings: BrushSettings = settings or BrushSettings()
        self.preset_manager: BrushPresetManager = preset_manager or BrushPresetManager()
        self.renderer: BrushRenderer = BrushRenderer()
        self.engine: RasterBrushEngine = RasterBrushEngine(self.renderer)
        self.stroke_controller: StrokeController = StrokeController(
            self.settings, self.engine
        )

    # --- Preset Management ---

    def apply_preset(self, name: str) -> bool:
        """Apply named preset to authoritative settings."""
        return self.preset_manager.apply_preset(name, self.settings)

    def create_preset(self, name: str, description: str = "") -> BrushPreset:
        """Save current configuration as a new user preset."""
        return self.preset_manager.create_user_preset(name, self.settings, description)

    def delete_preset(self, name: str) -> bool:
        """Delete user preset by name."""
        return self.preset_manager.delete_user_preset(name)

    # --- Setting Modifiers ---

    def set_size(self, size: int) -> None:
        self.settings.set_size(size)
        self.renderer.invalidate_cache()

    def set_opacity(self, opacity: float) -> None:
        self.settings.set_opacity(opacity)
        self.renderer.invalidate_cache()

    def set_flow(self, flow: float) -> None:
        self.settings.set_flow(flow)
        self.renderer.invalidate_cache()

    def set_hardness(self, hardness: float) -> None:
        self.settings.set_hardness(hardness)
        self.renderer.invalidate_cache()

    def set_spacing(self, spacing: float) -> None:
        self.settings.set_spacing(spacing)

    def set_is_eraser(self, is_eraser: bool) -> None:
        self.settings.set_is_eraser(is_eraser)
        self.renderer.invalidate_cache()

    def set_color(self, color: Tuple[int, int, int, int]) -> None:
        self.settings.set_color(color)
        self.renderer.invalidate_cache()

    def set_background_color(self, color: Tuple[int, int, int, int]) -> None:
        self.settings.set_background_color(color)

    def swap_colors(self) -> None:
        self.settings.swap_colors()
        self.renderer.invalidate_cache()

    def reset_default_colors(self) -> None:
        self.settings.reset_default_colors()
        self.renderer.invalidate_cache()
