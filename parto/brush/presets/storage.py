# parto/brush/presets/storage.py
"""
Parto Brush System — Preset Persistence and File Storage
Handles reading/writing brush preset files with corruption-resilient parsing.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import os
import json
import logging
from typing import List, Optional
from ..models.preset import BrushPreset

logger = logging.getLogger("parto.brush.presets.storage")


def get_default_presets_path() -> str:
    """Return filesystem location for user brush presets, with safe fallbacks."""
    try:
        from PySide6.QtCore import QStandardPaths
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    except Exception:
        base = ""

    if not base:
        base = os.path.expanduser("~/.parto")

    return os.path.join(base, "brush_presets.json")


class PresetStorage:
    """
    Manages filesystem serialization and deserialization of user presets.
    Guarantees corrupted or malformed files do not crash the application.
    """

    def __init__(self, filepath: Optional[str] = None):
        self.filepath: str = filepath or get_default_presets_path()

    def save_presets(self, presets: List[BrushPreset]) -> bool:
        """
        Serialize user presets to disk as formatted JSON.
        Returns True on success, False on error.
        """
        try:
            folder = os.path.dirname(self.filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)

            data = [p.to_dict() for p in presets if not p.is_builtin]
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Could not persist user brush presets to {self.filepath}: {e}")
            return False

    def load_presets(self) -> List[BrushPreset]:
        """
        Read user presets from disk. Recovers gracefully from non-existent or corrupted files.
        """
        if not os.path.exists(self.filepath):
            return []

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                logger.warning(f"Preset file {self.filepath} did not contain a JSON list.")
                return []

            results: List[BrushPreset] = []
            for item in data:
                if isinstance(item, dict) and "name" in item:
                    try:
                        preset = BrushPreset.from_dict(item, is_builtin=False)
                        results.append(preset)
                    except Exception as parse_err:
                        logger.warning(f"Skipping malformed preset record: {parse_err}")

            return results
        except Exception as e:
            logger.warning(f"Failed to read presets from {self.filepath}: {e}")
            return []

    def export_preset(self, preset: BrushPreset, target_path: str) -> bool:
        """Export a single preset to a JSON file."""
        try:
            folder = os.path.dirname(target_path)
            if folder:
                os.makedirs(folder, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(preset.to_dict(), f, indent=2)
            return True
        except Exception as e:
            logger.warning(f"Could not export preset to {target_path}: {e}")
            return False

    def import_preset(self, source_path: str) -> Optional[BrushPreset]:
        """Import a preset from a JSON file."""
        if not os.path.exists(source_path):
            return None
        try:
            with open(source_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return BrushPreset.from_dict(data, is_builtin=False)
            elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                return BrushPreset.from_dict(data[0], is_builtin=False)
            return None
        except Exception as e:
            logger.warning(f"Could not import preset from {source_path}: {e}")
            return None
