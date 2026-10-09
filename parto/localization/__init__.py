# parto/localization/__init__.py
"""
Parto Localization Subsystem (i18n / l10n)
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from .models import (
    LocaleMetadata,
    TextDirection,
    DiagnosticRecord,
    CATALOG_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    LocalizationError,
    CatalogError,
    CatalogNotFoundError,
    CatalogValidationError,
    InvalidLocaleIdentifierError,
    LocaleSwitchError,
    is_valid_locale_id,
)
from .catalog import TranslationCatalog
from .loader import LanguageCatalogLoader
from .formatting import (
    safe_interpolate,
    get_plural_category,
    resolve_translation_entry,
    extract_placeholders,
    validate_placeholder_syntax,
)
from .persistence import LocalePreferences
from .manager import (
    LocalizationManager,
    get_localization_manager,
    t,
)

__all__ = [
    "LocaleMetadata",
    "TextDirection",
    "DiagnosticRecord",
    "CATALOG_SCHEMA_VERSION",
    "SUPPORTED_SCHEMA_VERSIONS",
    "LocalizationError",
    "CatalogError",
    "CatalogNotFoundError",
    "CatalogValidationError",
    "InvalidLocaleIdentifierError",
    "LocaleSwitchError",
    "is_valid_locale_id",
    "TranslationCatalog",
    "LanguageCatalogLoader",
    "safe_interpolate",
    "get_plural_category",
    "resolve_translation_entry",
    "extract_placeholders",
    "validate_placeholder_syntax",
    "LocalePreferences",
    "LocalizationManager",
    "get_localization_manager",
    "t",
]
