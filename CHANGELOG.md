# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
