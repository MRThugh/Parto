# parto/brush/presets/preset_manager.py
"""
Parto Brush System — Preset Manager
Coordinates built-in factory presets and user-authored presets.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import List, Optional
from ..models.preset import BrushPreset
from ..models.settings import BrushSettings
from .builtin import get_builtin_presets
from .storage import PresetStorage, get_default_presets_path


class BrushPresetManager:
    """
    Coordinates built-in and user-defined brush presets.
    Guarantees built-in immutability and safe user persistence.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self._storage = PresetStorage(storage_path or get_default_presets_path())
        self._builtin_presets: List[BrushPreset] = get_builtin_presets()
        self._user_presets: List[BrushPreset] = []
        self._active_preset_name: Optional[str] = "Basic Round"
        self.load_user_presets()

    @property
    def storage_path(self) -> str:
        return self._storage.filepath

    @storage_path.setter
    def storage_path(self, path: str) -> None:
        self._storage = PresetStorage(path)

    @property
    def active_preset_name(self) -> Optional[str]:
        return self._active_preset_name

    @active_preset_name.setter
    def active_preset_name(self, name: Optional[str]) -> None:
        self._active_preset_name = name

    def get_all_presets(self) -> List[BrushPreset]:
        """Return combined list of built-in and user-defined presets."""
        return list(self._builtin_presets) + list(self._user_presets)

    def get_builtin_presets(self) -> List[BrushPreset]:
        """Return factory built-in presets."""
        return list(self._builtin_presets)

    def get_user_presets(self) -> List[BrushPreset]:
        """Return user-authored presets."""
        return list(self._user_presets)

    def get_preset(self, name: str) -> Optional[BrushPreset]:
        """Lookup preset by name (case-insensitive)."""
        target = name.strip().lower()
        for p in self.get_all_presets():
            if p.name.strip().lower() == target:
                return p
        return None

    def apply_preset(self, name: str, settings: BrushSettings) -> bool:
        """
        Locate preset by name and apply its parameters to BrushSettings.
        Returns True on success, False if preset not found.
        """
        preset = self.get_preset(name)
        if preset:
            preset.apply_to(settings)
            self._active_preset_name = preset.name
            return True
        return False

    def create_user_preset(
        self,
        name: str,
        settings: BrushSettings,
        description: str = "",
    ) -> BrushPreset:
        """
        Capture current brush parameters into a new custom user preset.
        Guarantees unique naming and non-interference with built-in presets.
        """
        clean_name = name.strip()
        if not clean_name:
            clean_name = f"Custom {len(self._user_presets) + 1}"

        # Prevent shadowing built-in presets
        for b in self._builtin_presets:
            if b.name.lower() == clean_name.lower():
                clean_name = f"{clean_name} (User)"
                break

        # Remove duplicate existing user preset with same name
        self._user_presets = [p for p in self._user_presets if p.name.lower() != clean_name.lower()]

        preset = BrushPreset(
            name=clean_name,
            size=settings.size,
            opacity=settings.opacity,
            flow=getattr(settings, "flow", 1.0),
            hardness=settings.hardness,
            spacing=getattr(settings, "spacing", 0.25),
            is_eraser=getattr(settings, "is_eraser", False),
            is_builtin=False,
            description=description,
        )
        self._user_presets.append(preset)
        self._active_preset_name = preset.name
        self.save_user_presets()
        return preset

    def delete_user_preset(self, name: str) -> bool:
        """
        Delete a custom user preset. Rejects deletion of factory built-ins.
        """
        clean_name = name.strip().lower()
        # Strictly forbid deleting built-in presets
        for b in self._builtin_presets:
            if b.name.strip().lower() == clean_name:
                return False

        before_len = len(self._user_presets)
        self._user_presets = [p for p in self._user_presets if p.name.strip().lower() != clean_name]
        if len(self._user_presets) < before_len:
            if self._active_preset_name and self._active_preset_name.strip().lower() == clean_name:
                self._active_preset_name = "Basic Round"
            self.save_user_presets()
            return True
        return False

    def save_user_presets(self) -> None:
        """Persist user presets to disk storage."""
        self._storage.save_presets(self._user_presets)

    def load_user_presets(self) -> None:
        """Reload user presets from disk storage."""
        self._user_presets = self._storage.load_presets()
