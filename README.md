# Parto (پرتو) — Lightweight Desktop Image Editor

[![Version](https://img.shields.io/badge/version-0.3.1-blue.svg)](https://github.com/MRThugh/Parto)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-41CD52.svg?logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Pillow](https://img.shields.io/badge/imaging-Pillow-blue.svg)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Parto** (*پرتو* — Ray / Beam of Light) is a fast, modern, and lightweight desktop image editor designed for daily image tasks without the bloat, slow startup, or visual clutter of heavyweight software.

---

## Highlights of Version 0.3.1

- **Professional Brush Studio Subsystem (`parto/brush/`, `parto/ui/panels/brush/`)**:
  - Modular studio dock (`BrushStudioDock`) with live-rendered dab preview, current preset summary, and quick action drawer.
  - Interactive preset grid (`PresetGridWidget`) with live stroke thumbnails, search filtering, category tabs, right-click context menu, and single-preset JSON import/export.
  - 14 factory presets categorized across Basic, Pencil, Ink, Paint, Airbrush, Marker, Texture, and Eraser.
  - Tip properties with synced sliders and spinboxes: Size (1–500 px), Hardness (0–100%), Spacing (5–200%), Tip Rotation Angle (0–360°), and Tip Roundness (1–100%).
  - Dynamics modulation engine for Size, Opacity, Flow, and Angle targeting Pressure, Velocity, Tilt, and Random jitter.
  - Interactive Color management with live foreground and background chips, color swap (`X`), color reset (`D`), and 8-color quick palette swatches.
  - Anti-aliased stroke smoothing and scatter jitter controls.
- **Authoritative Single-Document Architecture**: Unified state management through `Document` (`parto.editor.document`) and `LayerStack` (`parto.image.layers`). All image processing, layer compositing, transformations, filters, and color adjustments route through the central document model. `EditorEngine` operates as a seamless backward-compatibility shim.
- **Multi-Layer System**:
  - Non-destructive RGBA layer stack with per-layer opacity, vector eye visibility toggles, duplication, reordering, and merge down operations.
  - Interactive Layers Panel (`F7`) with continuous opacity slider history coalescing (one undo step per drag gesture).
  - Panels closed by default on startup for maximum canvas workspace.
- **Live Non-Destructive Adjustments Panel (`F8`)**:
  - Real-time color tuning: Brightness, Contrast, Saturation, and Sharpness with live preview and "Hold to Compare Original" inspection.
- **Normalized, Zero-Conflict Keyboard Shortcuts**:
  - Fully audited and normalized keyboard shortcut registry managed via singleton `ShortcutManager`.
  - Searchable Shortcuts & Preferences dialog (`parto.ui.dialogs.shortcuts_dialog`) with real-time category filtering and collision-aware remapping.
  - Dynamic Command Palette (`Ctrl+K`).
- **Dynamic Theming & 200ms Crossfade Transitions**:
  - 5 curated palettes: **Dark**, **Light**, **Graphite**, **Midnight**, and **Nord**.
  - Smooth 200ms crossfade animation (`transition_theme`) using `QGraphicsOpacityEffect` and `QPropertyAnimation`.
- **High-DPI Vector Icon System**:
  - Resolution-independent icons rendered via `QPainter` paths with canonical alias normalization.
- **Robust 287-Test Automated Verification**:
  - 287 automated tests validating brush studio properties, presets, dab generation, layers, command history, eyedropper, shortcuts, and theme palettes.

---

## Supported Formats

Parto supports a wide range of standard and modern image formats through Pillow and pillow-heif:

| Format | Extension | Read | Write | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **PNG** | `.png` | Yes | Yes | Full transparency support |
| **JPEG** | `.jpg`, `.jpeg` | Yes | Yes | Safe alpha compositing with matte |
| **WebP** | `.webp` | Yes | Yes | High compression & quality (lossy/lossless) |
| **BMP** | `.bmp` | Yes | Yes | Bitmap images |
| **TIFF** | `.tiff`, `.tif` | Yes | Yes | High dynamic range & print |
| **HEIC** | `.heic` | Yes | No | Apple device photos |

---

## Architecture & Package Structure

```
Parto/
├── main.py                    # Application entry point, High-DPI configuration & ThemeManager bootstrap
├── window.py                  # Backward-compatibility re-export shim for MainWindow
├── editor.py                  # Backward-compatibility re-export shim for EditorEngine
├── image.py                   # Backward-compatibility re-export shim for conversions & metadata
├── icons.py                   # Backward-compatibility re-export shim for vector icons
├── parto/                     # Core application package
│   ├── brush/                 # Professional Brush Subsystem
│   │   ├── models/            # BrushSettings, BrushPreset, enums (BlendMode, DynamicsControl)
│   │   ├── engine/            # DabGenerator, BrushRenderer, BrushEngine
│   │   ├── presets/           # Builtin presets factory, PresetManager, PresetStorage (JSON)
│   │   ├── controller/        # BrushController & StrokeController
│   │   ├── input/             # PointerState & InputNormalizer
│   │   └── tools/             # BrushTool
│   ├── editor/                # Document model, Canvas, SelectionBox geometry & EditorEngine
│   ├── image/                 # Layers, LayerStack, Filters, Transforms & Safe Export
│   ├── history/               # Command pattern base, Snapshot & Domain Commands, HistoryManager
│   ├── shortcuts/             # Centralized ShortcutManager & ShortcutDefinition registry
│   ├── tools/                 # BaseTool, MoveTool, CropTool, BrushTool, EyedropperTool
│   ├── themes/                # ThemeManager singleton & dynamic palettes (Dark, Light, Graphite, Midnight, Nord)
│   ├── workers/               # ImageWorkerThread with cancellation and Qt signals
│   ├── resources/             # High-DPI QPainter vector icons and logo loader
│   ├── ui/                    # MainWindow, ToolBar, StatusBar, Menus, Panels & Dialogs
│   │   ├── panels/            # Layers, Adjustments, and Brush Studio dock
│   │   │   └── brush/         # BrushStudioDock: Header, Presets, Properties, Dynamics, Color, Blend, Advanced
│   │   └── dialogs/           # Shortcuts, About, Resize, Image Info, Filter Gallery, Command Palette
│   └── utils/                 # Path helpers, settings persistence & error formatting
├── tests/                     # Automated unit, integration, and UI test suites (287 tests)
├── requirements.txt           # Python package dependencies
├── logo.png                   # Parto application branding icon
├── LICENSE                    # MIT License
├── CHANGELOG.md               # Release notes and version history
└── README.md                  # Project documentation
```

---

## Installation

### Prerequisites

- Python 3.10 or newer
- Virtual environment (recommended)

### Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/MRThugh/Parto.git
   cd Parto
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch the application:**
   ```bash
   python main.py
   ```

---

## Keyboard Shortcuts

Parto features a normalized, zero-conflict shortcut system registered through `ShortcutManager`:

### File & App
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Ctrl+N` | New Canvas | Create a blank canvas with custom dimensions |
| `Ctrl+O` | Open Image | Open image file from disk |
| `Ctrl+S` | Save Image | Save active image in-place |
| `Ctrl+Shift+S` | Save As... | Save copy with format selection |
| `Ctrl+Shift+E` | Export As... | Fast export to WebP, JPEG, PNG, or TIFF |
| `Ctrl+I` | Properties & Metadata | Inspect technical image specifications |
| `Ctrl+K` | Command Palette | Search and launch any action instantly |
| `F1` | Shortcut Reference | Searchable cheat sheet reference dialog |
| `F11` | Fullscreen | Toggle fullscreen mode |
| `Ctrl+Q` | Exit | Safely quit Parto (with unsaved changes prompt) |

### Brush & Painting
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `B` | Brush Tool | Freehand painting on active layer |
| `[` / `]` | Brush Size | Decrease / increase brush radius (1–500 px) |
| `Shift+[` / `Shift+]` | Brush Hardness | Decrease / increase radial hardness (0–100%) |
| `Ctrl+[` / `Ctrl+]` | Brush Opacity | Decrease / increase stroke opacity (0–100%) |
| `Shift+B` | Cycle Brush Mode | Toggle between Paint and Eraser mode |
| `X` | Swap Brush Colors | Swap active foreground and background colors |
| `D` | Reset Brush Colors | Reset colors to standard default black & white |
| `F9` | Toggle Brush Studio | Show/hide Brush Studio dock panel |
| `Shift+F9` | Reset Brush Defaults | Reset all brush parameters to factory defaults |
| `Ctrl+Shift+B` | Focus Preset Search | Quick-focus search input in Brush Studio |
| `Alt+B` | Focus Tip Properties | Quick-focus tip properties in Brush Studio |

### Tools & Editing
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `V` | Pan / Move Tool | Pan canvas viewport and drag content |
| `C` | Crop Tool | Interactive 8-handle crop selection |
| `I` | Eyedropper Tool | Inspect and sample canvas pixel color |
| `Enter` | Apply Crop | Execute crop with active bounding box |
| `Esc` | Cancel / Dismiss | Cancel crop or close interactive dialogs |
| `Ctrl+Z` | Undo | Revert last action or stroke |
| `Ctrl+Y` | Redo | Reapply previously undone action |
| `Ctrl+Alt+I` | Resize Image... | Resample canvas dimensions |

### Layers & View
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `F7` | Toggle Layers Panel | Show/hide multi-layer management dock |
| `F8` | Toggle Adjustments | Show/hide real-time color adjustments dock |
| `Ctrl+Shift+N` | New Layer | Create a new transparent layer |
| `Ctrl+J` | Duplicate Layer | Duplicate active layer |
| `Delete` | Delete Layer | Remove active layer from stack |
| `Ctrl+Up` / `Ctrl+Down` | Reorder Layer | Move layer higher or lower in stack |
| `Ctrl+E` | Merge Down | Merge active layer onto layer beneath |
| `Ctrl+=` / `Ctrl++` | Zoom In | Increase canvas zoom factor |
| `Ctrl+-` | Zoom Out | Decrease canvas zoom factor |
| `Ctrl+0` | Fit on Screen | Fit entire canvas inside viewport |
| `Ctrl+1` | 100% Actual Pixels | View image at 1:1 pixel scale |

### Geometry & Transforms
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `Ctrl+R` | Rotate 90° CW | Rotate canvas 90 degrees clockwise |
| `Ctrl+Shift+R` | Rotate 90° CCW | Rotate canvas 90 degrees counter-clockwise |
| `Ctrl+Alt+R` | Rotate 180° | Flip canvas upside down |
| `Ctrl+H` | Flip Horizontal | Mirror canvas horizontally |
| `Ctrl+Shift+H` | Flip Vertical | Mirror canvas vertically |
| `Ctrl+Shift+F` | Filter Gallery | Open interactive filter gallery dialog |

---

## Testing

Parto includes an automated test suite with **287 tests** covering all image processing routines, brush studio properties, dab generation, presets, layers, command history, dialogs, format conversions, and theme transitions.

Run the test suite using pytest:

```bash
pytest
```

---

## Author & Maintainer

- **Author**: Ali Kamrani (علی کامرانی)
- **GitHub**: [@MRThugh](https://github.com/MRThugh)
- **Profile**: [https://github.com/MRThugh](https://github.com/MRThugh)
- **Repository**: [https://github.com/MRThugh/Parto](https://github.com/MRThugh/Parto)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
