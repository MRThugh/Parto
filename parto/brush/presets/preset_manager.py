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
        category: str = "Custom",
        favorite: bool = False,
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
            category=category or "Custom",
            angle=getattr(settings, "angle", 0.0),
            roundness=getattr(settings, "roundness", 1.0),
            smoothing=getattr(settings, "smoothing", 0.0),
            scatter=getattr(settings, "scatter", 0.0),
            blend_mode=settings.blend_mode.value if hasattr(settings.blend_mode, "value") else str(settings.blend_mode),
            dynamics_size=getattr(settings, "dynamics_size", "off"),
            dynamics_opacity=getattr(settings, "dynamics_opacity", "off"),
            dynamics_flow=getattr(settings, "dynamics_flow", "off"),
            dynamics_angle=getattr(settings, "dynamics_angle", "off"),
            favorite=favorite,
        )
        self._user_presets.append(preset)
        self._active_preset_name = preset.name
        self.save_user_presets()
        return preset

    def duplicate_user_preset(self, name: str) -> Optional[BrushPreset]:
        """Duplicate an existing preset as a new user preset."""
        src = self.get_preset(name)
        if not src:
            return None

        base_name = f"{src.name} Copy"
        clean_name = base_name
        counter = 2
        all_names = {p.name.lower() for p in self.get_all_presets()}
        while clean_name.lower() in all_names:
            clean_name = f"{base_name} {counter}"
            counter += 1

        new_preset = BrushPreset(
            name=clean_name,
            size=src.size,
            opacity=src.opacity,
            flow=src.flow,
            hardness=src.hardness,
            spacing=src.spacing,
            is_eraser=src.is_eraser,
            is_builtin=False,
            description=src.description or f"Copy of {src.name}",
            category=src.category if src.category != "Basic" else "Custom",
            angle=src.angle,
            roundness=src.roundness,
            smoothing=src.smoothing,
            scatter=src.scatter,
            blend_mode=src.blend_mode,
            dynamics_size=src.dynamics_size,
            dynamics_opacity=src.dynamics_opacity,
            dynamics_flow=src.dynamics_flow,
            dynamics_angle=src.dynamics_angle,
            favorite=src.favorite,
        )
        self._user_presets.append(new_preset)
        self._active_preset_name = new_preset.name
        self.save_user_presets()
        return new_preset

    def rename_user_preset(self, old_name: str, new_name: str) -> bool:
        """Rename an existing user preset."""
        clean_old = old_name.strip().lower()
        clean_new = new_name.strip()
        if not clean_new:
            return False

        # Strictly disallow renaming built-in presets
        for b in self._builtin_presets:
            if b.name.strip().lower() == clean_old or b.name.strip().lower() == clean_new.lower():
                return False

        idx = -1
        for i, p in enumerate(self._user_presets):
            if p.name.strip().lower() == clean_old:
                idx = i
                break
        if idx == -1:
            return False

        src = self._user_presets[idx]
        renamed = BrushPreset(
            name=clean_new,
            size=src.size,
            opacity=src.opacity,
            flow=src.flow,
            hardness=src.hardness,
            spacing=src.spacing,
            is_eraser=src.is_eraser,
            is_builtin=False,
            description=src.description,
            category=src.category,
            angle=src.angle,
            roundness=src.roundness,
            smoothing=src.smoothing,
            scatter=src.scatter,
            blend_mode=src.blend_mode,
            dynamics_size=src.dynamics_size,
            dynamics_opacity=src.dynamics_opacity,
            dynamics_flow=src.dynamics_flow,
            dynamics_angle=src.dynamics_angle,
            favorite=src.favorite,
        )
        self._user_presets[idx] = renamed
        if self._active_preset_name and self._active_preset_name.strip().lower() == clean_old:
            self._active_preset_name = renamed.name
        self.save_user_presets()
        return True

    def toggle_favorite(self, name: str) -> bool:
        """Toggle favorite state of a preset."""
        clean = name.strip().lower()
        for i, p in enumerate(self._user_presets):
            if p.name.strip().lower() == clean:
                toggled = BrushPreset(
                    name=p.name,
                    size=p.size,
                    opacity=p.opacity,
                    flow=p.flow,
                    hardness=p.hardness,
                    spacing=p.spacing,
                    is_eraser=p.is_eraser,
                    is_builtin=False,
                    description=p.description,
                    category=p.category,
                    angle=p.angle,
                    roundness=p.roundness,
                    smoothing=p.smoothing,
                    scatter=p.scatter,
                    blend_mode=p.blend_mode,
                    dynamics_size=p.dynamics_size,
                    dynamics_opacity=p.dynamics_opacity,
                    dynamics_flow=p.dynamics_flow,
                    dynamics_angle=p.dynamics_angle,
                    favorite=not p.favorite,
                )
                self._user_presets[i] = toggled
                self.save_user_presets()
                return True
        return False

    def export_preset(self, name: str, filepath: str) -> bool:
        """Export preset to specified json path."""
        p = self.get_preset(name)
        if not p:
            return False
        return self._storage.export_preset(p, filepath)

    def import_preset(self, filepath: str) -> Optional[BrushPreset]:
        """Import preset from json path into user presets."""
        p = self._storage.import_preset(filepath)
        if not p:
            return None

        # Clean name to avoid collision with builtins
        clean_name = p.name
        for b in self._builtin_presets:
            if b.name.lower() == clean_name.lower():
                clean_name = f"{clean_name} (Imported)"
                break

        # Remove duplicate user preset if existing
        self._user_presets = [u for u in self._user_presets if u.name.lower() != clean_name.lower()]

        imported = BrushPreset(
            name=clean_name,
            size=p.size,
            opacity=p.opacity,
            flow=p.flow,
            hardness=p.hardness,
            spacing=p.spacing,
            is_eraser=p.is_eraser,
            is_builtin=False,
            description=p.description or "Imported preset",
            category=p.category or "Custom",
            angle=p.angle,
            roundness=p.roundness,
            smoothing=p.smoothing,
            scatter=p.scatter,
            blend_mode=p.blend_mode,
            dynamics_size=p.dynamics_size,
            dynamics_opacity=p.dynamics_opacity,
            dynamics_flow=p.dynamics_flow,
            dynamics_angle=p.dynamics_angle,
            favorite=p.favorite,
        )
        self._user_presets.append(imported)
        self._active_preset_name = imported.name
        self.save_user_presets()
        return imported

    def filter_presets(
        self,
        query: str = "",
        category: Optional[str] = None,
        only_favorites: bool = False,
    ) -> List[BrushPreset]:
        """Filter presets by search text, category, and favorite flag."""
        q = query.strip().lower()
        cat = category.strip().lower() if category and category != "All" else None

        results = []
        for p in self.get_all_presets():
            if only_favorites and not p.favorite:
                continue
            if cat is not None and p.category.lower() != cat:
                continue
            if q and q not in p.name.lower():
                continue
            results.append(p)
        return results

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
