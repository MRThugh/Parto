# Parto Test Fixtures & Synthetic Data

Author & Maintainer: **Ali Kamrani (علی کامرانی)**

## Purpose
This directory contains specifications and generation logic for synthetic, deterministic test fixtures used throughout the Parto automated QA suite.

## Principles
1. **Zero External Network Dependencies**: All test image fixtures are synthesized algorithmically in memory using Pillow and NumPy during test runs.
2. **Deterministic Arithmetic**: Small dimensions (1×1, 2×2, 4×4, 8×8, and 100×100) with known channel values allow exact integer and floating-point assertions without compression variance.
3. **Alpha Channel Diversity**: Test suites evaluate 4 distinct alpha states:
   - Fully opaque ($\alpha = 255$)
   - Semi-transparent ($\alpha = 128$)
   - Translucent ($\alpha = 64$)
   - Fully transparent ($\alpha = 0$)
4. **Temporary Directory Lifecycle**: All filesystem I/O operations (save, load, reload) execute inside pytest `tmp_path` fixtures and are automatically cleaned up after test termination.
