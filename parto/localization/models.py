# parto/localization/models.py
"""
Parto Localization Subsystem — Data Models and Enums
Defines core representations of locales, text directions, schemas, and diagnostics.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any


class TextDirection(str, Enum):
    """Supported text directions for typographic layouts."""
    LTR = "ltr"
    RTL = "rtl"

    @classmethod
    def from_string(cls, val: str) -> TextDirection:
        normalized = str(val).strip().lower()
        if normalized in ("rtl", "right-to-left", "right_to_left"):
            return cls.RTL
        return cls.LTR


CATALOG_SCHEMA_VERSION = "1.0.0"
SUPPORTED_SCHEMA_VERSIONS = ("1.0.0",)


# -----------------------------------------------------------------------------
# Subsystem Exceptions
# -----------------------------------------------------------------------------

class LocalizationError(Exception):
    """Base exception for all localization subsystem operations."""
    pass


class CatalogError(LocalizationError):
    """Base exception for catalog loading, discovery, and validation errors."""
    pass


class CatalogNotFoundError(CatalogError):
    """Raised when a requested translation catalog cannot be found on disk."""
    pass


class CatalogValidationError(CatalogError):
    """Raised when a translation catalog fails schema or content validation."""
    pass


class DuplicateCatalogError(CatalogError):
    """Raised when registering a catalog that is already registered without explicit replacement."""
    pass


class InvalidLocaleIdentifierError(LocalizationError):
    """Raised when a language identifier is malformed or invalid."""
    pass


class LocaleSwitchError(LocalizationError):
    """Raised when an atomic runtime locale switch operation fails."""
    pass


def is_valid_locale_id(locale_id: Any) -> bool:
    """
    Validate BCP 47 compliant language identifier syntax.
    Rejects path traversal, null bytes, separators, and non-alphanumeric patterns.
    Valid examples: 'en', 'fa', 'en-US', 'pt-BR', 'fa_IR', 'zh-Hans', 'sr-Latn-RS'.
    """
    if not isinstance(locale_id, str):
        return False
    lid = locale_id.strip()
    if not lid or len(lid) > 35:
        return False
    # Path traversal and injection defense
    if any(c in lid for c in ("/", "\\", "..", "\0", " ", "\t", "\n", "\r", ":", "*", "?", '"', "<", ">", "|")):
        return False
    import re
    pattern = r"^[a-zA-Z]{2,3}(?:[-_][a-zA-Z]{4})?(?:[-_](?:[a-zA-Z]{2}|[0-9]{3}))?(?:[-_][a-zA-Z0-9]{1,8})*$"
    return bool(re.match(pattern, lid))


def canonicalize_locale_id(locale_id: str) -> str:
    """
    Canonicalize a valid locale identifier into standard BCP 47 casing (e.g. 'en', 'en-US', 'pt-BR', 'zh-Hans').
    Hyphens are used as the canonical subtag separator.
    """
    if not is_valid_locale_id(locale_id):
        raise InvalidLocaleIdentifierError(f"Invalid or malformed locale identifier: {locale_id!r}")

    lid = locale_id.strip()
    sep = "_" if "_" in lid else "-"

    # Attempt Babel parsing if available
    try:
        from babel import Locale as BabelLocale
        loc = BabelLocale.parse(lid, sep=sep)
        parts = [loc.language.lower()]
        if loc.script:
            parts.append(loc.script.title())
        if loc.territory:
            parts.append(loc.territory.upper())
        if loc.variant:
            parts.append(str(loc.variant).lower())
        return "-".join(parts)
    except Exception:
        pass

    # Pure Python BCP 47 canonicalization fallback
    import re
    tokens = re.split(r"[-_]", lid)
    parts = [tokens[0].lower()]
    for token in tokens[1:]:
        if len(token) == 4 and token.isalpha():
            parts.append(token.title())
        elif (len(token) == 2 and token.isalpha()) or (len(token) == 3 and token.isdigit()):
            parts.append(token.upper())
        else:
            parts.append(token.lower())
    return "-".join(parts)


normalize_locale_id = canonicalize_locale_id


@dataclass(frozen=True)
class LocaleMetadata:
    """
    Immutable representation of language catalog metadata.
    BCP 47 compatible language identifier.
    """
    id: str
    name: str
    native_name: str
    direction: TextDirection = TextDirection.LTR
    version: str = "1.0.0"
    author: str = ""
    plural_rule: str = "cardinal"
    extra: Dict[str, Any] = field(default_factory=dict)

    @property
    def is_rtl(self) -> bool:
        return self.direction == TextDirection.RTL

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "native_name": self.native_name,
            "direction": self.direction.value,
            "version": self.version,
            "author": self.author,
            "plural_rule": self.plural_rule,
            **self.extra,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LocaleMetadata:
        raw_id = str(data.get("id", "")).strip()
        lang_id = canonicalize_locale_id(raw_id) if is_valid_locale_id(raw_id) else raw_id
        name = str(data.get("name", lang_id)).strip()
        native_name = str(data.get("native_name", name)).strip()
        dir_val = data.get("direction", "ltr")
        direction = TextDirection.from_string(dir_val)
        version = str(data.get("version", "1.0.0"))
        author = str(data.get("author", ""))
        plural_rule = str(data.get("plural_rule", "cardinal"))

        reserved = {"id", "name", "native_name", "direction", "version", "author", "plural_rule"}
        extra = {k: v for k, v in data.items() if k not in reserved}

        return cls(
            id=lang_id,
            name=name,
            native_name=native_name,
            direction=direction,
            version=version,
            author=author,
            plural_rule=plural_rule,
            extra=extra,
        )


@dataclass
class DiagnosticRecord:
    """Diagnostic entry tracking missing keys, catalog errors, or interpolation warnings."""
    level: str  # "warning", "error", "info"
    message: str
    locale_id: Optional[str] = None
    key: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
