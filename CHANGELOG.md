# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-09-21

### Added
- **Complete Modular Architecture (`parto/`)**:
  - Replaced monolithic `window.py` with modular subsystem packages: `editor`, `image`, `history`, `shortcuts`, `tools`, `ui`, `utils`, `resources`, `workers`, and `themes`.
  - Maintained 100% backward compatibility via root re-export shims (`window.py`, `editor.py`, `image.py`, `icons.py`).
- **Multi-Layer Engine (`parto.image.layers`)**:
  - Full layer stack architecture with non-destructive composition, per-layer opacity, visibility toggle, and layer ordering.
  - Interactive Layers Panel with live thumbnail generation, add, duplicate, delete, reorder, and merge down operations.
- **Command Pattern & Managed History (`parto.history`)**:
  - Robust Command pattern (`Command`, `SnapshotCommand`, `AddLayerCommand`, `RemoveLayerCommand`, `ApplyAdjustmentCommand`, `ApplyFilterCommand`).
  - Configurable history limit with bounded memory management and transactional undo/redo.
- **Pluggable Interactive Canvas Tools (`parto.tools`)**:
  - `MoveTool`: Freeform viewport panning and layer content repositioning.
  - `CropTool`: 8-handle drag-to-resize selection with aspect-ratio constraints (Free, 1:1, 4:3, 16:9, 3:2) and boundary clamping.
  - `BrushTool`: Freehand drawing directly onto active layer with configurable color and radius.
  - `EyedropperTool`: Live pixel color sampling from composite canvas with RGB/RGBA coordinate inspection.
- **Non-Blocking Background Worker (`parto.workers`)**:
  - `ImageWorkerThread` with cancelable tasks and Qt signals for heavy operations (large file loading, blur/sharpen, format export).
- **Centralized Shortcut Manager (`parto.shortcuts`)**:
  - Comprehensive action registry with category grouping, conflict avoidance, and interactive Keyboard Shortcuts cheat sheet dialog (`Ctrl+/` or `F1`).
- **Modern Theme System (`parto.themes`)**:
  - Dynamic QSS stylesheet generation for 5 curated palettes: **Dark**, **Light**, **Graphite**, **Midnight**, and **Nord**.
  - Dynamic vector icon recoloring based on active theme contrast metrics.
- **Advanced Export Pipeline (`parto.image.export`)**:
  - Comprehensive format support: PNG, JPEG (with white matte RGBA compositing), WebP (lossy & lossless), BMP, and TIFF.
- **Extended Test Suite (`test_parto_v03.py`)**:
  - 12 comprehensive unit and integration tests covering layer stacking, command history, brush strokes, eyedropper, shortcuts, and palettes (totaling 42 passed tests).

### Changed
- **Entry Point**: Modernized `main.py` to initialize `ThemeManager`, set application metadata, and load the new `MainWindow`.
- **Status Bar & Tool Bar**: Split into dedicated modular components with responsive breadcrumbs, zoom slider, color swatch, and status notifications.

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
