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
        success = self.preset_manager.apply_preset(name, self.settings)
        if success:
            self.renderer.invalidate_cache()
        return success

    def create_preset(
        self,
        name: str,
        description: str = "",
        category: str = "Custom",
    ) -> BrushPreset:
        """Save current configuration as a new user preset."""
        return self.preset_manager.create_user_preset(
            name, self.settings, description=description, category=category
        )

    def duplicate_preset(self, name: str) -> Optional[BrushPreset]:
        """Duplicate existing preset."""
        return self.preset_manager.duplicate_user_preset(name)

    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """Rename an existing user preset."""
        return self.preset_manager.rename_user_preset(old_name, new_name)

    def toggle_favorite(self, name: str) -> bool:
        """Toggle favorite state of a preset."""
        return self.preset_manager.toggle_favorite(name)

    def export_preset(self, name: str, filepath: str) -> bool:
        """Export preset to JSON file."""
        return self.preset_manager.export_preset(name, filepath)

    def import_preset(self, filepath: str) -> Optional[BrushPreset]:
        """Import preset from JSON file."""
        return self.preset_manager.import_preset(filepath)

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

    def set_angle(self, angle: float) -> None:
        self.settings.set_angle(angle)
        self.renderer.invalidate_cache()

    def set_roundness(self, roundness: float) -> None:
        self.settings.set_roundness(roundness)
        self.renderer.invalidate_cache()

    def set_smoothing(self, smoothing: float) -> None:
        self.settings.set_smoothing(smoothing)

    def set_scatter(self, scatter: float) -> None:
        self.settings.set_scatter(scatter)

    def set_blend_mode(self, mode: Any) -> None:
        self.settings.blend_mode = mode

    def set_dynamics_size(self, val: str) -> None:
        self.settings.set_dynamics_size(val)

    def set_dynamics_opacity(self, val: str) -> None:
        self.settings.set_dynamics_opacity(val)

    def set_dynamics_flow(self, val: str) -> None:
        self.settings.set_dynamics_flow(val)

    def set_dynamics_angle(self, val: str) -> None:
        self.settings.set_dynamics_angle(val)

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

    def reset_to_defaults(self) -> None:
        self.settings.reset_to_defaults()
        self.renderer.invalidate_cache()
