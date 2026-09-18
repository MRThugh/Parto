# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
