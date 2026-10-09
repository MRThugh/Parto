# parto/localization/persistence.py
"""
Parto Localization Subsystem — Locale Preference Persistence
Manages persisting user language selection across application runs.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import os
import json
import logging
from typing import Optional
from .models import is_valid_locale_id

logger = logging.getLogger("parto.localization.persistence")


def get_default_settings_path() -> str:
    """Return filesystem location for user application settings."""
    try:
        from PySide6.QtCore import QStandardPaths
        base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    except Exception:
        base = ""

    if not base:
        base = os.path.expanduser("~/.parto")

    return os.path.join(base, "settings.json")


class LocalePreferences:
    """
    Persistence adapter for locale preference.
    Resilient against disk write failures, path traversal, or file corruption.
    """

    def __init__(self, filepath: Optional[str] = None):
        self.filepath: str = filepath or get_default_settings_path()

    def get_preferred_locale(self, default: str = "en") -> str:
        """Load preferred locale code from settings file."""
        if not os.path.exists(self.filepath):
            return default

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                locale = data.get("locale")
                if locale and isinstance(locale, str) and is_valid_locale_id(locale.strip()):
                    return locale.strip()
        except Exception as e:
            logger.warning(f"Could not read locale preference from {self.filepath}: {e}")

        return default

    def set_preferred_locale(self, locale_id: str) -> bool:
        """Save preferred locale code to settings file."""
        if not is_valid_locale_id(locale_id):
            logger.warning(f"Refused to persist invalid locale identifier: {locale_id!r}")
            return False
        try:
            folder = os.path.dirname(self.filepath)
            if folder:
                os.makedirs(folder, exist_ok=True)

            data = {}
            if os.path.exists(self.filepath):
                try:
                    with open(self.filepath, "r", encoding="utf-8") as f:
                        existing = json.load(f)
                        if isinstance(existing, dict):
                            data = existing
                except Exception:
                    data = {}

            data["locale"] = str(locale_id).strip()

            # Write atomically using temporary file
            tmp_path = f"{self.filepath}.tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            os.replace(tmp_path, self.filepath)
            return True
        except Exception as e:
            logger.warning(f"Could not persist locale preference to {self.filepath}: {e}")
            return False
