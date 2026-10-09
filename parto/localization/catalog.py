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
        return self.metadata.id

    @property
    def locale_id(self) -> str:
        return self.metadata.id

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def native_name(self) -> str:
        return self.metadata.native_name

    @property
    def direction(self) -> TextDirection:
        return self.metadata.direction

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

    def validate(self) -> List[str]:
        """Validate catalog entries for structural and type correctness."""
        errors: List[str] = []
        if not self.metadata.id:
            errors.append("Catalog metadata missing 'id'.")
        if not self._translations:
            errors.append(f"Catalog '{self.id}' contains no translation entries.")

        for k, v in self._translations.items():
            if not isinstance(k, str) or not k.strip():
                errors.append(f"Invalid key format: {k!r}")
            if not isinstance(v, (str, dict)):
                errors.append(f"Key '{k}' must map to a string or plural dictionary, got {type(v).__name__}")
            elif isinstance(v, dict):
                for p_cat, p_val in v.items():
                    if not isinstance(p_val, str):
                        errors.append(f"Plural key '{k}[{p_cat}]' must map to string, got {type(p_val).__name__}")
        return errors
