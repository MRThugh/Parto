# Parto Brush System Architecture

The Brush subsystem in `parto/brush` is a dedicated, self-contained domain responsible for brush configuration, preset management, input normalization, stroke lifecycles, and raster operations in **Parto v0.3.x**.

---

## 1. Architectural Overview

```text
                         ┌─────────────────────────┐
                         │       Brush UI          │
                         │                         │
                         │  BrushDock (panel)      │
                         │  BrushBar (toolbar)     │
                         └───────────┬─────────────┘
                                     │ (Subscribes / Inspects)
                                     ▼
                         ┌─────────────────────────┐
                         │    Brush Controller     │
                         │                         │
                         │  Authoritative State    │
                         │  Preset Management      │
                         │  Stroke Lifecycle       │
                         └───────────┬─────────────┘
                                     │
                                     ▼
                         ┌─────────────────────────┐
                         │     Input Adapter       │
                         │                         │
                         │  InputNormalizer        │
                         │  PointerState           │
                         └───────────┬─────────────┘
                                     │
                                     ▼
                         ┌─────────────────────────┐
                         │      Brush Engine       │
                         │                         │
                         │  IBrushEngine (Protocol)│
                         │  RasterBrushEngine      │
                         │  BrushRenderer          │
                         │  DabGenerator           │
                         └───────────┬─────────────┘
                                     │
                                     ▼
                         ┌─────────────────────────┐
                         │ Document Adapter Boundary│
                         │                         │
                         │  BrushDocumentAdapter   │
                         │  Snapshot & Rollback    │
                         │  No-Op Detection        │
                         └───────────┬─────────────┘
                                     │
                                     ▼
                         ┌─────────────────────────┐
                         │   Document / LayerStack │
                         │                         │
                         │  Authoritative Pixels   │
                         │  Undo / Redo History    │
                         └─────────────────────────┘
```

---

## 2. Package Structure

- **`models/`**: Pure Python domain models with zero GUI dependencies.
  - `settings.py`: `BrushSettings` encapsulating size (1–500 px), opacity, flow, hardness, spacing, colors, blend mode, observer callbacks, and validation clamping.
  - `preset.py`: `BrushPreset` immutable dataclass representing named configuration states.
  - `stroke.py`: `StrokePoint` and `Stroke` recording active trajectory samples and runtime metadata.
  - `enums.py`: `BlendMode`, `BrushShapeType`, `PointerType`.
- **`input/`**: Input normalization layer.
  - `pointer.py`: `PointerState` standardized platform-independent input data.
  - `normalizer.py`: `InputNormalizer` converting Qt `QMouseEvent`, `QTabletEvent`, coordinates, or raw tuples into `PointerState`.
- **`engine/`**: Rendering algorithms and dab generation (pure Python + Pillow + NumPy).
  - `dab.py`: `DabGenerator` cached radial falloff alpha mask rasterizer.
  - `renderer.py`: `BrushRenderer` interpolating trajectory steps with spacing enforcement and compositing.
  - `brush_engine.py`: `IBrushEngine` protocol and `RasterBrushEngine` implementation.
- **`presets/`**: Preset definitions and safe file storage.
  - `builtin.py`: Factory for immutable built-in presets (`Basic Round`, `Soft Round`, `Hard Round`, `Pencil`, `Ink`, `Marker`, `Airbrush`, `Eraser`).
  - `storage.py`: `PresetStorage` resilient JSON file serialization with graceful corrupted-file recovery.
  - `preset_manager.py`: `BrushPresetManager` coordinating presets, user preset creation, and built-in protection.
- **`controller/`**: Orchestration and lifecycle.
  - `stroke_controller.py`: `StrokeController` managing stroke lifecycle (`start_stroke`, `continue_stroke`, `end_stroke`, `cancel_stroke`) and byte-for-byte no-op detection.
  - `brush_controller.py`: `BrushController` unified facade for settings, presets, stroke controller, and engine.
- **`document_adapter.py`**: `BrushDocumentAdapter` mediating between the brush engine and `Document` / `LayerStack` (snapshots, commits, undo/redo history, composite invalidation).
- **`tools/`**: Tool integration layer.
  - `brush_tool.py`: `BrushTool` subclassing `BaseTool` for Canvas routing, delegating all domain logic to `BrushController`.

---

## 3. Ownership and State Flow

| Component | State Owned |
| :--- | :--- |
| **`BrushSettings`** | Size, opacity, flow, hardness, spacing, colors, eraser mode, observer listeners. |
| **`BrushPreset`** | Named immutable configuration data snapshot. |
| **`BrushPresetManager`** | Built-in presets, user presets list, active preset name, storage path. |
| **`StrokeController`** | Active stroke status, start/current points, pre-stroke layer image, pre-stroke document snapshot. |
| **`BrushDocumentAdapter`** | Target layer resolution, pixel diff check, snapshot commit / rollback. |
| **`Document` / `LayerStack`** | Authoritative canvas dimensions, layers, blend modes, undo/redo command history. |
| **`BrushTool`** | Integration with Parto `Canvas` and toolbar actions. |
| **`BrushDock` / `BrushBar`** | UI views and controls bound to the authoritative `BrushSettings`. |

---

## 4. Stroke Lifecycle & History Integration

1. **`start_stroke(pt, target, doc)`**:
   - `InputNormalizer` normalizes point to `PointerState`.
   - `BrushDocumentAdapter.capture_pre_stroke` takes a pristine snapshot of the active layer and document.
   - Initial dab is stamped onto the layer image buffer.
2. **`continue_stroke(pt, target)`**:
   - Successive points are normalized.
   - `BrushRenderer` calculates step distances from spacing and stamps interpolated dabs.
3. **`end_stroke(doc)`**:
   - Active layer bytes are compared byte-for-byte with the pre-stroke buffer.
   - **No-op check**: If no bytes changed, the snapshot is discarded and no history command is recorded.
   - **Commit**: If pixels changed, `SnapshotCommand` is committed to `doc.history`, document is flagged modified, and composite pixmap is refreshed.
4. **`cancel_stroke(doc)`**:
   - Restores the exact pre-stroke image to the active layer and rolls back document state.

---

## 5. Extension Points

- **Alternative Engines**: Any class implementing `IBrushEngine` can replace `RasterBrushEngine` (e.g., procedural texture brushes, vector brushes).
- **Pressure Dynamics**: `PointerState.pressure` is recorded per `StrokePoint`, enabling pressure-to-size or pressure-to-opacity scaling in `DabGenerator` / `BrushRenderer`.
- **Custom Shapes**: `BrushShapeType` enum and `DabGenerator` allow loading custom grayscale alpha masks or vector shapes.
