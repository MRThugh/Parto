# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Localization Core Remediation & Hardening (`parto/localization/`)**:
  - Implemented transactional runtime locale switching with atomic rollback upon catalog validation or strict persistence failure.
  - Defined explicit settings persistence failure contract: default resilient mode (`strict_persistence=False`) treats persistence failure as a non-fatal side effect while exposing `last_persistence_succeeded` and `last_persistence_error`; strict mode (`strict_persistence=True`) enforces atomic rollback.
  - Implemented subscriber isolation for Qt signals and headless observer callbacks, tracking errors in `last_listener_failures` and `last_refresh_completed` without aborting other listeners.
  - Added UI refresh subscriber isolation in `MainWindow._on_locale_changed` preventing single-widget failures from corrupting application retranslation.
  - Added `toast.language_switched_not_saved` translation key to both English and Persian catalogs (191 verified keys each).
  - Added comprehensive failure-path unit tests to `tests/unit/test_localization_core.py` covering invalid locale IDs, missing catalogs, malformed catalogs, persistence failures, subscriber isolation, and idempotent no-ops.
  - Added end-to-end integration test suite `tests/integration/test_locale_state_preservation.py` verifying byte-for-byte preservation of document identity, dirty modification flag, layer stacks, undo/redo history, brush settings, active tools, zoom factors, and themes across language switches.
  - Created comprehensive standalone developer guide `docs/LOCALIZATION.md` documenting architecture, schemas, extension workflows, and future Intent integration.

- **Action + Command + History Architecture 2.0 Finalization**:
  - Closed all remaining architectural bypasses and legacy snapshot execution paths across UI, Brush, and Transform domains.
  - Added comprehensive integration tests (`test_architecture_20_closure.py`) validating layer opacity coalescing without snapshot creation, isolated layer brush strokes without document snapshot duplication, transform commands, shortcut/action execution consistency, dirty state tracking, and command palette integration.

### Changed
- **Documentation Audit & Release-Readiness Consistency**:
  - Aligned project documentation (`README.md`, `ARCHITECTURE.md`, `tests/README.md`, `docs/LOCALIZATION.md`, and `parto/brush/README.md`) to clearly distinguish the active `v0.4.0` development release line from the currently declared `0.3.1` package version.
  - Reconciled release status statements: replaced unsupported "Production Ready" and global "FINALIZED" labels with evidence-based status (26 Localization Core unit tests passing; Qt-dependent integration test verification pending in environments lacking PySide6).
  - Clarified test categorization across existing test files (44 files / 357 cases), passing CI tests, pure-Python unit tests, and tests blocked in minimal environments without PySide6.
  - Updated Brush documentation in `parto/brush/README.md` to reflect Architecture 2.0 `PaintStrokeCommand` memory isolation.
- **Layers Panel Opacity Workflow**:
  - Replaced legacy `create_snapshot()` and `record_operation()` calls with authoritative `ChangeLayerOpacityCommand` routed through `HistoryManager.execute()`.
  - Implemented slider drag session tracking to coalesce fine-grained opacity adjustments into a single undo/redo history step while maintaining non-drag atomicity.
- **Brush Stroke Memory Isolation**:
  - Eliminated full-document snapshotting during normal brush stroke lifecycle in `BrushDocumentAdapter`.
  - Optimized stroke history state to isolate only the affected layer's before/after raster images, verifying byte-for-byte pixel integrity across Undo and Redo operations.
- **Transform Command History Encapsulation**:
  - Streamlined `TransformCommand` execution, fully encapsulating snapshot and boundary state inside domain commands and removing controller-level transaction leaks.
- **Action Manager and Pipeline Harmonization**:
  - Ensured all keyboard shortcuts and Command Palette entries route through `ActionManager` and `DocumentController` / `HistoryManager`, strictly adhering to the Architecture 2.0 unidirectional pipeline.

### Fixed
- **Architectural Snapshot Bypasses**:
  - Removed deprecated snapshot history bypass mechanisms from layer opacity and stroke controllers.

- **Modular Document Domain Subsystem (`parto/document/`)**:
  - Independent, engineering-grade domain architecture separating document state, transformation engines, compositing, persistence, transactions, and presentations.
  - Dedicated state model (`DocumentState`) managing canvas dimensions, file path, modified tracking, and authoritative `LayerStack` ownership.
  - Domain engines (`DocumentEngine`, `TransformEngine`, `CompositingEngine`) coordinating offset-aware transformations, non-destructive preview rendering, and layer adjustments without duplicating image-processing algorithms.
  - Persistence adapter (`DocumentStorageAdapter`) providing safe image loading with EXIF orientation normalization, HEIF fallback, and format saving.
  - Centralized transaction coordinator (`TransactionCoordinator`) executing deep state snapshotting, snapshot equality comparison, and atomic undo/redo restoration.
  - Document domain controller (`DocumentController`) orchestrating domain actions, state mutations, and signal notifications.
  - Authoritative `Document` domain model and facade retaining full backward compatibility for `parto/editor/document.py` and `EditorEngine`.
- **Focused Architectural Test Suite (`test_document_subsystem_architecture.py`, `test_contextual_brush_menu.py`)**:
  - 10 new unit and UI integration tests verifying state isolation, transform engines, compositing previews, storage adapters, transaction histories, and contextual menu lifecycles (bringing total coverage to **297 passed tests**).

### Changed
- **Refactored Document Responsibilities**:
  - Transformed `Document` from a multi-responsibility god object into a clean domain boundary and facade.
  - Eliminated duplicate state representation; `DocumentState` acts as the single source of truth for canvas dimensions and layer collections.
  - Decoupled `parto/document/` from GUI and editor dependencies, establishing strict unidirectional architecture: `UI -> Controllers / Facades -> Domain -> Engines / Processing -> Pillow`.
- **Improved Layer and History Integration Boundaries**:
  - Preserved `LayerStack` as the authoritative layer state while standardizing transaction boundaries with `HistoryManager`.
  - Maintained complete undo/redo support across painting, layer operations, crop, resize, rotate, flip, filters, and adjustments without altering user editing workflows.
- **Contextual Brush Studio Architecture**:
  - Brush Studio is now treated as a contextual Brush feature rather than a global View-menu item.
  - Dynamically displays a dedicated `&Brush` menu when the Brush Tool is active, exposing Brush Studio (`F9`), preset navigation (`Ctrl+Shift+B`), tip property focus (`Alt+B`), mode cycling (`Shift+B`), defaults reset (`Shift+F9`), and size/hardness adjustments.
  - Automatically hides the contextual Brush menu and studio dock when switching to Move, Crop, or Eyedropper tools while strictly preserving all active brush settings (size, opacity, hardness, palette colors, eraser mode).

### Fixed
- **Brush Studio Global View-Menu Exposure**:
  - Removed `Brush Studio` from the global `View` menu where it was erroneously displayed regardless of active tool context.
  - Synchronized Brush Studio dock toggle, shortcuts, and menubar representation with active tool changes.

---

## [0.3.1] - 2026-10-04

### Added
- **Professional Brush Studio Subsystem (`parto.ui.panels.brush`, `parto.brush`)**:
  - Full modular studio dock architecture (`BrushStudioDock`) integrating:
    - **Header Card**: Live dab preview responding in real-time to size, hardness, color, angle, and roundness changes; quick actions menu with preset saving, duplicating, resetting, exporting, and importing.
    - **Presets Section**: Responsive preset search (`Ctrl+Shift+B`), category filtering (`Basic`, `Pencil`, `Ink`, `Paint`, `Airbrush`, `Marker`, `Texture`, `Eraser`, `Custom`, `★ Favorites`), and visual icon grid (`PresetGridWidget`) with live-rendered dab thumbnails, right-click context menu, and keyboard navigation.
    - **Tip & Basic Properties**: Synchronized custom sliders and numeric spinboxes for Size (1–500 px), Hardness (0–100%), Spacing (5–200%), Tip Rotation Angle (0–360°), and Tip Roundness (1–100%).
    - **Color Management**: Interactive foreground and background color chips with standard picker, quick color swap (`X`), color reset (`D`), and 8 curated quick palette swatches with click-to-apply and right-click-to-save.
    - **Blend & Rendering**: Opacity and Flow percentage controls, blend mode selection (`Normal`, `Multiply`, `Screen`, `Overlay`, `Darken`, `Lighten`), and Paint / Eraser mode toggle (`Shift+B`).
    - **Brush Dynamics**: Modulation source targeting for Size, Opacity, Flow, and Angle driven by Pressure, Velocity, Tilt, and Random jitter.
    - **Advanced & Stroke Settings**: Anti-aliased stroke smoothing and scatter jitter controls.
  - Complete backward-compatibility facade maintaining `BrushDock` and `BrushPanel` exports.
- **Factory Built-in & Custom Presets**:
  - 14 factory presets categorized across Basic, Pencil, Ink, Paint, Airbrush, Marker, Texture, and Eraser.
  - User preset creation, duplication, renaming, deletion, favorite toggling, and single-preset JSON export/import.
- **Dedicated Brush & Studio Shortcuts**:
  - `B`: Select Brush Tool.
  - `[` / `]`: Decrease / increase brush size.
  - `Shift+[` / `Shift+]`: Decrease / increase brush hardness.
  - `Ctrl+[` / `Ctrl+]`: Decrease / increase brush opacity.
  - `Shift+B`: Cycle between Paint and Eraser mode.
  - `X`: Swap active foreground and background colors.
  - `D`: Reset brush colors to default black and white.
  - `F9`: Toggle Brush Studio panel.
  - `Shift+F9`: Reset all brush parameters to factory defaults.
  - `Ctrl+Shift+B`: Quick-focus preset search in Brush Studio.
  - `Alt+B`: Quick-focus tip properties in Brush Studio.
- **Searchable Shortcuts & Preferences Dialog (`parto.ui.dialogs.shortcuts_dialog`)**:
  - Full-featured shortcut inspector with real-time category filtering, search, and collision-aware remapping.
- **Comprehensive Test Suite Expansion**:
  - Added dedicated unit and UI integration test suites (`test_brush_studio_subsystem.py`, `test_brush_studio_ui.py`) bringing automated test coverage to **287 passed tests**.

### Fixed
- **Merge Down & Blend Mode Correctness (`parto.image.layers`)**:
  - Fixed compositing bug where merging an upper layer down into a lower layer with a non-normal blend mode (e.g. `multiply`, `screen`, `overlay`) caused double-blending against underlying background layers.
  - Reset `lower.blend_mode = "normal"` upon flattening two visible layers, correctly preserving the rendered visual composite before and after merge.
  - Corrected Porter-Duff / W3C alpha blending in `_blend_mode_composite` to properly handle transparent or semi-transparent backdrops ($ba < 1.0$) without clipping to black.
  - Added dedicated regression test suite (`test_parto_v032_merge_blend.py`) covering multi-layer blend mode preservation and history undo/redo.
- **Canonical Vector Icon Aliases**:
  - Resolved missing icon warnings on startup by mapping toolbar and transform action identifiers (`tool_move`, `tool-move`, `tool_crop`, `tool-crop`, `tool_brush`, `tool-brush`, `tool_eyedropper`, `tool-eyedropper`, `rot_left`, `rot-left`, `rot_right`, `rot-right`) to existing canonical vector renderers (`move`, `crop`, `brush`, `eyedropper`, `rotate-ccw`, `rotate-cw`).
  - Audited all 37 application icon categories across New, Open, Save, Export, Transforms, Layers, Tools, and Dialogs to guarantee warning-free rendering.
  - Added dedicated regression test suite (`test_parto_v031_icons.py`) validating icon resolution, crop offset edge cases, resize resampling filters, and save safety flows.

---

## [0.3.0] - 2026-09-21

### Added
- **Authoritative Single-Document Architecture**:
  - Reconciled document state management into `Document` and `LayerStack` as the authoritative single source of truth.
  - Retired `EditorEngine` as an independent state manager; retained it as an API compatibility shim forwarding directly to `Document`.
  - Maintained 100% backward compatibility with existing tests and scripts (`window.py`, `editor.py`, `image.py`, `icons.py`).
- **Multi-Layer Engine & Panel (`parto.image.layers`)**:
  - Full layer stack architecture with non-destructive composition, per-layer opacity, visibility toggle, and layer ordering.
  - Interactive Layers Panel (`F7`) with live thumbnail generation, add, duplicate, delete, reorder, and merge down operations.
  - History coalescing on opacity slider dragging: continuous interactions record a single discrete undo step upon release.
  - Both side dock panels (`Layers` and `Adjustments`) are now cleanly hidden by default on startup for maximum workspace.
- **Professional Interactive Brush Tool (`B`)**:
  - Top context `BrushBar` equipped with Size (1–200 px), Opacity (1–100%), and Hardness (0–100%) sliders and spinboxes.
  - Interactive foreground and background color chips, quick-swatch palette, and standard color dialog picker.
  - Smooth anti-aliased interpolation drawing directly onto the active document layer.
  - Shortcut controls: `[` / `]` for brush size, `X` to swap foreground/background, `D` to reset to default black/white.
- **Live Non-Destructive Adjustments Panel (`F8`)**:
  - Real-time adjustment of Brightness, Contrast, Saturation, and Sharpness with live canvas previewing.
  - "Hold to Compare Original" instant before/after preview inspection button.
  - History coalescing: slider adjustments preview non-destructively; applying commits an atomic single-step undo history item.
- **Normalized, Zero-Conflict Shortcut Architecture**:
  - Systematic audit and re-mapping of all menu and tool shortcuts through `ShortcutManager`.
  - Complete elimination of keyboard shortcut collisions across all menus, tools, and actions.
  - Dynamic Command Palette (`Ctrl+K`) querying registered actions directly from `ShortcutManager`.
  - Comprehensive Keyboard Shortcuts cheat sheet reference dialog (`F1`).
- **Smooth 200ms Theme Crossfade Transitions**:
  - Added `transition_theme` in `ThemeManager` with `QGraphicsOpacityEffect` and `QPropertyAnimation` over viewport captures.
  - 5 curated palettes: **Dark**, **Light**, **Graphite**, **Midnight**, and **Nord** with unified semantic color lookup (`get_semantic_color`).
- **High-DPI Vector Icon System (`parto.resources.icons`)**:
  - Geometric vector icons drawn with `QPainter` paths, supporting canonical hyphenated alias resolution and automatic contrast-aware theme recoloring.
- **Safe Export Pipeline & Error Logging**:
  - Full logging across file I/O, format conversion, and layer operations, eliminating silent `pass` blocks.
  - Safe alpha-channel compositing when exporting transparent layers to JPEG or non-alpha formats.
- **Extended Test Suite (`test_parto_v03.py`)**:
  - Automated tests validating layers, command history, brush strokes, eyedropper, shortcut conflict detection, theme palettes, and export pipeline.

### Changed
- **Entry Point**: Modernized `main.py` to initialize `ThemeManager`, configure High-DPI scaling, set application metadata, and load `MainWindow`.
- **Docks**: Hidden by default on startup for a distraction-free, clean canvas experience.
- **Status Bar & Tool Bar**: Split into dedicated modular components with responsive breadcrumbs, zoom slider, color swatch, and status notifications.

### Fixed
- **Merge Down & Hidden Layer Semantics**: Hidden layers no longer leak unrendered pixels into merged results; visibility states are preserved accurately before and after merge.
- **Offset-Aware Geometry Transformations**: Crop, resize, 90° CW/CCW rotate, 180° rotate, and horizontal/vertical flip operations now properly transform layer canvas-space bounding boxes and coordinate offsets.
- **Single Coordinate System**: Introduced `parto.editor.geometry` module for canonical conversions between Canvas, Layer, and Screen coordinates.
- **Blend Mode Support**: Implemented mathematical compositing for `Normal`, `Multiply`, `Screen`, `Overlay`, `Darken`, and `Lighten` blend modes.
- **Unsaved Changes Safety & Close Event**: Ensured `SaveResult` enum handling across New, Open, and Close actions so cancel/failure never discards document state silently.
- **Canvas Interaction Ownership**: Routed Middle-click and Space-drag gestures exclusively to `MoveTool`, eliminating stuck drag states during tool switches.
- **Brush Tool Hardening**: Unified 1–500px brush size across UI and engine, added `deactivate()` stroke finalization, and synced foreground/background colors.
- **LayerStack Index Management**: Corrected active index tracking when removing or reordering layers.

---

## [0.2.0] - 2026-09-18

### Added
- **Vector Icon System (`icons.py`)**: Resolution-independent, theme-aware geometric vector icons drawn with `QPainter`, replacing emoji toolbar icons across the entire application.
- **Photo Filters**: Dedicated filter gallery and direct menu actions for **Grayscale**, **Sepia**, and **Invert**, with full alpha-channel transparency preservation for RGBA and palette images.
- **Before / After Live Preview**: Interactive comparison feature allowing users to press and hold "Hold to View Original" during color adjustment or filter review, as well as a dedicated toolbar compare toggle.
- **Enhanced Aspect-Ratio Crop**: On-canvas crop tool now supports aspect ratio presets: **Free**, **1:1 (Square)**, **4:3 (Standard)**, and **16:9 (Widescreen)**, with interactive boundary clamping and a dedicated crop control bar.
- **Enhanced Resize Utility**: Resize dialog with bidirectional aspect ratio lock, instant percentage presets (**25%**, **50%**, **75%**, **100%**, **150%**, **200%**), and real-time megapixel calculation.
- **Technical Image Properties Dialog**: Displays verified file metadata including resolution, aspect ratio, megapixels, color mode, transparency status, file size, and file path with copy-to-clipboard functionality.
- **Expanded History Stack**: Undo and Redo stacks increased to 30 depth with strict state tracking and action button state synchronization.
- **Command Palette**: Quick searchable command launcher activated via `Ctrl+Shift+P`.
- **Pixel Color Inspector**: Status bar updates with live $(X, Y)$ coordinates and exact RGB/RGBA channel values as the cursor hovers over canvas pixels.
- **Persian Branding**: Integrated official Persian subtitle ("پرتو — A Fast, Lightweight Image Editor") in the Welcome Screen and About dialog.
- **Comprehensive Test Suite (`test_parto.py`)**: 30-point automated pytest test suite validating transformations, conversions, edge cases, history limits, and UI interactions.

### Changed
- **Visual Design & Themes**: Upgraded both Dark (`#18181b`) and Light (`#f8fafc`) themes with refined typography, balanced contrast, rounded interactive controls, and a smooth fade transition.
- **Toolbar Layout**: Reorganized toolbar into clearly separated functional groups: File, History, Geometry, Rotation/Flip, Adjustments/Filters, Compare, Zoom, and Info/Theme.
- **Safe JPEG Export**: When saving transparent images to JPEG, the engine now composites them cleanly over a solid white background instead of failing or producing corrupted output.
- **Settings Persistence**: User preferences (theme mode and recent file history) are safely persisted using `QSettings` with fallback handling for corrupted configurations.

### Fixed
- Fixed memory collection glitches and surface artifacts during rapid transformations and mouse wheel zooming.
- Fixed crop selection dragging out of bounds by enforcing boundary clamping to image dimensions.
- Fixed unhandled exception when saving images in memory without an existing file path.

---

## [0.1.0] - 2026-09-18

### Added
- Initial project prototype.
- Basic image viewing with `QGraphicsView` and `QGraphicsScene`.
- Basic image transformations (rotate, flip, crop, resize).
- Basic brightness, contrast, and saturation adjustments.
- Welcome screen with open button.
- Dark and Light theme toggle.
- Open, Save, and Save As capabilities for standard image formats.
