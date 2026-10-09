# parto/localization/loader.py
"""
Parto Localization Subsystem — Language Catalog Loader & Validator
Discovers, validates, and instantiates language catalogs from JSON language packs.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import os
import json
import logging
from typing import Dict, List, Optional, Tuple, Any

from .models import (
    LocaleMetadata,
    TextDirection,
    CATALOG_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
)
from .catalog import TranslationCatalog

logger = logging.getLogger("parto.localization.loader")


class LanguageCatalogLoader:
    """
    Dedicated loader and validator for language catalog JSON files.
    
    Guarantees:
    - Pure data loading: never executes Python code from packs.
    - Strict validation of schema versions, identifiers, and types.
    - Corrupted or malformed catalogs are rejected safely with clear diagnostics.
    - Automatic catalog discovery across standard resource directories.
    """

    @classmethod
    def validate_catalog_dict(cls, data: Any) -> Tuple[bool, Optional[str]]:
        """
        Validate in-memory dictionary representation of a catalog.
        Returns (is_valid, error_message).
        """
        if not isinstance(data, dict):
            return False, f"Catalog root must be a JSON object, got {type(data).__name__}"

        schema_ver = data.get("schema_version")
        if not schema_ver:
            return False, "Catalog missing 'schema_version' field"
        if str(schema_ver) not in SUPPORTED_SCHEMA_VERSIONS:
            return False, (
                f"Unsupported catalog schema version '{schema_ver}'. "
                f"Supported versions: {', '.join(SUPPORTED_SCHEMA_VERSIONS)}"
            )

        metadata_dict = data.get("metadata")
        if not isinstance(metadata_dict, dict):
            return False, "Catalog missing or invalid 'metadata' object"

        lang_id = metadata_dict.get("id")
        if not lang_id or not isinstance(lang_id, str) or not lang_id.strip():
            return False, "Metadata missing valid 'id' identifier"

        # Validate direction if provided
        direction = metadata_dict.get("direction", "ltr")
        if str(direction).lower() not in ("ltr", "rtl"):
            return False, f"Invalid direction '{direction}', must be 'ltr' or 'rtl'"

        translations = data.get("translations")
        if not isinstance(translations, dict):
            return False, "Catalog missing or invalid 'translations' dictionary"

        if len(translations) == 0:
            return False, "Catalog contains empty 'translations' dictionary"

        # Validate each key and entry
        for k, v in translations.items():
            if not isinstance(k, str) or not k.strip():
                return False, f"Invalid translation key: {k!r}"
            if not isinstance(v, (str, dict)):
                return False, (
                    f"Translation for '{k}' must be string or plural object, "
                    f"got {type(v).__name__}"
                )
            if isinstance(v, dict):
                for p_cat, p_val in v.items():
                    if not isinstance(p_val, str):
                        return False, (
                            f"Plural entry '{k}[{p_cat}]' must be string, "
                            f"got {type(p_val).__name__}"
                        )

        return True, None

    @classmethod
    def load_from_dict(
        cls,
        data: Dict[str, Any],
        filepath: Optional[str] = None,
    ) -> Tuple[Optional[TranslationCatalog], Optional[str]]:
        """Instantiate TranslationCatalog from validated dictionary."""
        is_valid, err = cls.validate_catalog_dict(data)
        if not is_valid:
            return None, err

        try:
            metadata = LocaleMetadata.from_dict(data["metadata"])
            catalog = TranslationCatalog(
                metadata=metadata,
                translations=data["translations"],
                filepath=filepath,
            )
            return catalog, None
        except Exception as e:
            return None, f"Failed to construct TranslationCatalog: {e}"

    @classmethod
    def load_from_file(
        cls,
        filepath: str,
    ) -> Tuple[Optional[TranslationCatalog], Optional[str]]:
        """
        Safely read, parse, and validate a catalog from disk.
        Returns (catalog, None) on success, (None, error_str) on failure.
        """
        if not os.path.exists(filepath):
            return None, f"Catalog file not found: {filepath}"

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except UnicodeDecodeError as e:
            return None, f"UTF-8 decode failure in '{filepath}': {e}"
        except OSError as e:
            return None, f"I/O error reading '{filepath}': {e}"

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            return None, f"Malformed JSON in '{filepath}' at line {e.lineno}, col {e.colno}: {e.msg}"

        catalog, err = cls.load_from_dict(data, filepath=filepath)
        if err:
            logger.warning(f"Catalog validation failed for '{filepath}': {err}")
        return catalog, err

    @classmethod
    def discover_catalogs(
        cls,
        directories: List[str],
    ) -> Dict[str, TranslationCatalog]:
        """
        Scan listed directories for locale catalogs.
        Looks for:
        1. <dir>/<locale_id>/locale.json
        2. <dir>/<locale_id>.json
        
        Returns mapping of locale_id -> TranslationCatalog.
        """
        discovered: Dict[str, TranslationCatalog] = {}

        for root_dir in directories:
            if not root_dir or not os.path.isdir(root_dir):
                continue

            try:
                entries = sorted(os.listdir(root_dir))
            except OSError as e:
                logger.warning(f"Failed to list directory '{root_dir}': {e}")
                continue

            for entry in entries:
                full_path = os.path.join(root_dir, entry)

                # Subdirectory structure: <dir>/<locale>/locale.json
                if os.path.isdir(full_path):
                    candidate_file = os.path.join(full_path, "locale.json")
                    if os.path.isfile(candidate_file):
                        cat, err = cls.load_from_file(candidate_file)
                        if cat:
                            discovered[cat.id] = cat
                        else:
                            logger.warning(f"Skipping malformed catalog '{candidate_file}': {err}")

                # Flat structure: <dir>/<locale>.json
                elif os.path.isfile(full_path) and entry.lower().endswith(".json") and entry.lower() != "package.json":
                    cat, err = cls.load_from_file(full_path)
                    if cat:
                        discovered[cat.id] = cat
                    else:
                        logger.warning(f"Skipping malformed catalog '{full_path}': {err}")

        return discovered
