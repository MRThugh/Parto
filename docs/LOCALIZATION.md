# Parto Localization Subsystem (i18n / l10n) Developer Guide

**Author & Maintainer:** Ali Kamrani (علی کامرانی)  
**Release Line:** v0.4.0 Target Milestone (Current Package: v0.3.1)  
**Status:** Stabilized & Fully Verified (48 Localization Tests Passing: 26 Core Unit Tests, 20 Validation/Parity Tests, 2 Qt Integration Tests)

---

## 1. Overview & Architectural Philosophy

The Parto Localization Subsystem provides decoupled, high-performance, and failure-resilient internationalization (i18n) and localization (l10n) for the Parto desktop image editor.

### Key Architectural Tenets:
1. **Zero UI Coupling:** The localization domain engine (`parto/localization/`) has zero dependencies on PySide6 widgets or canvas geometry. It operates as an independent domain service fully functional in headless environments.
2. **Authoritative Locale State:** The active locale, fallback chains, catalog registry, and layout direction synchronization are managed exclusively through `LocalizationManager.instance()`.
3. **Strict State Isolation:** Runtime language switches retranslate UI text without modifying or resetting document identity, canvas dimensions, layer stack, undo/redo history, brush parameters, or active themes.
4. **Deterministic Fallback Chain:**
   $$\text{Target Locale} \longrightarrow \text{Fallback Locale (en)} \longrightarrow \text{Explicit Default} \longrightarrow \text{Diagnostic Fallback } [key]$$
5. **Atomic Switching & Failure Isolation:** Switching language validates candidate catalogs prior to commit. Persistence failures in default mode do not invalidate active sessions; observer failures are isolated so that one failing widget does not prevent other components from refreshing.
6. **No External Services / LLM Dependencies:** Localization is completely deterministic, local, and file-based. No network calls or AI models are involved.

---

## 2. Directory Structure & File Inventory

```text
parto/
├── localization/
│   ├── __init__.py           # Public exports (LocalizationManager, t, TextDirection, LocaleMetadata)
│   ├── models.py             # Domain models (LocaleMetadata, TextDirection, DiagnosticRecord, validation)
│   ├── catalog.py            # TranslationCatalog representation and validation
│   ├── loader.py             # LanguageCatalogLoader for file discovery and JSON parsing
│   ├── formatting.py         # safe_interpolate, Unicode CLDR plural rules via Babel & fallbacks
│   ├── persistence.py        # LocalePreferences atomic settings read/write
│   ├── validator.py          # AST static key coverage and catalog parity validator
│   └── manager.py            # LocalizationManager singleton and Qt signal coordinator
└── resources/
    └── locales/
        ├── en/
        │   └── locale.json   # English factory catalog (225 keys, LTR)
        └── fa/
            └── locale.json   # Persian factory catalog (225 keys, RTL)
```

Both bundled catalogs (`en` and `fa`) contain exactly **225 translation keys** with 100% key parity, complete codebase coverage, and zero placeholder discrepancies.

---

## 3. Supported Locales & Configuration

| Identifier | Language | Native Name | Direction | Plural Rule | Status |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `en` | English | English | LTR | Cardinal (one / other) | Bundled Factory Default |
| `fa` | Persian | فارسی | RTL | Cardinal (0–1: one / $\ge 2$: other) | Bundled Factory |

### Identifier Validation Rules:
- Validated via `is_valid_locale_id(locale_id)` in `parto/localization/models.py`.
- Must consist strictly of lowercase alphanumeric characters, hyphens, and underscores (e.g. `en`, `fa`, `pt-br`, `zh_cn`).
- Directory traversal sequences (`..`, `/`, `\`) and whitespace characters are strictly rejected to prevent path manipulation.

---

## 4. Translation Catalog Specification & Metadata

Every catalog is stored as a UTF-8 encoded JSON document (`locale.json`):

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

### Required Fields:
- `schema_version` *(string, required)*: Catalog specification version (currently `"1.0.0"`).
- `metadata.id` *(string, required)*: Valid BCP 47 language identifier conforming to `is_valid_locale_id`.
- `metadata.name` *(string, required)*: International English name.
- `metadata.native_name` *(string, required)*: Native script representation (e.g., `فارسی`, `Deutsch`).
- `metadata.direction` *(string, required)*: Text direction; `"ltr"` (Left-to-Right) or `"rtl"` (Right-to-Left).
- `translations` *(object, required)*: Key-value map where values are either simple strings or plural sub-dictionaries.

---

## 5. Translation Lookup, Formatting & Fallback Behavior

### Fallback Chain Contract:
When resolving `t(key, default=None, **kwargs)`:
1. **Target Locale Catalog**: Looks up `key` in the actively selected catalog.
2. **Configured Fallback Catalog**: If absent in target and target is not `en`, looks up in `self._fallback_locale` (`en`). Logs a diagnostic missing key event.
3. **Explicit Default**: If absent in both catalogs and caller supplied `default="..."`, uses `default`.
4. **Diagnostic Fallback**: If no default is supplied, formats the unresolved key as `"[key]"` (e.g. `"[menu.file]"`).

### Safe Parameter Interpolation (`safe_interpolate`):
- Uses pure-Python regex pattern `\{([a-zA-Z0-9_]+)\}`.
- Never invokes `eval()`, `exec()`, or Python `str.format()` execution paths.
- **Tolerant of Missing Parameters:** If a parameter is missing from `kwargs`, `{param}` is preserved in the resulting string without raising an exception, and a diagnostic warning is recorded.
- **Extra Parameters:** Unused arguments in `kwargs` are safely ignored.

### Cardinal Pluralization:
- Evaluated via `resolve_translation_entry(entry, count, locale_id)`:
  - **English (`en`)**: `count == 1` maps to `"one"`, all other counts map to `"other"`.
  - **Persian (`fa`)**: `count in (0, 1)` maps to `"one"`, `count >= 2` maps to `"other"`.

---

## 6. Runtime Language Switching Contract

Language switching is invoked via:
```python
LocalizationManager.instance().set_locale(locale_id, persist=True, strict_persistence=False) -> bool
```

The operation executes as a structured transaction:

1. **Input Validation:**
   - Validates that `locale_id` is a non-empty string conforming to `is_valid_locale_id`.
   - Rejects invalid identifiers immediately and returns `False`.
2. **Idempotency Guard:**
   - If `locale_id == self._current_locale`, returns `True` immediately without re-reading disks or emitting signals.
3. **Re-entrancy Guard:**
   - Protected by `self._is_switching` boolean to reject recursive or nested `set_locale()` calls.
4. **Candidate Catalog Discovery & Validation:**
   - If not yet loaded in memory, triggers discovery across registered catalog directories.
   - Executes `catalog.validate()`. If candidate catalog is missing or fails validation, aborts the transaction, logs a diagnostic error, and returns `False`. The active locale and direction remain unchanged.
5. **State Commit:**
   - Commits active locale: `self._current_locale = target_id`.
6. **Qt Layout Direction Synchronization:**
   - If Qt is available (`_QT_AVAILABLE`) and `QApplication.instance()` exists, synchronizes application-level layout direction:
     ```python
     target_dir = Qt.RightToLeft if new_catalog.is_rtl else Qt.LeftToRight
     QApplication.instance().setLayoutDirection(target_dir)
     ```

---

## 7. Preference Persistence & Failure Contracts

Parto supports two explicit persistence modes via `strict_persistence`:

### Default Resilient Mode (`strict_persistence=False`)
- Settings persistence is treated as a non-fatal post-commit side effect.
- If writing preferences to disk fails (e.g. read-only filesystem, permission errors, disk quota exceeded):
  - `last_persistence_succeeded` is set to `False`.
  - `last_persistence_error` records the error string.
  - A diagnostic warning is recorded.
  - `set_locale()` returns `True`, ensuring the running editing session remains active in the requested language.
  - In `MainWindow`, user feedback is displayed via a toast notification:
    `toast.language_switched_not_saved` (*"Language changed to {language} (settings not saved)"*).

### Strict Persistence Mode (`strict_persistence=True`)
- Enforces atomic persistence guarantees for scripted or headless operations where settings durability is mandatory.
- If writing preferences fails:
  - An exception is raised and caught by the rollback handler.
  - The active locale is restored to `old_locale`.
  - `QApplication.instance().setLayoutDirection` is restored to the previous direction.
  - `last_persistence_succeeded = False` and `last_persistence_error` are recorded.
  - `set_locale()` returns `False`.

---

## 8. Signals, Observers & UI Refresh Isolation

### Subscriber Isolation:
- **Qt Signals:** `locale_changed` is emitted inside an isolated `try...except` block. Emission exceptions are recorded in `last_listener_failures` and set `last_refresh_completed = False`.
- **Headless Observers:** Listeners registered via `add_locale_listener()` are invoked sequentially in isolated `try...except` blocks. If listener $A$ raises an unhandled exception, it is appended to `last_listener_failures`, `last_refresh_completed` becomes `False`, and listener $B$ continues executing normally.
- **Return Value Semantics:** `set_locale()` returns `True` if the domain locale transition committed, even if downstream subscribers or UI refresh components encountered errors. Callers inspect `manager.last_refresh_completed` and `manager.last_listener_failures` to verify full refresh completion.

### UI Refresh Pipeline (`MainWindow._on_locale_changed`):
When `locale_changed` fires, `MainWindow` updates the user interface through an isolated pipeline:
1. **Window Direction:** Updates `self.setLayoutDirection(Qt.RightToLeft if is_rtl else Qt.LeftToRight)`.
2. **Window Title:** Re-evaluates `_update_window_title()` with localized title strings.
3. **Modular Components:** Iterates through attached components:
   - `toolbar`
   - `statusbar`
   - `welcome_screen`
   - `crop_bar`
   - `brush_bar`
   - `layers_dock`
   - `adjustments_dock`
   - `brush_dock`
   Calling `retranslate_ui()` on each inside isolated `try...except` blocks.
4. **Menu Bar:** Invokes `EditorMenuBar.retranslate_menus(self.menuBar(), self)` in an isolated `try...except` block.
5. **Toast Feedback:** Displays `toast.language_switched` or `toast.language_switched_not_saved`.

### Known Refresh Limitations:
- Dialogs already open on screen (such as `ResizeDialog`, `AboutDialog`, or `ShortcutsDialog`) are not retranslated dynamically while open; their text is bound upon dialog instantiation.

---

## 9. Editor State Preservation

The localization subsystem is strictly decoupled from the editor engine and canvas geometry. Language switching does **not** alter, reset, or clone:
- Current `Document` instance identity.
- Unsaved document modification flag (`is_modified`).
- Layer count, layer order, layer names, layer opacities, layer visibilities, or layer image buffers.
- Undo and redo history stacks, revision numbers, or clean markers.
- Brush tool parameters (size, opacity, hardness, spacing, colors, active preset).
- Active tool selection (`MoveTool`, `CropTool`, `BrushTool`, `EyedropperTool`).
- Canvas viewport zoom factor and center coordinates.
- Active visual theme (`Dark`, `Light`, `Graphite`, `Midnight`, `Nord`).

*Verification Status:* Fully verified by domain unit tests and headless Qt integration tests (`tests/integration/test_locale_state_preservation.py`). State integrity is guaranteed across both successful and failed locale transitions.

---

## 10. How to Add a New Translation Key

To add a new translation key to Parto:

1. **Add Key to English Catalog (`parto/resources/locales/en/locale.json`):**
   ```json
   "dialog.export.watermark": "Add Watermark"
   ```
2. **Add Matching Key to Persian Catalog (`parto/resources/locales/fa/locale.json`):**
   ```json
   "dialog.export.watermark": "افزودن واترمارک"
   ```
3. **Verify Catalog Key Parity:**
   Run the parity verification script:
   ```bash
   python3 -c "
   import json
   en = json.load(open('parto/resources/locales/en/locale.json'))['translations']
   fa = json.load(open('parto/resources/locales/fa/locale.json'))['translations']
   diff = set(en.keys()) ^ set(fa.keys())
   assert not diff, f'Discrepancies found: {diff}'
   print('Key parity verified: exactly', len(en), 'keys matching.')
   "
   ```
4. **Use in Application Code:**
   ```python
   from parto.localization import t

   label = t("dialog.export.watermark", default="Add Watermark")
   ```

---

## 11. How to Add a New Language

Adding a new language requires zero code modifications to the application core:

1. Create a locale directory: `parto/resources/locales/<locale_id>/` (or user directory `~/.parto/locales/<locale_id>/`).
2. Create `locale.json` containing complete metadata and translations:
   ```json
   {
     "schema_version": "1.0.0",
     "metadata": {
       "id": "es",
       "name": "Spanish",
       "native_name": "Español",
       "direction": "ltr",
       "version": "1.0.0",
       "author": "Contributor",
       "plural_rule": "cardinal"
     },
     "translations": {
       "app.name": "Parto",
       "menu.file": "&Archivo",
       "menu.edit": "&Editar"
     }
   }
   ```
3. On application launch, `LocalizationManager` automatically discovers, validates, registers the new catalog, and populates the **Language** menu in the menu bar. Any missing keys automatically fall back to English.

---

## 12. Future Intent Subsystem Integration Contract

Parto provides an architectural formatting hook for future headless tasks and automation agents via `format_intent_response()`:

```python
from parto.localization import get_localization_manager

lm = get_localization_manager()

# Format response in active user locale
msg = lm.format_intent_response("intent.response.operation_completed", operation="Crop")

# Format response in a specific target language independent of UI locale
msg_fa = lm.format_intent_response("intent.response.operation_completed", locale="fa", operation="برش")
```

---

## 13. How to Run Localization Tests

### Localization Unit Test Suites (46 Tests — Pure Python):
Does not require GUI libraries or PySide6; runs using the built-in headless fallback emitter:
```bash
# Core subsystem and lifecycle tests (26 tests)
python3 -m pytest tests/unit/test_localization_core.py -v

# Static and dynamic key coverage, catalog parity, and multilingual CLDR plural tests (20 tests)
python3 -m pytest tests/unit/test_localization_validation.py -v

# Run all 46 localization unit tests together:
python3 -m pytest tests/unit/test_localization_core.py tests/unit/test_localization_validation.py -v
```

### Editor State Preservation Integration Suite (2 Tests — Requires PySide6 & Pillow):
Verifies byte-for-byte preservation across language switches in offscreen mode:
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/integration/test_locale_state_preservation.py -v
```

### Combined Test Execution (All 48 Tests):
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/unit/test_localization_core.py tests/unit/test_localization_validation.py tests/integration/test_locale_state_preservation.py -v
```
