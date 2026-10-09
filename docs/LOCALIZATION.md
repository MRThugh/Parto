# Parto Localization Subsystem (i18n / l10n) Developer Guide
**Author & Maintainer:** Ali Kamrani (علی کامرانی)  
**Release Line:** 0.4.0 (Localization Core Finalization)  
**Status:** Production Ready

---

## 1. Overview & Architectural Philosophy

The Parto Localization Subsystem provides decoupled, high-performance, and resilient internationalization (i18n) and localization (l10n) for the Parto desktop image editor.

### Key Architectural Tenets:
1. **Zero UI Coupling:** The localization engine (`parto/localization/`) has zero dependencies on PySide6 widgets or canvas geometry. It operates as an independent domain service.
2. **Authoritative Locale State:** The active locale, fallback chains, catalog registry, and layout direction synchronization are managed exclusively through `LocalizationManager.instance()`.
3. **Strict State Isolation:** Runtime language switches retranslate UI text without modifying or resetting document identity, canvas dimensions, layer stack, undo/redo history, brush parameters, or active themes.
4. **Deterministic Fallback Chain:**
   $$\text{Target Locale} \longrightarrow \text{Fallback Locale (en)} \longrightarrow \text{Explicit Default} \longrightarrow \text{Diagnostic Fallback } [key]$$
5. **Atomic Switching & Failure Isolation:** Switching language validates candidate catalogs prior to commit. Persistence failures in default mode do not invalidate active sessions; observer failures are isolated so that one failing widget does not prevent other components from refreshing.
6. **No External Services / LLM Dependencies:** Localization is completely deterministic, local, and file-based. No network or AI models are involved.

---

## 2. Directory Structure

```text
parto/
├── localization/
│   ├── __init__.py           # Public exports (LocalizationManager, t, TextDirection, LocaleMetadata)
│   ├── models.py             # Domain models (LocaleMetadata, TextDirection, DiagnosticRecord, validation)
│   ├── catalog.py            # TranslationCatalog representation and validation
│   ├── loader.py             # LanguageCatalogLoader for file discovery and JSON parsing
│   ├── formatting.py         # safe_interpolate, pluralization rules, placeholder extractors
│   ├── persistence.py        # LocalePreferences atomic settings read/write
│   └── manager.py            # LocalizationManager singleton and Qt signal coordinator
└── resources/
    └── locales/
        ├── en/
        │   └── locale.json   # English factory catalog (191 keys, LTR)
        └── fa/
            └── locale.json   # Persian factory catalog (191 keys, RTL)
```

---

## 3. Public API & Signatures

### Global Convenience Methods (`parto.localization`)
```python
from parto.localization import get_localization_manager, t

# 1. Quick translation lookup in active locale
message: str = t("menu.file", default="&File")

# 2. Named interpolation
title: str = t("app.window_title_with_file", filename="artwork.png *")

# 3. Pluralized lookup
layer_label: str = t("layers.count_summary", count=3)
```

### LocalizationManager (`parto.localization.manager.LocalizationManager`)
```python
class LocalizationManager(QObject):
    @classmethod
    def instance(cls) -> LocalizationManager: ...

    @classmethod
    def reset_instance(cls) -> None: ...

    # Active State
    @property
    def current_locale(self) -> str: ...

    @property
    def direction(self) -> TextDirection: ...

    @property
    def is_rtl(self) -> bool: ...

    @property
    def current_metadata(self) -> LocaleMetadata: ...

    # Persistence & Refresh Status
    @property
    def last_persistence_succeeded(self) -> bool: ...

    @property
    def last_persistence_error(self) -> Optional[str]: ...

    @property
    def last_refresh_completed(self) -> bool: ...

    @property
    def last_listener_failures(self) -> List[Dict[str, Any]]: ...

    # Language Switching
    def set_locale(
        self,
        locale_id: str,
        persist: bool = True,
        strict_persistence: bool = False,
    ) -> bool: ...

    # Lookup & Formatting
    def translate(
        self,
        key: str,
        default: Optional[str] = None,
        count: Optional[int] = None,
        **kwargs,
    ) -> str: ...

    def translate_for_locale(
        self,
        locale_id: str,
        key: str,
        default: Optional[str] = None,
        count: Optional[int] = None,
        **kwargs,
    ) -> str: ...

    def format_intent_response(
        self,
        key: str,
        locale: Optional[str] = None,
        **kwargs,
    ) -> str: ...

    # Observers & Registration
    def add_locale_listener(self, callback: Callable[[str], None]) -> None: ...
    def remove_locale_listener(self, callback: Callable[[str], None]) -> None: ...
    def register_catalog(self, catalog: TranslationCatalog) -> bool: ...
    def discover_locales(self, directory: Optional[str] = None) -> int: ...
```

---

## 4. Catalog Schema Specification

Every catalog is stored as a UTF-8 JSON file (`locale.json`).

```json
{
  "schema_version": "1.0.0",
  "metadata": {
    "id": "de",
    "name": "German",
    "native_name": "Deutsch",
    "direction": "ltr",
    "version": "1.0.0",
    "author": "Translator Name",
    "plural_rule": "cardinal"
  },
  "translations": {
    "app.name": "Parto",
    "menu.file": "&Datei",
    "layers.layer_count": {
      "one": "{count} Ebene",
      "other": "{count} Ebenen"
    },
    "toast.saved": "{filename} gespeichert"
  }
}
```

### Metadata Fields:
- `id` *(string, required)*: Valid BCP 47 language code (e.g., `en`, `fa`, `fr`, `de`). Must be lowercase alphanumeric, dashes, or underscores. Path traversals are strictly rejected.
- `name` *(string, required)*: International English name of the language.
- `native_name` *(string, required)*: Native representation (e.g., `فارسی`, `Deutsch`).
- `direction` *(string, required)*: Text direction; `"ltr"` (Left-to-Right) or `"rtl"` (Right-to-Left).
- `version` *(string, optional)*: Semantic version of the catalog pack.
- `author` *(string, optional)*: Maintainer credit.

---

## 5. Runtime Language Switching Contract

When `manager.set_locale(locale_id, persist=True, strict_persistence=False)` is executed:

1. **Validation Phase:**
   - Locale ID format is verified against `is_valid_locale_id`.
   - Idempotency check: If `locale_id == current_locale`, immediately returns `True` without redundant processing.
   - Catalog discovery & validation: Candidate catalog is located and validated. If validation errors occur, switch aborts and returns `False`.
2. **Transaction Commit Phase:**
   - Active locale is committed: `self._current_locale = locale_id`.
   - Layout direction is updated on `QApplication.instance()` (`Qt.LeftToRight` vs `Qt.RightToLeft`).
3. **Persistence Phase:**
   - By default (`strict_persistence=False`), persistence is treated as a non-critical post-commit side effect. If disk writing fails (e.g. read-only disk or quota exceeded), `last_persistence_succeeded` is set to `False`, a diagnostic warning is logged, and the function returns `True` (active session remains functional).
   - If `strict_persistence=True`, persistence failure triggers an atomic rollback to the previous locale and layout direction, returning `False`.
4. **Broadcast & Subscriber Isolation:**
   - `locale_changed` Qt signal is emitted.
   - Headless listeners are invoked sequentially inside isolated `try...except` blocks. An exception in listener $A$ is recorded in `last_listener_failures` and does not prevent listener $B$ from executing.
   - In `MainWindow`, each UI component (`toolbar`, `statusbar`, `dock panels`, `menus`) is retranslated in an isolated block, preventing partial UI breakage.

---

## 6. How to Add a New Language

Adding a new language to Parto requires **zero code modifications** to the engine:

1. Create a subdirectory under `parto/resources/locales/<id>/` (or in external user directory `~/.parto/locales/<id>/`).
2. Add `locale.json` matching the schema:
   ```json
   {
     "schema_version": "1.0.0",
     "metadata": {
       "id": "es",
       "name": "Spanish",
       "native_name": "Español",
       "direction": "ltr",
       "version": "1.0.0",
       "author": "Contributor"
     },
     "translations": {
       "app.name": "Parto",
       "menu.file": "&Archivo",
       "menu.edit": "&Editar"
     }
   }
   ```
3. On application launch, `LocalizationManager` automatically scans `parto/resources/locales/` and user directories, validates the file, registers it, and populates the **Language** menu in `EditorMenuBar`. Any untranslated keys automatically fall back to English (`en`).

---

## 7. Future Intent Subsystem Integration

Parto's architecture prepares for future natural-language and automation Intent integration through `format_intent_response()`:

```python
from parto.localization import get_localization_manager

lm = get_localization_manager()

# 1. Format intent operation result in current user locale
response = lm.format_intent_response(
    "intent.response.operation_completed",
    operation="Crop",
)
# Returns: "Operation 'Crop' completed successfully."

# 2. Format intent response in a specific target locale (independent of current UI locale)
persian_response = lm.format_intent_response(
    "intent.response.operation_completed",
    locale="fa",
    operation="برش",
)
# Returns: "عملیات «برش» با موفقیت انجام شد."
# Current UI locale remains unmodified!

# 3. Intent confirmation prompt
confirmation = lm.format_intent_response(
    "intent.confirmation.operation_required",
    locale="en",
    operation="Delete Layer",
)
# Returns: "Are you sure you want to proceed with 'Delete Layer'?"
```

### Architectural Properties:
- **Widget-Independent:** Can be invoked from headless workers, background threads, CLI scripts, or socket handlers.
- **Decoupled from Active UI:** Can produce localized responses in French or Persian while the desktop UI is displayed in English.
- **Zero Mock / Zero LLM Dependency:** Format strings and interpolation are 100% deterministic and safe from injection attacks.
