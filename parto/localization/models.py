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
        lang_id = str(data.get("id", "")).strip()
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
