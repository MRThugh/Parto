import os
import pytest

# Ensure headless offscreen platform for PySide6 in container environments
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp():
    try:
        from PySide6.QtWidgets import QApplication
    except (ImportError, Exception) as e:
        pytest.skip(f"PySide6.QtWidgets is unavailable: {e}")
    app = QApplication.instance()
    if app is None:
        app = QApplication(["--platform", "offscreen"])
    return app
