# Parto (پرتو) — Lightweight Desktop Image Editor

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/MRThugh/Parto)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-41CD52.svg?logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Pillow](https://img.shields.io/badge/imaging-Pillow-blue.svg)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Parto** (*پرتو* — Ray / Beam of Light) is a fast, modern, and lightweight desktop image editor designed for daily image tasks without the bloat, slow startup, or visual clutter of heavyweight software.

---

## Highlights of Version 0.3.0

- **Authoritative Single-Document Architecture**: Unified state management through `Document` (`parto.editor.document`) and `LayerStack` (`parto.image.layers`). All image processing, layer compositing, transformations, filters, and color adjustments route through the central document model. `EditorEngine` operates as a seamless backward-compatibility shim.
- **Multi-Layer System**:
  - Non-destructive RGBA layer stack with per-layer opacity, vector eye visibility toggles, duplication, reordering, and merge down operations.
  - Interactive Layers Panel (`F7`) with continuous opacity slider history coalescing (one undo step per drag gesture).
  - Panels closed by default on startup for maximum canvas workspace.
- **Live Non-Destructive Adjustments Panel (`F8`)**:
  - Real-time color tuning: Brightness, Contrast, Saturation, and Sharpness.
  - Live on-canvas non-destructive preview compositing.
  - "Hold to Compare Original" instant before/after inspection.
  - Atomic single-step undo history commit upon clicking Apply.
- **Professional Interactive Brush Tool (`B`)**:
  - Top context Brush Bar with size (1–200 px), opacity (1–100%), and hardness (0–100%) controls.
  - Interactive foreground/background color swatches, color picker dialog, and curated palette chips.
  - Anti-aliased smooth interpolated brush strokes directly onto the active document layer.
  - Professional shortcuts: `[` / `]` for brush size, `X` to swap foreground/background colors, `D` to reset to default black/white.
- **Normalized, Zero-Conflict Keyboard Shortcuts**:
  - Fully audited and normalized keyboard shortcut registry managed via singleton `ShortcutManager`.
  - Zero key collisions across all menus, tools, layers, and navigation actions.
  - Interactive searchable shortcut reference cheat sheet dialog (`F1`).
  - Searchable Command Palette (`Ctrl+K`).
- **Dynamic Theming & 200ms Crossfade Transitions**:
  - 5 curated palettes: **Dark**, **Light**, **Graphite**, **Midnight**, and **Nord**.
  - Smooth 200ms crossfade animation (`transition_theme`) using `QGraphicsOpacityEffect` and `QPropertyAnimation`.
  - Comprehensive semantic color lookups (`get_semantic_color`).
- **High-DPI Vector Icon System**:
  - Resolution-independent icons rendered via `QPainter` paths with canonical alias normalization.
  - Automatic contrast-aware color adaptation based on active theme.
- **Robust Exception Handling & Safe Export**:
  - Full logging across file I/O, format conversion, and layer composition.
  - Safe alpha-channel compositing when exporting transparent layers to formats without native transparency (e.g. JPEG white matte).
- **Extended Test Suite**:
  - Automated test coverage validating layers, command history, brush strokes, eyedropper, shortcut conflict detection, theme palettes, and export pipeline.

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
├── test_parto.py              # Baseline compatibility test suite (30 tests)
├── test_parto_v03.py          # Parto v0.3.0 subsystem test suite (12 tests)
├── parto/                     # Core application package
│   ├── editor/                # Document model, Canvas, SelectionBox geometry & EditorEngine
│   ├── image/                 # Layers, LayerStack, Filters, Transforms & Safe Export
│   ├── history/               # Command pattern base, Snapshot & Domain Commands, HistoryManager
│   ├── shortcuts/             # Centralized ShortcutManager & ShortcutDefinition registry
│   ├── tools/                 # BaseTool, MoveTool, CropTool, BrushTool, EyedropperTool
│   ├── themes/                # ThemeManager singleton & dynamic palettes (Dark, Light, Graphite, Midnight, Nord)
│   ├── workers/               # ImageWorkerThread with cancellation and Qt signals
│   ├── resources/             # High-DPI QPainter vector icons and logo loader
│   ├── ui/                    # MainWindow, ToolBar, StatusBar, Menus, Panels & Dialogs
│   └── utils/                 # Path helpers, settings persistence & error formatting
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

Parto v0.3.0 features a normalized, zero-conflict shortcut system registered through `ShortcutManager`:

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

### Tools & Editing
| Shortcut | Action | Description |
| :--- | :--- | :--- |
| `V` | Pan / Move Tool | Pan canvas viewport and drag content |
| `C` | Crop Tool | Interactive 8-handle crop selection |
| `B` | Brush Tool | Freehand painting on active layer |
| `I` | Eyedropper Tool | Inspect and sample canvas pixel color |
| `[` / `]` | Brush Size | Decrease / increase brush radius |
| `X` | Swap Brush Colors | Swap active foreground and background colors |
| `D` | Reset Brush Colors | Reset colors to standard default black & white |
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

Parto includes a 30-point automated test suite covering all image processing routines, history states, dialog presets, format conversions, and theme transitions.

Run the test suite using pytest:

```bash
pytest -v test_parto.py
```

---

## Author & Maintainer

- **Author**: Ali Kamrani
- **GitHub**: [@MRThugh](https://github.com/MRThugh)
- **Profile**: [https://github.com/MRThugh](https://github.com/MRThugh)
- **Repository**: [https://github.com/MRThugh/Parto](https://github.com/MRThugh/Parto)

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
