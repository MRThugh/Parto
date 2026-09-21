# Parto (پرتو) — Lightweight Desktop Image Editor

[![Version](https://img.shields.io/badge/version-0.3.0-blue.svg)](https://github.com/MRThugh/Parto)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-41CD52.svg?logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Pillow](https://img.shields.io/badge/imaging-Pillow-blue.svg)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Parto** (*پرتو* — Ray / Beam of Light) is a fast, modern, and lightweight desktop image editor designed for daily image tasks without the bloat, slow startup, or visual clutter of heavyweight software.

---

## Highlights of Version 0.3.0

- **Modular Architecture**: Complete redesign separating state, UI presentation, command history, and tool logic into a maintainable `parto/` package.
- **Multi-Layer System**: Non-destructive layer stack with opacity controls, visibility toggles, duplicate, reorder, and merge operations.
- **Transactional Undo / Redo**: Command pattern (`parto.history`) tracking all modifications with configurable history depth and bounded memory.
- **Interactive Tool Palette**:
  - **Move Tool (`V`)**: Viewport panning and layer offset movement.
  - **Crop Tool (`C`)**: 8-handle interactive bounding box with aspect ratio presets (Free, 1:1, 4:3, 16:9, 3:2).
  - **Brush Tool (`B`)**: Freehand drawing directly onto the active layer with configurable color and radius.
  - **Eyedropper (`I`)**: Real-time pixel color inspection with direct active color selection.
- **Dynamic Theming System**:
  - 5 curated palettes: **Dark**, **Light**, **Graphite**, **Midnight**, and **Nord**.
  - Adaptive contrast-aware vector icons.
- **Asynchronous Worker Thread**: Non-blocking image processing pipeline (`parto.workers`) for heavy computations and file I/O.
- **Centralized Keyboard Shortcut Registry**: Searchable keyboard shortcuts cheat sheet dialog (`Ctrl+/` or `F1`).
- **Comprehensive Test Coverage**: 42 automated tests validating backward compatibility, layers, tools, history, and exports.

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

| Shortcut | Action |
| :--- | :--- |
| `Ctrl+O` | Open Image |
| `Ctrl+S` | Save Image |
| `Ctrl+Shift+S` | Save As... |
| `Ctrl+Z` | Undo |
| `Ctrl+Y` | Redo |
| `Ctrl+K` | Toggle Crop Tool |
| `Ctrl+R` | Resize Dialog |
| `Ctrl+Shift+L` | Rotate Left (90° CCW) |
| `Ctrl+Shift+R` | Rotate Right (90° CW) |
| `Ctrl++` | Zoom In |
| `Ctrl+-` | Zoom Out |
| `Ctrl+0` | Fit Image to Window |
| `Ctrl+1` | Actual Size (100%) |
| `Ctrl+I` | Image Properties |
| `Ctrl+T` | Toggle Dark / Light Theme |
| `Ctrl+Shift+P` | Open Command Palette |
| `Ctrl+Q` | Exit Application |
| `Enter` | Apply Crop (in crop mode) |
| `Esc` | Cancel Crop / Close Dialogs |

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
