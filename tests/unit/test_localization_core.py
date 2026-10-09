# tests/unit/test_localization_core.py
"""
Unit Tests — Parto Localization Core Subsystem (i18n / l10n)
Author & Maintainer: Ali Kamrani (علی کامرانی)

Tests:
1. Valid catalog loading and validation (English and Persian)
2. Automatic catalog discovery
3. Safe rejection of malformed or invalid catalogs
4. Stable-key lookups, fallback chains, and missing-key diagnostics
5. Named safe interpolation (no eval/code execution, missing parameter tolerance)
6. Locale-aware pluralization (English and Persian rules)
7. TextDirection and RTL / LTR metadata
8. Atomic runtime switching and failure rollback
9. Future Intent Subsystem integration contract
"""

import os
import json
import tempfile
import pytest

from parto.localization.models import (
    LocaleMetadata,
    TextDirection,
    DiagnosticRecord,
    CATALOG_SCHEMA_VERSION,
)
from parto.localization.catalog import TranslationCatalog
from parto.localization.loader import LanguageCatalogLoader
from parto.localization.formatting import (
    safe_interpolate,
    extract_placeholders,
    get_plural_category,
    resolve_translation_entry,
)
from parto.localization.manager import LocalizationManager
from parto.localization.persistence import LocalePreferences


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def clean_manager(tmp_path):
    """Provides a fresh isolated LocalizationManager instance."""
    LocalizationManager.reset_instance()
    mgr = LocalizationManager()
    mgr._preferences = LocalePreferences(filepath=str(tmp_path / "settings.json"))
    mgr._current_locale = "en"
    mgr.fallback_locale = "en"
    return mgr


@pytest.fixture
def temp_catalog_dir():
    """Temporary directory for testing catalog discovery and malformed files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# -----------------------------------------------------------------------------
# 1. Models & Metadata Tests
# -----------------------------------------------------------------------------

def test_locale_metadata_properties():
    """Verify LocaleMetadata immutability, BCP 47 id, and RTL evaluation."""
    meta_en = LocaleMetadata(
        id="en",
        name="English",
        native_name="English",
        direction=TextDirection.LTR,
        version="1.0.0",
        author="Ali Kamrani",
    )
    assert meta_en.id == "en"
    assert meta_en.name == "English"
    assert meta_en.native_name == "English"
    assert meta_en.direction == TextDirection.LTR
    assert meta_en.is_rtl is False

    meta_fa = LocaleMetadata(
        id="fa",
        name="Persian",
        native_name="فارسی",
        direction=TextDirection.RTL,
        version="1.0.0",
        author="Ali Kamrani (علی کامرانی)",
    )
    assert meta_fa.id == "fa"
    assert meta_fa.direction == TextDirection.RTL
    assert meta_fa.is_rtl is True

    # Serialization roundtrip
    d = meta_fa.to_dict()
    assert d["id"] == "fa"
    assert d["direction"] == "rtl"
    meta_restored = LocaleMetadata.from_dict(d)
    assert meta_restored.id == "fa"
    assert meta_restored.is_rtl is True


def test_text_direction_parsing():
    """Verify TextDirection parses strings robustly."""
    assert TextDirection.from_string("rtl") == TextDirection.RTL
    assert TextDirection.from_string("RTL") == TextDirection.RTL
    assert TextDirection.from_string("right-to-left") == TextDirection.RTL
    assert TextDirection.from_string("ltr") == TextDirection.LTR
    assert TextDirection.from_string("unknown") == TextDirection.LTR


# -----------------------------------------------------------------------------
# 2. Interpolation and Formatting Tests
# -----------------------------------------------------------------------------

def test_safe_interpolation_basic_and_named():
    """Verify placeholder replacement without eval or string concatenation."""
    tpl = "Hello, {name}! Welcome to {app}."
    res, missing = safe_interpolate(tpl, {"name": "Ali", "app": "Parto"})
    assert res == "Hello, Ali! Welcome to Parto."
    assert len(missing) == 0


def test_safe_interpolation_missing_parameters():
    """Missing parameters must be safely retained and reported in missing set."""
    tpl = "Dimensions: {width} × {height} px with {zoom}%"
    res, missing = safe_interpolate(tpl, {"width": 1920})
    assert res == "Dimensions: 1920 × {height} px with {zoom}%"
    assert missing == {"height", "zoom"}


def test_safe_interpolation_extra_parameters():
    """Extra parameters must not break interpolation."""
    tpl = "Saved {filename}"
    res, missing = safe_interpolate(tpl, {"filename": "art.png", "unused": 42})
    assert res == "Saved art.png"
    assert len(missing) == 0


def test_extract_placeholders():
    """Extract named parameters from format string."""
    assert extract_placeholders("No variables here") == set()
    assert extract_placeholders("Image: {width}x{height} px, {filter}") == {"width", "height", "filter"}


def test_plural_rules_english_and_persian():
    """Verify locale-specific plural category calculation."""
    # English: 1 is 'one', all other numbers are 'other'
    assert get_plural_category(1, "en") == "one"
    assert get_plural_category(0, "en") == "other"
    assert get_plural_category(2, "en") == "other"
    assert get_plural_category(10, "en") == "other"

    # Persian (fa): 0 and 1 are 'one', other numbers are 'other'
    assert get_plural_category(0, "fa") == "one"
    assert get_plural_category(1, "fa") == "one"
    assert get_plural_category(2, "fa") == "other"
    assert get_plural_category(5, "fa") == "other"


def test_resolve_translation_entry_plural_dict():
    """Verify plural dictionary resolution."""
    entry = {
        "one": "{count} Layer",
        "other": "{count} Layers",
    }
    # In English
    assert resolve_translation_entry(entry, count=1, locale_id="en") == "{count} Layer"
    assert resolve_translation_entry(entry, count=5, locale_id="en") == "{count} Layers"

    # In Persian
    fa_entry = {
        "one": "{count} لایه",
        "other": "{count} لایه",
    }
    assert resolve_translation_entry(fa_entry, count=1, locale_id="fa") == "{count} لایه"
    assert resolve_translation_entry(fa_entry, count=4, locale_id="fa") == "{count} لایه"


# -----------------------------------------------------------------------------
# 3. Catalog Loading and Validation Tests
# -----------------------------------------------------------------------------

def test_load_bundled_english_and_persian_catalogs():
    """Verify factory English and Persian catalogs are valid and loadable."""
    here = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.abspath(os.path.join(here, "../.."))
    locales_dir = os.path.join(repo_root, "parto", "resources", "locales")

    en_path = os.path.join(locales_dir, "en", "locale.json")
    fa_path = os.path.join(locales_dir, "fa", "locale.json")

    assert os.path.exists(en_path), f"Missing {en_path}"
    assert os.path.exists(fa_path), f"Missing {fa_path}"

    cat_en, err_en = LanguageCatalogLoader.load_from_file(en_path)
    assert err_en is None
    assert cat_en is not None
    assert cat_en.id == "en"
    assert cat_en.is_rtl is False
    assert cat_en.has("app.name")
    assert cat_en.has("menu.file")

    cat_fa, err_fa = LanguageCatalogLoader.load_from_file(fa_path)
    assert err_fa is None
    assert cat_fa is not None
    assert cat_fa.id == "fa"
    assert cat_fa.is_rtl is True
    assert cat_fa.has("app.name")
    assert cat_fa.has("menu.file")


def test_reject_malformed_catalogs(temp_catalog_dir):
    """Corrupt JSON or missing metadata must be safely rejected without crashing."""
    # 1. Invalid JSON
    corrupt_file = os.path.join(temp_catalog_dir, "corrupt.json")
    with open(corrupt_file, "w", encoding="utf-8") as f:
        f.write("{invalid json: here")
    cat, err = LanguageCatalogLoader.load_from_file(corrupt_file)
    assert cat is None
    assert err is not None
    assert "Malformed JSON" in err

    # 2. Missing schema version
    noschema_file = os.path.join(temp_catalog_dir, "noschema.json")
    with open(noschema_file, "w", encoding="utf-8") as f:
        json.dump({"metadata": {"id": "de"}, "translations": {"a": "b"}}, f)
    cat, err = LanguageCatalogLoader.load_from_file(noschema_file)
    assert cat is None
    assert "schema_version" in err

    # 3. Missing translations
    notrans_file = os.path.join(temp_catalog_dir, "notrans.json")
    with open(notrans_file, "w", encoding="utf-8") as f:
        json.dump({"schema_version": "1.0.0", "metadata": {"id": "de"}}, f)
    cat, err = LanguageCatalogLoader.load_from_file(notrans_file)
    assert cat is None
    assert "translations" in err

    # 4. Non-string translation values
    badtype_file = os.path.join(temp_catalog_dir, "badtype.json")
    with open(badtype_file, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0.0",
            "metadata": {"id": "de"},
            "translations": {"bad": 12345},
        }, f)
    cat, err = LanguageCatalogLoader.load_from_file(badtype_file)
    assert cat is None
    assert "must be string or plural" in err


def test_catalog_discovery_across_directories(temp_catalog_dir, clean_manager):
    """Verify loader discovers catalogs in subdirectories or flat files."""
    # Create French pack in subfolder: <temp>/fr/locale.json
    fr_dir = os.path.join(temp_catalog_dir, "fr")
    os.makedirs(fr_dir, exist_ok=True)
    fr_file = os.path.join(fr_dir, "locale.json")
    with open(fr_file, "w", encoding="utf-8") as f:
        json.dump({
            "schema_version": "1.0.0",
            "metadata": {
                "id": "fr",
                "name": "French",
                "native_name": "Français",
                "direction": "ltr",
            },
            "translations": {
                "app.name": "Parto",
                "menu.file": "Fichier",
            },
        }, f)

    # Discover
    added = clean_manager.discover_locales(temp_catalog_dir)
    assert added >= 1
    assert "fr" in clean_manager.get_available_locales()
    assert clean_manager.translate_for_locale("fr", "menu.file") == "Fichier"


# -----------------------------------------------------------------------------
# 4. Fallback Chain & Diagnostics Tests
# -----------------------------------------------------------------------------

def test_translation_fallback_chain(clean_manager):
    """
    Test predictable fallback:
    1. Active language entry
    2. Fallback language (en) entry
    3. Diagnostic string [key] or explicit default
    """
    # Register minimal German catalog with only some keys
    de_meta = LocaleMetadata(id="de", name="German", native_name="Deutsch", direction=TextDirection.LTR)
    de_cat = TranslationCatalog(
        metadata=de_meta,
        translations={
            "app.name": "Parto DE",
            # "menu.file" is omitted deliberately to test fallback to English
        },
    )
    clean_manager.register_catalog(de_cat)
    clean_manager.set_locale("de", persist=False)

    # 1. Key present in DE
    assert clean_manager.translate("app.name") == "Parto DE"

    # 2. Key missing in DE, present in EN fallback
    en_file_text = clean_manager.translate_for_locale("en", "menu.file")
    assert clean_manager.translate("menu.file") == en_file_text

    # 3. Key missing in both DE and EN: check explicit default
    assert clean_manager.translate("completely.nonexistent.key", default="Default Msg") == "Default Msg"

    # 4. Key missing in both without default: returns diagnostic [key]
    assert clean_manager.translate("completely.nonexistent.key") == "[completely.nonexistent.key]"

    # Missing keys should be tracked in diagnostics
    missing = clean_manager.get_missing_keys()
    assert any("completely.nonexistent.key" in k for k in missing)


def test_missing_translation_does_not_raise(clean_manager):
    """Missing translations must NEVER raise an unhandled exception."""
    try:
        val = clean_manager.translate("nonexistent.key.test")
        assert val == "[nonexistent.key.test]"
    except Exception as e:
        pytest.fail(f"translate() raised exception on missing key: {e}")


# -----------------------------------------------------------------------------
# 5. Runtime Language Switching & Atomicity Tests
# -----------------------------------------------------------------------------

def test_runtime_switching_between_en_and_fa(clean_manager):
    """Verify switching between English and Persian updates locale and text direction."""
    assert clean_manager.set_locale("en", persist=False) is True
    assert clean_manager.current_locale == "en"
    assert clean_manager.is_rtl is False
    assert clean_manager.direction == TextDirection.LTR
    assert clean_manager.translate("menu.file") == "&File"

    # Switch to Persian
    assert clean_manager.set_locale("fa", persist=False) is True
    assert clean_manager.current_locale == "fa"
    assert clean_manager.is_rtl is True
    assert clean_manager.direction == TextDirection.RTL
    assert clean_manager.translate("menu.file") == "پرونده"

    # Switch back to English
    assert clean_manager.set_locale("en", persist=False) is True
    assert clean_manager.current_locale == "en"
    assert clean_manager.is_rtl is False


def test_runtime_switching_failure_preserves_active_locale(clean_manager):
    """Switching to an invalid or uninstalled language must fail and preserve active state."""
    clean_manager.set_locale("en", persist=False)
    assert clean_manager.current_locale == "en"

    # Attempt switch to unknown language
    result = clean_manager.set_locale("nonexistent_lang", persist=False)
    assert result is False
    # Active locale must remain English untouched
    assert clean_manager.current_locale == "en"
    assert clean_manager.is_rtl is False


def test_listener_notifications(clean_manager):
    """Verify observers receive notifications on locale change."""
    events = []

    def _observer(new_locale: str):
        events.append(new_locale)

    clean_manager.add_locale_listener(_observer)
    clean_manager.set_locale("fa", persist=False)
    clean_manager.set_locale("en", persist=False)
    clean_manager.remove_locale_listener(_observer)
    clean_manager.set_locale("fa", persist=False)

    assert events == ["fa", "en"]


# -----------------------------------------------------------------------------
# 6. Future Intent Subsystem Compatibility Tests
# -----------------------------------------------------------------------------

def test_future_intent_system_contract(clean_manager):
    """
    Verify Localization Core supports the future Intent subsystem contract:
    - Requests localized structured responses with message keys and named parameters.
    - Decoupled from active UI locale (can request Persian response while UI is English).
    - No LLM, network, or command interpretation dependencies.
    """
    clean_manager.set_locale("en", persist=False)

    # 1. Format intent response in current UI locale
    resp_en = clean_manager.format_intent_response(
        "intent.response.operation_completed",
        operation="Crop",
    )
    assert "Operation 'Crop' completed successfully." in resp_en

    # 2. Format intent response in Persian while UI remains English
    resp_fa = clean_manager.format_intent_response(
        "intent.response.operation_completed",
        locale="fa",
        operation="برش",
    )
    assert "عملیات «برش» با موفقیت انجام شد." in resp_fa
    # Confirm UI locale was NOT modified by the intent formatting call
    assert clean_manager.current_locale == "en"

    # 3. Intent confirmation prompt
    conf_fa = clean_manager.format_intent_response(
        "intent.confirmation.operation_required",
        locale="fa",
        operation="حذف لایه",
    )
    assert "حذف لایه" in conf_fa

    # 4. Intent unsupported command
    err_en = clean_manager.format_intent_response(
        "intent.error.unsupported_command",
        locale="en",
        command="generate_vector",
    )
    assert "generate_vector" in err_en


# -----------------------------------------------------------------------------
# 7. Failure-Path & Robustness Tests (Task Two)
# -----------------------------------------------------------------------------

def test_invalid_locale_id_does_not_corrupt_state(clean_manager):
    """Invalid locale IDs must be rejected safely without modifying active state."""
    clean_manager.set_locale("en", persist=False)
    assert clean_manager.current_locale == "en"

    for invalid_id in ["", "  ", None, "../../traversal", "invalid#id", "too_many_parts_in_id_foo_bar_baz"]:
        result = clean_manager.set_locale(invalid_id, persist=False)
        assert result is False
        assert clean_manager.current_locale == "en"
        assert clean_manager.direction == TextDirection.LTR
        assert clean_manager.is_rtl is False

    # Previous locale remains fully usable
    assert clean_manager.translate("menu.file") == "&File"
    diagnostics = clean_manager.get_diagnostics()
    assert len(diagnostics) > 0


def test_missing_catalog_does_not_change_active_locale(clean_manager):
    """Requesting an unregistered/non-existent catalog must fail and preserve state."""
    clean_manager.set_locale("en", persist=False)

    assert clean_manager.set_locale("xx", persist=False) is False
    assert clean_manager.current_locale == "en"
    assert clean_manager.is_rtl is False
    assert clean_manager.direction == TextDirection.LTR


def test_malformed_candidate_catalog_does_not_replace_valid_catalog(clean_manager):
    """A catalog that fails validation must be rejected and never activated."""
    clean_manager.set_locale("en", persist=False)

    # Create catalog with invalid empty ID
    invalid_meta = LocaleMetadata(id="", name="Bad", native_name="Bad", direction=TextDirection.LTR)
    invalid_cat = TranslationCatalog(metadata=invalid_meta, translations={"app.name": "Bad"})

    # register_catalog should fail validation
    reg_ok = clean_manager.register_catalog(invalid_cat)
    assert reg_ok is False
    assert clean_manager.current_locale == "en"


def test_settings_persistence_failure_default_contract(clean_manager, monkeypatch):
    """
    Contract test: When persistence fails in default mode (strict_persistence=False),
    the active session is successfully switched (returns True), but last_persistence_succeeded
    is False and a diagnostic warning is logged.
    """
    clean_manager.set_locale("en", persist=False)

    # Simulate filesystem write failure in LocalePreferences
    def mock_set_preferred_locale(locale_id):
        return False

    monkeypatch.setattr(clean_manager._preferences, "set_preferred_locale", mock_set_preferred_locale)

    result = clean_manager.set_locale("fa", persist=True, strict_persistence=False)
    assert result is True
    assert clean_manager.current_locale == "fa"
    assert clean_manager.is_rtl is True
    assert clean_manager.last_persistence_succeeded is False
    assert clean_manager.last_persistence_error is not None

    diagnostics = [d for d in clean_manager.get_diagnostics() if "Could not persist" in d.message]
    assert len(diagnostics) >= 1


def test_settings_persistence_failure_strict_contract(clean_manager, monkeypatch):
    """
    Contract test: When persistence fails in strict mode (strict_persistence=True),
    the locale switch is rolled back to the previous locale and returns False.
    """
    clean_manager.set_locale("en", persist=False)

    def mock_set_preferred_locale_raise(locale_id):
        raise IOError("Disk quota exceeded")

    monkeypatch.setattr(clean_manager._preferences, "set_preferred_locale", mock_set_preferred_locale_raise)

    result = clean_manager.set_locale("fa", persist=True, strict_persistence=True)
    assert result is False
    # Verified rollback to previous working state
    assert clean_manager.current_locale == "en"
    assert clean_manager.is_rtl is False
    assert clean_manager.direction == TextDirection.LTR
    assert clean_manager.last_persistence_succeeded is False


def test_listener_failure_isolation_and_reporting(clean_manager):
    """
    Subscriber isolation test: An unhandled exception in one subscriber callback
    must not prevent subsequent subscribers from receiving notification, and
    must record last_refresh_completed = False.
    """
    clean_manager.set_locale("en", persist=False)
    delivered = []

    def failing_listener(loc):
        raise RuntimeError("Widget refresh failure simulation")

    def successful_listener(loc):
        delivered.append(loc)

    clean_manager.add_locale_listener(failing_listener)
    clean_manager.add_locale_listener(successful_listener)

    # Switch language to Persian
    result = clean_manager.set_locale("fa", persist=False)
    assert result is True
    assert clean_manager.current_locale == "fa"

    # Successful listener was still called despite the failure in the previous listener
    assert delivered == ["fa"]
    assert clean_manager.last_refresh_completed is False
    assert len(clean_manager.last_listener_failures) == 1
    assert "Widget refresh failure simulation" in clean_manager.last_listener_failures[0]["error"]


def test_repeated_switching_does_not_duplicate_subscriptions(clean_manager):
    """Adding the same callback multiple times must not produce duplicate calls."""
    calls = []

    def test_callback(loc):
        calls.append(loc)

    clean_manager.add_locale_listener(test_callback)
    clean_manager.add_locale_listener(test_callback)  # Duplicate registration

    clean_manager.set_locale("fa", persist=False)
    clean_manager.set_locale("en", persist=False)

    assert calls == ["fa", "en"]


def test_selecting_current_locale_is_idempotent_noop(clean_manager):
    """Selecting the currently active locale returns True immediately as an idempotent no-op."""
    clean_manager.set_locale("en", persist=False)
    events = []

    clean_manager.add_locale_listener(lambda l: events.append(l))

    # Re-selecting current locale
    result = clean_manager.set_locale("en", persist=False)
    assert result is True
    assert len(events) == 0  # No redundant notification dispatched
    assert clean_manager.current_locale == "en"


def test_previous_locale_remains_usable_after_failed_switch(clean_manager):
    """When switching to an invalid locale fails, the previous locale remains 100% usable."""
    clean_manager.set_locale("fa", persist=False)
    assert clean_manager.current_locale == "fa"
    assert clean_manager.is_rtl is True

    # Failed switch attempt
    res = clean_manager.set_locale("nonexistent_locale", persist=False)
    assert res is False

    # Previous active state must be untouched and fully functional
    assert clean_manager.current_locale == "fa"
    assert clean_manager.is_rtl is True
    assert clean_manager.direction == TextDirection.RTL
    assert clean_manager.translate("menu.file") == "پرونده"

