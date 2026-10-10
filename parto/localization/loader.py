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
    is_valid_locale_id,
    canonicalize_locale_id,
)
from .catalog import TranslationCatalog
from .formatting import validate_placeholder_syntax, extract_placeholders

logger = logging.getLogger("parto.localization.loader")

VALID_PLURAL_CATEGORIES = {"zero", "one", "two", "few", "many", "other"}


class LanguageCatalogLoader:
    """
    Dedicated loader and validator for language catalog JSON files.
    
    Guarantees:
    - Pure data loading: never executes Python code from packs.
    - Strict validation of schema versions, identifiers, types, and placeholders.
    - Corrupted or malformed catalogs are rejected safely with clear diagnostics.
    - Path traversal defense and automatic catalog discovery across standard resource directories.
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
        if not lang_id or not isinstance(lang_id, str) or not is_valid_locale_id(lang_id):
            return False, f"Metadata contains invalid or malformed locale identifier: {lang_id!r}"

        name = metadata_dict.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            return False, "Metadata has invalid 'name' field"

        native_name = metadata_dict.get("native_name")
        if native_name is not None and (not isinstance(native_name, str) or not native_name.strip()):
            return False, "Metadata has invalid 'native_name' field"

        # Validate direction if provided
        direction = metadata_dict.get("direction", "ltr")
        if str(direction).lower() not in ("ltr", "rtl"):
            return False, f"Invalid direction '{direction}', must be 'ltr' or 'rtl'"

        translations = data.get("translations")
        if not isinstance(translations, dict):
            return False, "Catalog missing or invalid 'translations' dictionary"

        if len(translations) == 0:
            return False, "Catalog contains empty 'translations' dictionary"

        # Validate each key, entry, and placeholder
        for k, v in translations.items():
            if not isinstance(k, str) or not k.strip():
                return False, f"Invalid translation key: {k!r}"
            if not isinstance(v, (str, dict)):
                return False, (
                    f"Translation for '{k}' must be string or plural object, "
                    f"got {type(v).__name__}"
                )
            if isinstance(v, str):
                p_valid, p_err = validate_placeholder_syntax(v)
                if not p_valid:
                    return False, f"Translation entry '{k}' has invalid placeholder syntax: {p_err}"
            elif isinstance(v, dict):
                if len(v) == 0:
                    return False, f"Plural entry for '{k}' cannot be empty"
                for p_cat, p_val in v.items():
                    if p_cat not in VALID_PLURAL_CATEGORIES:
                        return False, (
                            f"Invalid plural category '{p_cat}' in '{k}'. "
                            f"Allowed categories: {', '.join(sorted(VALID_PLURAL_CATEGORIES))}"
                        )
                    if not isinstance(p_val, str):
                        return False, (
                            f"Plural entry '{k}[{p_cat}]' must be string, "
                            f"got {type(p_val).__name__}"
                        )
                    p_valid, p_err = validate_placeholder_syntax(p_val)
                    if not p_valid:
                        return False, f"Plural entry '{k}[{p_cat}]' has invalid placeholder syntax: {p_err}"

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
        Scan listed directories for locale catalogs with path traversal protection.
        Looks for:
        1. <dir>/<locale_id>/locale.json
        2. <dir>/<locale_id>.json
        
        Returns mapping of locale_id -> TranslationCatalog.
        Maintains deterministic first-discovery-wins policy for duplicates.
        """
        discovered: Dict[str, TranslationCatalog] = {}

        for raw_dir in directories:
            if not raw_dir:
                continue
            root_dir = os.path.abspath(raw_dir)
            if not os.path.isdir(root_dir):
                continue

            try:
                entries = sorted(os.listdir(root_dir))
            except OSError as e:
                logger.warning(f"Failed to list directory '{root_dir}': {e}")
                continue

            for entry in entries:
                # Prevent directory traversal attacks
                if entry in (".", "..") or "/" in entry or "\\" in entry:
                    continue

                full_path = os.path.abspath(os.path.join(root_dir, entry))
                # Ensure the resolved path remains strictly within root_dir
                try:
                    if os.path.commonpath([root_dir, full_path]) != root_dir:
                        logger.warning(f"Path traversal detected and blocked: '{entry}' in '{root_dir}'")
                        continue
                except ValueError:
                    continue

                # Subdirectory structure: <dir>/<locale>/locale.json
                if os.path.isdir(full_path):
                    candidate_file = os.path.abspath(os.path.join(full_path, "locale.json"))
                    if os.path.isfile(candidate_file):
                        cat, err = cls.load_from_file(candidate_file)
                        if cat:
                            norm_id = canonicalize_locale_id(cat.id) if is_valid_locale_id(cat.id) else cat.id
                            if norm_id in discovered:
                                logger.warning(
                                    f"Deterministic discovery: Ignoring duplicate locale '{norm_id}' "
                                    f"at '{candidate_file}', keeping previously discovered at '{discovered[norm_id].filepath}'"
                                )
                            else:
                                discovered[norm_id] = cat
                        else:
                            logger.warning(f"Skipping malformed catalog '{candidate_file}': {err}")

                # Flat structure: <dir>/<locale>.json
                elif os.path.isfile(full_path) and entry.lower().endswith(".json") and entry.lower() != "package.json":
                    cat, err = cls.load_from_file(full_path)
                    if cat:
                        norm_id = canonicalize_locale_id(cat.id) if is_valid_locale_id(cat.id) else cat.id
                        if norm_id in discovered:
                            logger.warning(
                                f"Deterministic discovery: Ignoring duplicate locale '{norm_id}' "
                                f"at '{full_path}', keeping previously discovered at '{discovered[norm_id].filepath}'"
                            )
                        else:
                            discovered[norm_id] = cat
                    else:
                        logger.warning(f"Skipping malformed catalog '{full_path}': {err}")

        return discovered

    @classmethod
    def validate_placeholder_compatibility(
        cls,
        candidate: TranslationCatalog,
        fallback: TranslationCatalog,
    ) -> List[str]:
        """
        Verify named interpolation placeholders in candidate catalog match fallback catalog.
        Returns list of mismatch error descriptions identifying the locale, key, and mismatch nature.
        """
        mismatches: List[str] = []
        for key in candidate.keys():
            if not fallback.has(key):
                continue

            cand_val = candidate.get(key)
            fall_val = fallback.get(key)

            cand_placeholders: Set[str] = set()
            fall_placeholders: Set[str] = set()

            if isinstance(cand_val, str):
                cand_placeholders = extract_placeholders(cand_val)
            elif isinstance(cand_val, dict):
                for p_str in cand_val.values():
                    if isinstance(p_str, str):
                        cand_placeholders.update(extract_placeholders(p_str))

            if isinstance(fall_val, str):
                fall_placeholders = extract_placeholders(fall_val)
            elif isinstance(fall_val, dict):
                for p_str in fall_val.values():
                    if isinstance(p_str, str):
                        fall_placeholders.update(extract_placeholders(p_str))

            if cand_placeholders != fall_placeholders:
                missing_in_cand = fall_placeholders - cand_placeholders
                extra_in_cand = cand_placeholders - fall_placeholders
                details = []
                if missing_in_cand:
                    details.append(f"missing in candidate: {sorted(missing_in_cand)}")
                if extra_in_cand:
                    details.append(f"extra in candidate: {sorted(extra_in_cand)}")
                diff_str = "; ".join(details) if details else f"candidate={sorted(cand_placeholders)}, fallback={sorted(fall_placeholders)}"
                mismatches.append(
                    f"Key '{key}' placeholder mismatch in locale '{candidate.id}': {diff_str} (fallback '{fallback.id}')"
                )

        return mismatches
