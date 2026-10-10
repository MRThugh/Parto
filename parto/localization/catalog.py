# parto/localization/catalog.py
"""
Parto Localization Subsystem — Translation Catalog
Immutable in-memory catalog representation for a language pack.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from typing import Dict, Union, Optional, Set, List
from .models import LocaleMetadata, TextDirection


class TranslationCatalog:
    """
    In-memory representation of a validated language catalog.
    Maintains locale metadata and stable-key translation entries.
    """

    def __init__(
        self,
        metadata: LocaleMetadata,
        translations: Dict[str, Union[str, Dict[str, str]]],
        filepath: Optional[str] = None,
    ):
        self.metadata = metadata
        self._translations = dict(translations)
        self.filepath = filepath

    @property
    def id(self) -> str:
        return self.metadata.id if self.metadata else ""

    @property
    def locale_id(self) -> str:
        return self.metadata.id if self.metadata else ""

    @property
    def name(self) -> str:
        return self.metadata.name if self.metadata else ""

    @property
    def native_name(self) -> str:
        return self.metadata.native_name if self.metadata else ""

    @property
    def direction(self) -> TextDirection:
        return self.metadata.direction if self.metadata else TextDirection.LTR

    @property
    def is_rtl(self) -> bool:
        return self.metadata.is_rtl

    def get(self, key: str) -> Optional[Union[str, Dict[str, str]]]:
        """Look up translation entry by key."""
        return self._translations.get(key)

    def has(self, key: str) -> bool:
        """Check if message key exists in catalog."""
        return key in self._translations

    def keys(self) -> Set[str]:
        """Return all message keys in catalog."""
        return set(self._translations.keys())

    def count(self) -> int:
        """Total number of translation entries."""
        return len(self._translations)

    def __len__(self) -> int:
        return len(self._translations)

    def __contains__(self, key: str) -> bool:
        return key in self._translations

    def to_dict(self) -> dict:
        """Serialize back to catalog dictionary format."""
        return {
            "schema_version": self.metadata.version,
            "metadata": self.metadata.to_dict(),
            "translations": self._translations,
        }

    def get_placeholders(self, key: str) -> Set[str]:
        """Return all named placeholders for a given translation key."""
        entry = self.get(key)
        if not entry:
            return set()
        from .formatting import extract_placeholders
        if isinstance(entry, str):
            return extract_placeholders(entry)
        if isinstance(entry, dict):
            res: Set[str] = set()
            for v in entry.values():
                if isinstance(v, str):
                    res.update(extract_placeholders(v))
            return res
        return set()

    def is_complete_against(self, reference: TranslationCatalog) -> Tuple[bool, Set[str]]:
        """Check if catalog contains all keys from reference catalog. Returns (is_complete, missing_keys)."""
        ref_keys = reference.keys()
        cur_keys = self.keys()
        missing = ref_keys - cur_keys
        return len(missing) == 0, missing

    def validate(self, reference: Optional[TranslationCatalog] = None) -> List[str]:
        """
        Validate catalog entries for structural and type correctness.
        If a reference catalog is provided, also validates placeholder compatibility.
        """
        from .loader import LanguageCatalogLoader
        errors: List[str] = []
        is_valid, err = LanguageCatalogLoader.validate_catalog_dict(self.to_dict())
        if not is_valid and err:
            errors.append(err)
        if reference is not None:
            mismatches = LanguageCatalogLoader.validate_placeholder_compatibility(self, reference)
            errors.extend(mismatches)
        return errors
