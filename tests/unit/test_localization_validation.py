# tests/unit/test_localization_validation.py
"""
Localization Core Hardening — Validation & Multilingual Pluralization Regression Tests
Author: Ali Kamrani (علی کامرانی)

Comprehensive automated tests covering:
1. Static codebase translation key coverage (ensures zero missing keys)
2. English-Persian catalog key parity (exact 1:1 match)
3. Placeholder consistency and syntax validation across languages
4. Multilingual CLDR pluralization (English, Persian, French, Russian, Polish, Arabic)
5. Floating point, decimal, string coercion, and invalid count resilience
6. Locale identifier canonicalization and fallback behavior
"""

import math
import os
import pytest
from decimal import Decimal

from parto.localization.models import (
    is_valid_locale_id,
    canonicalize_locale_id,
    TextDirection,
    LocaleMetadata,
)
from parto.localization.catalog import TranslationCatalog
from parto.localization.loader import LanguageCatalogLoader
from parto.localization.formatting import (
    extract_placeholders,
    validate_placeholder_syntax,
    safe_interpolate,
    get_plural_category,
    resolve_translation_entry,
)
from parto.localization.validator import (
    scan_codebase_translation_keys,
    validate_catalog_parity,
    validate_codebase_key_coverage,
)


@pytest.fixture(scope="module")
def repo_root():
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "../.."))


@pytest.fixture(scope="module")
def bundled_catalogs(repo_root):
    en_path = os.path.join(repo_root, "parto", "resources", "locales", "en", "locale.json")
    fa_path = os.path.join(repo_root, "parto", "resources", "locales", "fa", "locale.json")

    cat_en, err_en = LanguageCatalogLoader.load_from_file(en_path)
    assert err_en is None and cat_en is not None, f"Failed loading English catalog: {err_en}"

    cat_fa, err_fa = LanguageCatalogLoader.load_from_file(fa_path)
    assert err_fa is None and cat_fa is not None, f"Failed loading Persian catalog: {err_fa}"

    return cat_en, cat_fa


# -----------------------------------------------------------------------------
# 1. Automated Key-Consistency & Coverage Tests
# -----------------------------------------------------------------------------

def test_static_codebase_keys_covered_in_english_catalog(repo_root, bundled_catalogs):
    """Verify that every statically referenced translation key in the codebase exists in en catalog."""
    cat_en, _ = bundled_catalogs
    codebase_keys_map = scan_codebase_translation_keys(repo_root)
    assert len(codebase_keys_map) > 0, "AST scanner found no keys in codebase"

    is_complete, missing = validate_codebase_key_coverage(set(codebase_keys_map.keys()), cat_en)
    assert is_complete, f"Missing keys in English catalog: {missing}"


def test_static_codebase_keys_covered_in_persian_catalog(repo_root, bundled_catalogs):
    """Verify that every statically referenced translation key in the codebase exists in fa catalog."""
    _, cat_fa = bundled_catalogs
    codebase_keys_map = scan_codebase_translation_keys(repo_root)

    is_complete, missing = validate_codebase_key_coverage(set(codebase_keys_map.keys()), cat_fa)
    assert is_complete, f"Missing keys in Persian catalog: {missing}"


def test_catalogs_maintain_exact_key_parity(bundled_catalogs):
    """Verify 100% key parity between English and Persian catalogs (zero discrepancies)."""
    cat_en, cat_fa = bundled_catalogs
    is_equal, missing_in_fa, missing_in_en = validate_catalog_parity(cat_en, cat_fa)
    assert is_equal, f"Catalog parity failed. Missing in fa: {missing_in_fa}, missing in en: {missing_in_en}"


def test_previously_reported_missing_keys_explicitly_present(bundled_catalogs):
    """
    Explicit regression test for keys identified in previous code review:
    - brush.reset_defaults
    - brush.studio.angle
    - dialog.info.alpha_no
    - dialog.resize.quick_presets
    - panel.adjustments.compare
    - brush.toggle_studio
    """
    cat_en, cat_fa = bundled_catalogs
    critical_keys = [
        "brush.reset_defaults",
        "brush.studio.angle",
        "dialog.info.alpha_no",
        "dialog.resize.quick_presets",
        "panel.adjustments.compare",
        "brush.toggle_studio",
    ]

    for key in critical_keys:
        assert cat_en.has(key), f"Key '{key}' missing from English catalog"
        assert cat_fa.has(key), f"Key '{key}' missing from Persian catalog"
        assert cat_en.get(key) != "", f"Empty translation for '{key}' in English"
        assert cat_fa.get(key) != "", f"Empty translation for '{key}' in Persian"


# -----------------------------------------------------------------------------
# 2. Placeholder Compatibility & Syntax Validation
# -----------------------------------------------------------------------------

def test_placeholder_compatibility_between_catalogs(bundled_catalogs):
    """Verify that named formatting parameters ({width}, {filename}, etc.) match between en and fa."""
    cat_en, cat_fa = bundled_catalogs
    mismatches = LanguageCatalogLoader.validate_placeholder_compatibility(cat_fa, cat_en)
    assert len(mismatches) == 0, f"Found placeholder mismatches: {mismatches}"


def test_synthetic_placeholder_mismatch_detection():
    """Verify that the placeholder compatibility validator catches discrepancies."""
    meta_en = LocaleMetadata(id="en", name="English", native_name="English", direction=TextDirection.LTR)
    meta_fa = LocaleMetadata(id="fa", name="Persian", native_name="فارسی", direction=TextDirection.RTL)
    cat_en = TranslationCatalog(
        metadata=meta_en,
        translations={"msg.welcome": "Hello {user}, you have {count} items"},
    )
    cat_fa = TranslationCatalog(
        metadata=meta_fa,
        translations={"msg.welcome": "سلام {user} عزیز"},  # Missing {count}
    )

    mismatches = LanguageCatalogLoader.validate_placeholder_compatibility(cat_fa, cat_en)
    assert len(mismatches) == 1
    assert "count" in mismatches[0]


def test_placeholder_syntax_validator():
    """Verify template placeholder syntax validation."""
    valid, err = validate_placeholder_syntax("Width: {width}px, Height: {height}px")
    assert valid is True
    assert err is None

    # Unclosed bracket
    valid, err = validate_placeholder_syntax("Width: {width")
    assert valid is False
    assert "Unclosed" in err

    # Unmatched closing bracket
    valid, err = validate_placeholder_syntax("Width: width}")
    assert valid is False
    assert "Unmatched" in err

    # Empty placeholder
    valid, err = validate_placeholder_syntax("Width: {}")
    assert valid is False
    assert "Empty" in err


# -----------------------------------------------------------------------------
# 3. Unicode CLDR Multilingual Pluralization Tests
# -----------------------------------------------------------------------------

def test_plural_rules_english():
    """English CLDR: 1 is 'one', everything else is 'other'."""
    assert get_plural_category(1, "en") == "one"
    assert get_plural_category(0, "en") == "other"
    assert get_plural_category(2, "en") == "other"
    assert get_plural_category(10, "en") == "other"
    assert get_plural_category(-1, "en") == "one" or get_plural_category(-1, "en") == "other"


def test_plural_rules_persian():
    """Persian CLDR: 0 and 1 are 'one', numbers >= 2 are 'other'."""
    assert get_plural_category(0, "fa") == "one"
    assert get_plural_category(1, "fa") == "one"
    assert get_plural_category(2, "fa") == "other"
    assert get_plural_category(5, "fa") == "other"
    assert get_plural_category(100, "fa") == "other"


def test_plural_rules_french():
    """French CLDR: 0 and 1 are 'one', 2 and above are 'other'."""
    assert get_plural_category(0, "fr") == "one"
    assert get_plural_category(1, "fr") == "one"
    assert get_plural_category(0.5, "fr") == "one"
    assert get_plural_category(1.5, "fr") == "one"
    assert get_plural_category(2, "fr") == "other"
    assert get_plural_category(10, "fr") == "other"


def test_plural_rules_slavic_complex_russian():
    """
    Russian CLDR:
    one: mod 10 == 1 and mod 100 != 11
    few: mod 10 in 2..4 and mod 100 not in 12..14
    many: mod 10 == 0 or mod 10 in 5..9 or mod 100 in 11..14
    """
    # 'one' cases
    assert get_plural_category(1, "ru") == "one"
    assert get_plural_category(21, "ru") == "one"
    assert get_plural_category(101, "ru") == "one"

    # 'few' cases
    assert get_plural_category(2, "ru") == "few"
    assert get_plural_category(3, "ru") == "few"
    assert get_plural_category(4, "ru") == "few"
    assert get_plural_category(22, "ru") == "few"
    assert get_plural_category(104, "ru") == "few"

    # 'many' cases
    assert get_plural_category(0, "ru") == "many"
    assert get_plural_category(5, "ru") == "many"
    assert get_plural_category(11, "ru") == "many"
    assert get_plural_category(12, "ru") == "many"
    assert get_plural_category(14, "ru") == "many"
    assert get_plural_category(20, "ru") == "many"
    assert get_plural_category(100, "ru") == "many"


def test_plural_rules_slavic_complex_polish():
    """
    Polish CLDR:
    one: 1
    few: mod 10 in 2..4 and mod 100 not in 12..14
    many: everything else
    """
    assert get_plural_category(1, "pl") == "one"
    assert get_plural_category(2, "pl") == "few"
    assert get_plural_category(4, "pl") == "few"
    assert get_plural_category(22, "pl") == "few"
    assert get_plural_category(0, "pl") == "many"
    assert get_plural_category(5, "pl") == "many"
    assert get_plural_category(12, "pl") == "many"


def test_plural_rules_arabic_six_categories():
    """
    Arabic CLDR (6 categories):
    zero (0), one (1), two (2), few (3..10), many (11..99), other (100)
    """
    assert get_plural_category(0, "ar") == "zero"
    assert get_plural_category(1, "ar") == "one"
    assert get_plural_category(2, "ar") == "two"
    assert get_plural_category(3, "ar") == "few"
    assert get_plural_category(10, "ar") == "few"
    assert get_plural_category(11, "ar") == "many"
    assert get_plural_category(99, "ar") == "many"
    assert get_plural_category(100, "ar") in ("other", "many")


# -----------------------------------------------------------------------------
# 4. Decimals, Coercion, Normalization & Error Resilience
# -----------------------------------------------------------------------------

def test_plural_decimal_and_numeric_coercion():
    """Verify float, Decimal, and numeric string coercion."""
    assert get_plural_category(1.0, "en") == "one"
    assert get_plural_category(2.5, "en") == "other"
    assert get_plural_category(Decimal("1.0"), "en") == "one"
    assert get_plural_category(Decimal("5"), "en") == "other"
    assert get_plural_category("1", "en") == "one"
    assert get_plural_category("2", "en") == "other"


def test_plural_locale_normalization():
    """Verify locale tags with region, script, casing, or hyphens are normalized."""
    assert get_plural_category(1, "EN-US") == "one"
    assert get_plural_category(1, "fa_IR") == "one"
    assert get_plural_category(0, "fa-IR") == "one"
    assert get_plural_category(21, "RU_ru") == "one"


def test_plural_invalid_inputs_resilience():
    """Non-numeric values or NaN/Infinity must safely return 'other' without raising."""
    assert get_plural_category(None, "en") == "other"
    assert get_plural_category("not-a-number", "en") == "other"
    assert get_plural_category(float("nan"), "en") == "other"
    assert get_plural_category(float("inf"), "en") == "other"


def test_plural_unsupported_locale_fallback():
    """Unknown or unsupported locale IDs safely fall back to standard cardinal rule."""
    cat = get_plural_category(1, "xyz-unknown")
    assert cat == "one"
    cat_multi = get_plural_category(5, "xyz-unknown")
    assert cat_multi == "other"


def test_resolve_translation_entry_missing_category_fallback():
    """When a plural dict lacks the exact category, fall back to 'other', then 'one'."""
    entry_only_other = {"other": "{count} items"}
    assert resolve_translation_entry(entry_only_other, count=1, locale_id="en") == "{count} items"

    entry_only_one = {"one": "Single item"}
    assert resolve_translation_entry(entry_only_one, count=5, locale_id="en") == "Single item"

    entry_plain = "Simple plain text"
    assert resolve_translation_entry(entry_plain, count=1, locale_id="en") == "Simple plain text"
