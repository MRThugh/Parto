# tests/unit/test_version_consistency.py
"""
Unit Tests — Version Consistency & Maintainer Attribution Audit
Author & Maintainer: Ali Kamrani (علی کامرانی)

Enforces:
1. Single source of truth: `parto.__version__`.
2. All runtime components derive from `parto.__version__`.
3. Packaging configuration (pyproject.toml, package.json) matches `parto.__version__`.
4. CHANGELOG latest entry matches `parto.__version__`.
5. No accidental declaration of unreleased 0.4.0 as current release.
6. Attribution identifies Ali Kamrani (علی کامرانی) as Author & Maintainer.
"""

import json
import os
import re
import pytest

import parto
from parto import __version__, __author__


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))


def test_authoritative_version_format():
    """Verify parto.__version__ follows Semantic Versioning (X.Y.Z)."""
    assert isinstance(__version__, str)
    match = re.match(r"^(\d+)\.(\d+)\.(\d+)$", __version__)
    assert match is not None, f"Version '{__version__}' is not valid semver (X.Y.Z)"
    major, minor, patch = map(int, match.groups())
    assert (major, minor) == (0, 3), f"Expected 0.3.x release line, got {major}.{minor}"
    assert patch >= 1, f"Expected at least 0.3.1, got {patch}"


def test_maintainer_attribution():
    """Verify maintainer attribution identifies Ali Kamrani (علی کامرانی)."""
    assert "Ali Kamrani" in __author__
    assert "علی کامرانی" in __author__


def test_pyproject_toml_version_consistency():
    """Verify pyproject.toml matches parto.__version__."""
    pyproject_path = os.path.join(REPO_ROOT, "pyproject.toml")
    assert os.path.exists(pyproject_path), "pyproject.toml missing"

    with open(pyproject_path, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    assert match is not None, "Version not found in pyproject.toml"
    assert match.group(1) == __version__


def test_package_json_version_consistency():
    """Verify package.json matches parto.__version__."""
    package_json_path = os.path.join(REPO_ROOT, "package.json")
    if os.path.exists(package_json_path):
        with open(package_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data.get("version") == __version__


def test_changelog_latest_release_matches_version():
    """Verify CHANGELOG.md top release matches the current version."""
    changelog_path = os.path.join(REPO_ROOT, "CHANGELOG.md")
    assert os.path.exists(changelog_path), "CHANGELOG.md missing"

    with open(changelog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find first release header: ## [X.Y.Z]
    match = re.search(r"^##\s*\[(\d+\.\d+\.\d+)\]", content, re.MULTILINE)
    assert match is not None, "No release header found in CHANGELOG.md"
    latest_changelog_ver = match.group(1)
    assert latest_changelog_ver == __version__, (
        f"CHANGELOG latest release [{latest_changelog_ver}] does not match "
        f"parto.__version__ ({__version__})"
    )


def test_no_premature_0_4_0_release():
    """Ensure future milestone 0.4.0 is not claimed as current active release."""
    assert __version__ != "0.4.0", "0.4.0 cannot be set as the current release before milestone release!"


def test_server_py_reports_authoritative_version():
    """Verify server.py references the authoritative version and author."""
    server_path = os.path.join(REPO_ROOT, "server.py")
    with open(server_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "from parto import __version__" in code
    assert "from parto import" in code and "__author__" in code


def test_main_py_reports_authoritative_version():
    """Verify main.py configures QApplication version from parto.__version__."""
    main_path = os.path.join(REPO_ROOT, "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        code = f.read()

    assert "from parto import __version__" in code
    assert "app.setApplicationVersion(__version__)" in code


def test_about_dialog_reports_dynamic_version(qapp):
    """Verify AboutDialog displays the current version dynamically."""
    from parto.ui.dialogs.about import AboutDialog
    dlg = AboutDialog()
    title_labels = [w for w in dlg.findChildren(object) if hasattr(w, "text") and f"v{__version__}" in w.text()]
    assert len(title_labels) >= 1, f"AboutDialog does not display current version v{__version__}"
    dlg.close()
