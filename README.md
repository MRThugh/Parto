# Parto (پرتو) — Lightweight Desktop Image Editor

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/MRThugh/Parto)
[![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt-41CD52.svg?logo=qt&logoColor=white)](https://pypi.org/project/PySide6/)
[![Pillow](https://img.shields.io/badge/imaging-Pillow-blue.svg)](https://python-pillow.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Parto** (*پرتو* — Ray / Beam of Light) is a fast, modern, and lightweight desktop image editor designed for daily image tasks without the bloat, slow startup, or visual clutter of heavyweight software.

---

## Highlights of Version 0.2.0

- **Fast & Minimal**: Near-instant launch time and low resource consumption.
- **Refined User Interface**:
  - Polished **Dark** and **Light** themes with smooth transition animations.
  - Resolution-independent **vector icon system** replacing emoji icons with geometric vector graphics.
  - Organized, logically grouped toolbar with intuitive keyboard shortcuts.
- **Modern Welcome Screen**:
  - Clean layout featuring format badges, drag-and-drop zone, and quick launch button.
- **Image Cropping**:
  - Interactive on-canvas crop rectangle with border bounds clamping.
  - Aspect ratio constraints: **Free**, **1:1 (Square)**, **4:3 (Standard)**, and **16:9 (Widescreen)**.
  - Dedicated crop control bar with Apply (`Enter`) and Cancel (`Esc`).
- **Image Resizing**:
  - Aspect ratio locking with automatic bidirectional dimension synchronization.
  - One-click percentage presets: **25%**, **50%**, **75%**, **100%**, **150%**, and **200%**.
  - Real-time resolution and megapixel computation.
- **Transformations**:
  - 90° counter-clockwise (`Ctrl+Shift+L`), 90° clockwise (`Ctrl+Shift+R`), and 180° rotation.
  - Horizontal and vertical flipping.
- **Color Adjustments**:
  - Non-intrusive side-dock for **Brightness**, **Contrast**, and **Saturation**.
  - Real-time preview with individual slider resets and percentage indicators.
  - **Hold to View Original** Before/After comparison button.
- **Photographic Filters**:
  - **Grayscale**, **Sepia**, and **Invert** with full alpha-channel transparency preservation.
  - Filter gallery with live preview and Before/After verification.
- **Technical Image Properties**:
  - Detailed metadata inspector displaying dimensions, aspect ratio, megapixels, color mode, transparency status, file size, and file path with copy-to-clipboard support.
- **Reliable Undo / Redo**:
  - Up to 30 history states tracking all transformations, adjustments, and crops.
- **Status Bar & Pixel Inspector**:
  - Live cursor pixel coordinates $(X, Y)$ and RGB/RGBA channel color inspection.
  - Dynamic display of resolution, aspect ratio, color mode, format, and zoom level.

---

## Supported Formats

Parto supports a wide range of standard and modern image formats through Pillow and pillow-heif:

| Format | Extension | Read | Write | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **PNG** | `.png` | Yes | Yes | Full transparency support |
| **JPEG** | `.jpg`, `.jpeg` | Yes | Yes | Safe alpha compositing |
| **WebP** | `.webp` | Yes | Yes | High compression & quality |
| **BMP** | `.bmp` | Yes | Yes | Bitmap images |
| **TIFF** | `.tiff`, `.tif` | Yes | Yes | High dynamic range & print |
| **HEIC** | `.heic` | Yes | No | Apple device photos |

---

## Architecture & Code Structure

Parto maintains a strict separation of concerns between core image processing and GUI presentation:

```
Parto/
├── main.py            # Application entry point, High-DPI configuration, app metadata
├── window.py          # MainWindow, Canvas (QGraphicsView), Dock, Dialogs, WelcomeScreen, Styles
├── editor.py          # EditorEngine: Pillow-based transformation, adjustment, filter & history logic
├── image.py           # Safe PIL-to-QPixmap conversions & metadata extraction
├── icons.py           # Resolution-independent QPainter vector icon generation
├── test_parto.py      # Comprehensive 30-point automated test suite (pytest)
├── requirements.txt   # Python package dependencies
├── logo.png           # Parto application branding icon
├── LICENSE            # MIT License
├── CHANGELOG.md       # Release notes and version history
└── README.md          # Project documentation
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
