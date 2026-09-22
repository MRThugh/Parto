import os

# Ensure headless offscreen platform for PySide6 in container environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
