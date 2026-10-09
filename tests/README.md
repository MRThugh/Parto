# Parto Automated Test Suite & QA Guide

**Author & Maintainer:** Ali Kamrani (علی کامرانی)  
**Release Line:** 0.3.x (Current: `0.3.1`)  
**Application Type:** Native Desktop Image Editor (Python + PySide6)

---

## 1. Directory Structure

```text
tests/
├── conftest.py                       # Root fixtures, headless offscreen setup & image generators
├── README.md                         # This documentation guide
├── fixtures/
│   └── README.md                     # Synthetic deterministic fixture specifications
├── unit/                             # Isolated component tests
│   ├── test_document.py              # Document model, dimensions, layers & dirty tracking
│   ├── test_layers.py                # Layer & LayerStack lifecycle, opacity & offsets
│   ├── test_blend_modes.py           # Mathematical verification of all 6 blend modes
│   ├── test_compositing.py           # compose_layers rendering & layer ordering
│   ├── test_history.py               # HistoryManager, SnapshotCommand & undo/redo limits
│   ├── test_image_operations.py      # Transforms, photographic filters & color adjustments
│   ├── test_import_export.py         # Format saving (PNG, JPEG, WebP, BMP, TIFF)
│   ├── test_icons.py                 # Vector icon renderers, cache & alias resolution
│   ├── test_localization_core.py     # Localization catalog, validation, fallback, atomicity
│   └── test_version_consistency.py   # Repository-wide version audit & attribution checks
├── integration/                      # End-to-end multi-component workflows
│   ├── test_layer_workflows.py       # Multi-layer authoring, duplication & export
│   ├── test_editing_workflows.py     # Adjustments, transforms, undo & redo chain
│   ├── test_locale_state_preservation.py # Editor state preservation during language switch
│   ├── test_save_reload.py           # Disk roundtrip fidelity & modified state reset
│   └── test_application_startup.py   # Application bootstrap, High-DPI & dock defaults
├── regression/                       # Verified bug fixes & regression guards
│   ├── test_merge_down_visibility.py # All 4 visibility combinations of Merge Down
│   ├── test_merge_down_blend_modes.py# Double-blending prevention & normal reset
│   ├── test_alpha_compositing.py     # Filter alpha preservation & Porter-Duff backdrop
│   ├── test_undo_redo_regressions.py # Brush pixel restoration & no-op stroke suppression
│   └── test_issue_regressions.py     # Offset-aware crop, resize, rotate & flip math
├── ui/                               # Headless Qt GUI interaction tests
│   ├── test_main_window.py           # MainWindow shell, canvas & zoom
│   ├── test_dialogs.py               # About, Resize, Image Info & Shortcuts dialogs
│   └── test_shortcuts.py             # Conflict detection & resolution policies
└── legacy/                           # Preserved historical test files for exact provenance
    ├── test_parto.py
    ├── test_parto_hardening.py
    ├── test_parto_rc.py
    ├── test_parto_v03.py
    ├── test_parto_v031_icons.py
    ├── test_parto_v032_merge_blend.py
    ├── test_parto_v03_stabilization.py
    └── test_parto_v03_stabilization_pass.py
```

---

## 2. Environment & Prerequisites

- **Python Version**: Python 3.10, 3.11, or 3.12.
- **Core Runtime Dependencies**:
  - `PySide6>=6.4.0` (Qt for Python GUI framework)
  - `Pillow>=9.5.0` (Digital image processing)
  - `numpy>=1.24.0` (Vectorized image compositing and blend mathematics)
  - `pillow-heif>=0.10.0` (HEIC format opener)
- **Test Dependencies**:
  - `pytest>=7.0.0`

### Linux Headless Requirements
When running in headless container environments or CI runners without an active X11 display server, ensure the following native packages are installed:
```bash
sudo apt-get update && sudo apt-get install -y \
    libegl1 libgl1 libxkbcommon-x11-0 libfontconfig1 libdbus-1-3 \
    libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
    libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0
```

---

## 3. How to Run Tests

### Running the Entire Test Suite
From the project root:
```bash
QT_QPA_PLATFORM=offscreen pytest
```

### Running Localization Test Suites
```bash
# Localization Core Unit Tests (Catalogs, validation, formatting, fallback, failure-paths)
QT_QPA_PLATFORM=offscreen pytest tests/unit/test_localization_core.py -v

# Editor State Preservation Integration Tests (Document, layers, history, brush, zoom, theme)
QT_QPA_PLATFORM=offscreen pytest tests/integration/test_locale_state_preservation.py -v

# Run All Localization Tests Combined
QT_QPA_PLATFORM=offscreen pytest tests/unit/test_localization_core.py tests/integration/test_locale_state_preservation.py -v
```

### Running by Category
```bash
# Unit Tests
QT_QPA_PLATFORM=offscreen pytest tests/unit/

# Integration Tests
QT_QPA_PLATFORM=offscreen pytest tests/integration/

# Regression Tests
QT_QPA_PLATFORM=offscreen pytest tests/regression/

# UI & Dialog Tests
QT_QPA_PLATFORM=offscreen pytest tests/ui/

# Historical Legacy Suite
QT_QPA_PLATFORM=offscreen pytest tests/legacy/
```

### Running a Specific Test File
```bash
QT_QPA_PLATFORM=offscreen pytest tests/unit/test_blend_modes.py -v
```

### Generating an XML / HTML Test Report
```bash
QT_QPA_PLATFORM=offscreen pytest --junitxml=reports/test_report.xml -v
```

---

## 4. Version Source of Truth & Update Procedure

The single authoritative source of truth for the application version is:
```python
# parto/__init__.py
__version__ = "0.3.1"
```

### Update Procedure:
1. Update `__version__ = "X.Y.Z"` in `parto/__init__.py`.
2. Update `version = "X.Y.Z"` in `pyproject.toml` and `package.json`.
3. Add release section `## [X.Y.Z] - YYYY-MM-DD` in `CHANGELOG.md`.
4. Update version badge in `README.md`.
5. Run the automated consistency check:
   ```bash
   QT_QPA_PLATFORM=offscreen pytest tests/unit/test_version_consistency.py
   ```
