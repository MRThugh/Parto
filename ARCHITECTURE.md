# PARTO ARCHITECTURE SPECIFICATION 2.0

**Author & Project Owner:** Ali Kamrani (MRThugh)  
**System:** Parto (پرتو) — Lightweight Desktop Image Editor  
**Version:** Parto v0.3.1  
**Status:** FINALIZED  

```text
PARTO ACTION + COMMAND + HISTORY ARCHITECTURE 2.0
Status: FINALIZED
```

---

## 1. Executive Summary

Parto Architecture 2.0 establishes a decoupled, predictable, and fully reversible interaction model.
It strictly enforces the separation of concerns:

> **UI triggers Actions. Actions coordinate Commands. Commands modify Domain state. History tracks reversible Commands.**

```text
USER INTERFACE (Mouse / Keyboard / Menu / Toolbar / Command Palette / Dock)
                                   │
                                   ↓
                         ACTION SUBSYSTEM
                    (Action / ActionRegistry)
                                   │
                                   ↓
                       CONTROLLER / FAÇADE
                (DocumentController / BrushController)
                                   │
                                   ↓
                         COMMAND SUBSYSTEM
              (Reversible Domain Commands & Transactions)
                                   │
                                   ↓
                           DOMAIN MODEL
              (Document / LayerStack / Layer / BrushEngine)
                                   │
                                   ↓
                         HISTORY SUBSYSTEM
                (HistoryManager / Undo & Redo Stacks)
```

---

## 2. Core Subsystems

### 2.1 Action Subsystem (`parto/actions/`)

An **Action** represents *what the user intends to do*. It is completely decoupled from Qt widgets, GUI layouts, and low-level pixel manipulation.

* **Action (`parto/actions/action.py`)**:
  * `id`: Stable, dotted global identifier (e.g. `document.save`, `layer.create`, `brush.activate`).
  * `name`: User-facing label (e.g. "Save", "New Layer").
  * `description`: Contextual tooltip or status text.
  * `category`: Categorization (`File`, `Edit`, `View`, `Layer`, `Brush`, `Transform`, `Filter`, `Help`).
  * `default_shortcut`: Baseline key combination (e.g. `Ctrl+S`, `Ctrl+Shift+N`).
  * `shortcut`: Active key combination synced with `ShortcutManager`.
  * `icon_name`: Vector icon key.
  * `checkable` & `checked`: Toggleable state representation.
  * `contexts`: Permitted execution scopes (`GLOBAL`, `CANVAS`, `BRUSH`, `LAYERS`, `TEXT_INPUT`, `DIALOG`).
  * `is_enabled(context)`: Pure evaluation function determining availability.
  * `execute(context)`: Triggers controllers or domain operations.

* **ActionRegistry (`parto/actions/registry.py`)**:
  * Central repository of all available application actions.
  * Supports alias mappings for backward compatibility (e.g. `file_save` → `document.save`, `edit_undo` → `history.undo`).
  * Provides fuzzy/substring searching for Command Palette filtering.

* **ActionContext & ActionContextManager (`parto/actions/context.py`)**:
  * Evaluates current execution scope and injects domain references (`document`, `window`, `canvas`, `active_tool`) without coupling Actions to widget layout.

* **ActionManager (`parto/actions/manager.py`)**:
  * Generates and synchronizes `QAction` objects with menus, toolbars, and `ShortcutManager`.

---

### 2.2 Shortcut Subsystem (`parto/shortcuts/`)

Shortcuts target Action IDs, rather than directly referencing widget callbacks:

```text
Keyboard Event → ShortcutManager → Action ID → Action → Controller / Command
```

* Retains deterministic conflict resolution policies:
  * `track`: Default logging and dual tracking for discovery dialogs.
  * `override`: Overrides previous assignment and clears colliding actions.
  * `reject`: Raises explicit conflict errors.
* Resolves legacy shortcut IDs to canonical Action IDs transparently.

---

### 2.3 Command Subsystem (`parto/commands/`)

A **Command** represents *a reversible domain mutation that alters document or layer state*. Commands operate purely against domain models and never manipulate GUI widgets directly.

* **Command Contract (`parto/commands/base.py`)**:
  * `id`: Semantic identifier.
  * `name`: Human-readable description displayed in Undo/Redo labels (e.g. `"Add Layer 2"`, `"Brush Stroke (15px)"`).
  * `execute()`: Initial state execution.
  * `undo()`: Reverses domain state to prior state.
  * `redo()`: Re-applies domain state.
  * `can_execute() -> bool`: Precondition validation.
  * `can_merge(other: Command) -> bool`: Coalescing detection.
  * `merge_with(other: Command) -> bool`: State merging for continuous inputs.

* **Domain Commands**:
  * `CreateLayerCommand`: Inserts layer at target index. Reverses by removing.
  * `DeleteLayerCommand`: Removes layer with index restoration on undo.
  * `DuplicateLayerCommand`: Duplicates active layer.
  * `MoveLayerCommand`: Reorders layers safely.
  * `MergeDownCommand`: Merges upper layer into lower layer with non-destructive layer backups.
  * `ChangeLayerOpacityCommand`: Merges continuous slider adjustments into a single history entry.
  * `ToggleLayerVisibilityCommand`: Toggles layer rendering visibility.
  * `RenameLayerCommand`: Renames layer metadata.
  * `PaintStrokeCommand`: Memory-safe raster stroke undo/redo capturing solely the affected layer's image buffer.
  * `RotateCommand`, `FlipCommand`, `ResizeCommand`, `CropCommand`: Geometric canvas transformations with offset-aware layer handling.
  * `ApplyFilterCommand`, `ColorAdjustmentsCommand`, `RemoveBackgroundCommand`: Photographic filter mutations.
  * `SelectAllCommand`, `DeselectCommand`, `InvertSelectionCommand`: Selection region state management.

---

### 2.4 History Subsystem (`parto/history/`)

* **HistoryManager (`parto/history/manager.py`)**:
  * Standardized entry point: `history.execute(command)`.
  * Validates preconditions via `can_execute()`.
  * Merges consecutive commands if `can_merge()` is True.
  * Manages undo stack, redo stack, and revision indices.
  * Tracks dirty state accurately through clean revision markers (`is_clean`, `set_clean`).

* **Transaction Architecture (`parto/commands/compound.py`)**:
  * `history.begin_transaction(name)`
  * `history.commit_transaction() -> bool`
  * `history.rollback_transaction() -> bool`
  * `with history.transaction("Name"):` context manager.
  * Groups complex multi-step user workflows (e.g. multi-layer batch transforms or composite filter pipelines) into one atomic `TransactionCommand`.
  * Nest-safe: inner transactions nest into outer transaction scope.
  * Exception-safe: rolling back a transaction unrolls all intermediate changes in reverse order, leaving no partial state behind.

---

## 3. Architecture Interaction Diagram

```text
┌─────────────────────────────────────────────────────────────┐
│                      USER INTERFACE                         │
│  [Menu Item]    [Toolbar Button]   [Shortcut]   [Palette]   │
└───────┬─────────────────┬───────────────┬────────────┬──────┘
        │                 │               │            │
        └─────────────────┼───────────────┼────────────┘
                          ↓
               ┌──────────────────────┐
               │    ActionRegistry    │
               │   Action.execute()   │
               └──────────┬───────────┘
                          ↓
               ┌──────────────────────┐
               │  DocumentController  │
               │  (Facade / Pipeline) │
               └──────────┬───────────┘
                          ↓
               ┌──────────────────────┐
               │   HistoryManager     │
               │  .execute(command)   │
               └──────────┬───────────┘
                          │
             ┌────────────┴────────────┐
             ↓                         ↓
   [In Transaction?]            [Can Merge?]
     YES: append to tx           YES: coalesce state
     NO:  execute & push         NO:  execute & push
             │                         │
             └────────────┬────────────┘
                          ↓
               ┌──────────────────────┐
               │     DOMAIN MODEL     │
               │ Document / LayerStack│
               └──────────────────────┘
```

---

## 4. Architectural Rules

1. **Rule 1 — UI does not own domain logic.**  
   Widgets, dialogs, and toolbar buttons only capture user input and trigger Actions.

2. **Rule 2 — Shortcuts target Actions.**  
   Keyboard shortcuts map to stable Action IDs, not widget callback methods.

3. **Rule 3 — Actions do not directly manipulate widgets.**  
   Actions interact with Controllers and Domain objects.

4. **Rule 4 — Commands do not manipulate UI.**  
   Commands operate strictly on domain models (`Document`, `LayerStack`, `Layer`).

5. **Rule 5 — Commands are reversible when appropriate.**  
   Every state-altering command implements symmetric `undo()` and `redo()`.

6. **Rule 6 — History tracks logical user operations.**  
   Continuous interactions (e.g. opacity sliders) merge into a single history entry.

7. **Rule 7 — Document remains authoritative for document state.**  
   `Document` and `DocumentState` own authoritative layer and canvas state.

8. **Rule 8 — Domain code must not depend on UI.**  
   Domain subsystems never import from `parto.ui`.

9. **Rule 9 — Compatibility layers are migration mechanisms, not new feature locations.**  
   Legacy shims are maintained for backward compatibility, while new features target Architecture 2.0.

10. **Rule 10 — Memory Safety.**  
    Commands must store only the necessary state or layer delta rather than duplicating entire document images.

---

## 5. Backward Compatibility Architecture

To prevent regressions across existing test suites, Parto 2.0 provides compatibility adapters:

* `parto.history.commands.SnapshotCommand` is preserved as a fallback checkpoint.
* Legacy command classes (`LayerAddCommand`, `LayerDeleteCommand`, etc.) continue to exist in `parto.history.commands`.
* `ShortcutManager` transparently resolves legacy IDs (`file_save`, `edit_undo`, `view_brush`, `brush_studio`) to Architecture 2.0 Action IDs.
* `Document._record_operation` and `Document._create_snapshot` remain operational for legacy tests and external callers.

---

## 6. Architecture 2.0 Final Closure Verification

The final stabilization pass permanently closed all remaining migration bypasses in Parto v0.3.1:

1. **Layers Panel Opacity Migration**:
   * Removed manual `_opacity_snap` and `record_operation` bypass from `LayersDock`.
   * Routed opacity changes through `ChangeLayerOpacityCommand` via `HistoryManager.execute()`.
   * Added `seal()` support to `ChangeLayerOpacityCommand` to ensure continuous slider interactions coalesce into a single history entry while subsequent gestures create distinct entries.

2. **Brush Snapshot Elimination & Memory Localized Buffering**:
   * Removed full-document `_create_snapshot()` from normal `BrushDocumentAdapter.capture_pre_stroke` and `commit_stroke`.
   * Brush strokes now store only the affected layer's pre- and post-stroke image buffers in `PaintStrokeCommand`.
   * Unrelated layers in multi-layer documents are never duplicated or cloned.
   * Byte-for-byte exact equality between initial/modified pixels verified across undo/redo cycles.

3. **Transform Command History Ownership**:
   * Geometric transforms (`RotateCommand`, `FlipCommand`, `ResizeCommand`, `CropCommand`) are fully encapsulated commands executed via `HistoryManager.execute()`.
   * Controllers never manage or expose snapshot state for transform operations.

4. **ActionManager Full Integration**:
   * Initialized in `MainWindow` with `get_action_manager()`.
   * Fully coordinates canonical Action lookups, legacy alias resolution, dynamic `QAction` generation, bidirectional state synchronization (`update_states`), shortcut synchronization (`sync_shortcut`), and direct trigger dispatch.
   * Full Command Palette compatibility with search filtering and direct Action invocation.

5. **Single Authoritative History Source of Truth**:
   * `HistoryManager` is the sole authoritative history manager in Parto. No UI panel, controller, adapter, or tool maintains private undo/redo stacks.
   * Dirty state (`is_clean`, `is_modified`) is strictly maintained across command executions, undos, redos, saves, and atomic transactions.

---

## 7. Localization Core Architecture (`parto/localization/`)

Parto v0.4.0 establishes a robust, decoupled, and failure-tolerant internationalization and localization architecture.

```text
┌────────────────────────────────────────────────────────────────────────┐
│                          LOCALIZATION SERVICE                          │
│                                                                        │
│   ┌─────────────────────┐               ┌──────────────────────────┐   │
│   │ LanguageCatalog     │  Discover &   │   TranslationCatalog     │   │
│   │     Loader          │ ────────────> │  (Metadata & Entries)    │   │
│   └─────────────────────┘   Validate    └──────────────────────────┘   │
│                                                      │                 │
│                                                      ▼                 │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                    LocalizationManager                         │   │
│   │   - Active Locale & Fallback Chain ('fa' -> 'en' -> default)   │   │
│   │   - Layout Direction Synchronization (LTR <-> RTL)             │   │
│   │   - Future Intent Subsystem Contract (format_intent_response)  │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                 │                                │                     │
│                 ▼                                ▼                     │
│   ┌───────────────────────────┐    ┌───────────────────────────────┐   │
│   │    LocalePreferences      │    │       Subscriber Isolation    │   │
│   │ (Atomic Disk Persistence) │    │  (Qt Signals & Observers)     │   │
│   └───────────────────────────┘    └───────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 7.1 Architecture Components

1. **`LocalizationManager` (`parto/localization/manager.py`)**:
   - Central singleton service coordinating active language selection, catalog registry, translation lookup, layout direction, and observer notifications.
   - Decoupled from UI widgets; fully usable in headless environments and background workers.
2. **`TranslationCatalog` (`parto/localization/catalog.py`)**:
   - Pure domain model encapsulating catalog metadata (BCP 47 identifier, native name, text direction, version) and dictionary of translation keys.
   - Implements strict validation: ensures non-empty IDs, valid schema versions, and rejection of malformed translation types.
3. **`LanguageCatalogLoader` (`parto/localization/loader.py`)**:
   - Discovers catalogs across bundled package paths (`parto/resources/locales/`) and user directories (`~/.parto/locales/`).
   - Safely parses JSON files without code execution risks and logs diagnostics for corrupted files.
4. **`safe_interpolate` & Formatter (`parto/localization/formatting.py`)**:
   - Regex-based named placeholder interpolation without `eval()` or code execution.
   - Tolerant of missing parameters (retains unresolved `{param}` placeholders while returning diagnostic missing sets).
   - Cardinal pluralization engine supporting English (`one`, `other`) and Persian (`one` for 0–1, `other` for $\ge 2$).
5. **`LocalePreferences` (`parto/localization/persistence.py`)**:
   - Atomic disk persistence using temporary file writing and atomic replace (`os.replace`).
   - Resilient against corrupted configuration files and read-only storage.
6. **Layout Direction Synchronization**:
   - Automatically synchronizes application layout direction (`QApplication.setLayoutDirection`) and window layout directions between `Qt.LeftToRight` (English) and `Qt.RightToLeft` (Persian).
7. **Subscriber Isolation & Error Recovery**:
   - Observers are invoked inside isolated `try...except` blocks. An exception in one widget retranslation callback is recorded in `last_listener_failures` and does not prevent other widgets from updating.
   - Persistence failures in default mode (`strict_persistence=False`) are non-fatal side effects; the active session remains in the requested language and UI toast alerts the user that settings were not saved.
8. **Future Intent Subsystem Integration Contract**:
   - Exposes `format_intent_response(key, locale=None, **kwargs)` for headless CLI, scripts, and future intent automation without UI dependencies.

