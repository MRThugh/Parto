# Parto Automated Test Suite & QA Guide

**Author & Maintainer:** Ali Kamrani (علی کامرانی)  
**Release Line:** v0.4.0 (Declared Package Version: `0.3.1`)  
**Application Type:** Native Desktop Image Editor (Python + PySide6)

---

## 1. Directory Structure & Test Inventory

```text
tests/
├── conftest.py                           # Root fixtures, headless offscreen setup & image generators
├── README.md                             # This documentation guide
├── fixtures/
│   └── README.md                         # Synthetic deterministic fixture specifications
├── unit/                                 # Isolated component tests
│   ├── test_actions.py                   # Action model, predicates, scoping & QAction binding
│   ├── test_blend_modes.py               # Mathematical verification of all 6 blend modes
│   ├── test_brush_studio_subsystem.py    # Extended brush settings, presets & dab generators
│   ├── test_brush_subsystem_architecture.py # Decoupled brush engine & stroke controller
│   ├── test_brush_system.py              # Brush settings, presets persistence & color operations
│   ├── test_commands_v2.py               # Domain commands (layers, brush, transform, selections)
│   ├── test_compositing.py               # compose_layers rendering & layer ordering
│   ├── test_document.py                  # Document model, dimensions, layers & dirty tracking
│   ├── test_document_subsystem_architecture.py # DocumentState isolation, transform/compositing engines
│   ├── test_history.py                   # HistoryManager, SnapshotCommand & undo/redo limits
│   ├── test_icons.py                     # Vector icon renderers, cache & alias resolution
│   ├── test_image_operations.py          # Transforms, photographic filters & color adjustments
│   ├── test_import_export.py             # Format saving (PNG, JPEG, WebP, BMP, TIFF)
│   ├── test_layers.py                    # Layer & LayerStack lifecycle, opacity & offsets
│   ├── test_layers_subsystem_architecture.py # Pure-python layer model, blender & compositor
│   ├── test_localization_core.py         # 26 unit tests: catalogs, validation, fallback, atomicity
│   ├── test_transactions.py              # Compound transactions & rollback mechanics
│   └── test_version_consistency.py       # Repository-wide version audit & attribution checks
├── integration/                          # End-to-end multi-component workflows
│   ├── test_action_pipeline.py           # Action to Command to History pipeline
│   ├── test_application_startup.py       # Application bootstrap, High-DPI & dock defaults
│   ├── test_architecture_20_closure.py   # Snapshot bypass elimination & layer stroke isolation
│   ├── test_editing_workflows.py         # Adjustments, transforms, undo & redo chain
│   ├── test_layer_workflows.py           # Multi-layer authoring, duplication & export
│   ├── test_locale_state_preservation.py # 2 integration tests: editor state across language switches
│   └── test_save_reload.py               # Disk roundtrip fidelity & modified state reset
├── regression/                           # Verified bug fixes & regression guards
│   ├── test_alpha_compositing.py         # Filter alpha preservation & Porter-Duff backdrop
│   ├── test_issue_regressions.py         # Offset-aware crop, resize, rotate & flip math
│   ├── test_merge_down_blend_modes.py    # Double-blending prevention & normal reset
│   ├── test_merge_down_visibility.py     # All 4 visibility combinations of Merge Down
│   └── test_undo_redo_regressions.py     # Brush pixel restoration & no-op stroke suppression
├── ui/                                   # Headless Qt GUI interaction tests
│   ├── test_brush_dock_integration.py    # Brush dock two-way sync & auto-activation
│   ├── test_brush_studio_ui.py           # Brush studio dock composition & property widgets
│   ├── test_contextual_brush_menu.py     # Contextual brush menu lifecycle & tool switching
│   ├── test_dialogs.py                   # About, Resize, Image Info & Shortcuts dialogs
│   ├── test_main_window.py               # MainWindow shell, canvas & zoom
│   └── test_shortcuts.py                 # Conflict detection & resolution policies
└── legacy/                               # Preserved historical test files for exact provenance
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

## 2. Test Execution Status & Categorization

To maintain strict truth-in-documentation, tests are classified into four clear states:

1. **Test Files & Cases Present**:
   - The test repository contains 44 test files defining 328 test functions and 357 parameterized test cases across unit, integration, regression, UI, and legacy suites.
2. **Tests Verified Passing (Environment-Dependent)**:
   - **Full CI Suite (357 passed)**: In automated CI environments (Ubuntu 22.04 with PySide6, Pillow, NumPy, and offscreen Qt libraries), all 357 test cases passed (reference: `reports/test_report.xml`).
   - **Localization Core Unit Suite (26 passed)**: The 26 tests in `tests/unit/test_localization_core.py` are pure-Python compatible and verify catalog loading, validation, plural rules, safe interpolation, fallback resolution, subscriber isolation, and rollback semantics.
3. **Tests Blocked by Missing Dependencies**:
   - In environments where Python packages (`pytest`, `PySide6`, `Pillow`, `numpy`) are not installed, test runner commands cannot execute.
   - Qt-dependent tests (including `test_locale_state_preservation.py` and all tests in `tests/ui/`) fail on import if `PySide6` or system X11/EGL libraries are unavailable.
4. **Integration Verification Pending**:
   - The Localization editor state preservation test (`tests/integration/test_locale_state_preservation.py`) is implemented, but its verification remains *pending* in environments lacking PySide6. Do not mark this integration test as passing without an active test execution in an environment containing PySide6.

---

## 3. Environment & Prerequisites

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

## 4. How to Run Tests

### Running the Entire Test Suite (Full Environment)
From the project root:
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest
```

### Running Localization Test Suites
```bash
# Localization Core Unit Tests (26 tests — Pure Python / Headless fallback)
python3 -m pytest tests/unit/test_localization_core.py -v

# Editor State Preservation Integration Tests (2 tests — Requires PySide6 & Pillow)
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/integration/test_locale_state_preservation.py -v

# Run All Localization Tests Combined (when PySide6 is installed)
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/unit/test_localization_core.py tests/integration/test_locale_state_preservation.py -v
```

### Running by Category
```bash
# Unit Tests
python3 -m pytest tests/unit/

# Integration Tests (Requires PySide6)
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/integration/

# Regression Tests
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/regression/

# UI & Dialog Tests (Requires PySide6)
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ui/

# Historical Legacy Suite
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/legacy/
```

### Running a Specific Test File
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/unit/test_blend_modes.py -v
```

### Generating an XML Test Report
```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest --junitxml=reports/test_report.xml -v
```

---

## 5. Version Source of Truth & Release Line Policy

The single authoritative source of truth for the package version is:
```python
# parto/__init__.py
__version__ = "0.3.1"
```

### Release Line Distinction:
- **Declared Version (`0.3.1`)**: Set in `parto/__init__.py`, `pyproject.toml`, and `package.json`. Represents the latest stable packaged release.
- **Active Release Line (`v0.4.0`)**: Represents the ongoing development milestone (containing Localization Core and Architecture 2.0 finalization) tracked under `## [Unreleased]` in `CHANGELOG.md`.
- `tests/unit/test_version_consistency.py` explicitly enforces that `0.4.0` is not prematurely set as `parto.__version__` before the milestone is formally released.

### Version Update Procedure (Upon Formal Milestone Release):
1. Update `__version__ = "0.4.0"` in `parto/__init__.py`.
2. Update `version = "0.4.0"` in `pyproject.toml` and `package.json`.
3. Promote `## [Unreleased]` to `## [0.4.0] - YYYY-MM-DD` in `CHANGELOG.md`.
4. Update `tests/unit/test_version_consistency.py` assertions for the new release line.
5. Update version badge in `README.md`.
6. Run the consistency suite:
   ```bash
   QT_QPA_PLATFORM=offscreen python3 -m pytest tests/unit/test_version_consistency.py
   ```
