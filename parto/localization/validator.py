# parto/localization/validator.py
"""
Parto Localization Subsystem — Static Key Reference Validator & Parity Checker
AST-based static analysis tool verifying that all translation keys referenced in the
application codebase exist in translation catalogs, and that catalogs maintain key parity.
Author & Maintainer: Ali Kamrani (علی کامرانی)
"""

from __future__ import annotations
import ast
import os
from typing import Dict, List, Set, Tuple, Optional

from .catalog import TranslationCatalog


TRANSLATION_FUNCTION_NAMES = {
    "t",
    "translate",
    "translate_plural",
    "translate_for_locale",
    "format_intent_response",
}


class _TranslationKeyASTVisitor(ast.NodeVisitor):
    """AST visitor extracting string literal keys from translation calls and known mappings."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.keys: List[Tuple[str, int]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in TRANSLATION_FUNCTION_NAMES:
            # Check first positional argument: t("some.key", ...)
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                self.keys.append((node.args[0].value, node.lineno))
            # Check keyword argument: t(key="some.key", ...)
            elif node.keywords:
                for kw in node.keywords:
                    if kw.arg in ("key", "message_key") and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                        self.keys.append((kw.value.value, node.lineno))

        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict) -> None:
        # Detect explicit static mappings like TOOLBAR_ACTION_KEYS = { ... }
        for k, v in zip(node.keys, node.values):
            if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                val_str = str(v.value)
                if any(val_str.startswith(prefix) for prefix in ("action.", "tool.", "menu.", "filter.", "brush.", "dialog.", "status.", "panel.", "toast.")):
                    self.keys.append((val_str, getattr(v, "lineno", node.lineno)))
        self.generic_visit(node)


def extract_static_keys_from_file(filepath: str) -> List[Tuple[str, int]]:
    """Parse a single Python source file and return all statically identifiable translation keys."""
    if not os.path.isfile(filepath):
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source, filename=filepath)
        visitor = _TranslationKeyASTVisitor(filepath)
        visitor.visit(tree)
        return visitor.keys
    except Exception:
        return []


def scan_codebase_translation_keys(root_dir: str) -> Dict[str, List[Tuple[str, int]]]:
    """
    Recursively scan Python source files in root_dir for statically referenced translation keys.
    Excludes test suites, third-party packages, and virtual environments.
    Returns mapping of key -> list of (filepath, lineno).
    """
    results: Dict[str, List[Tuple[str, int]]] = {}
    excluded_dirs = {
        ".git",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        "tests",
        "venv",
        ".venv",
        "build",
        "dist",
    }

    for current_root, dirs, files in os.walk(root_dir):
        # Prune excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith(".")]

        for filename in files:
            if filename.endswith(".py"):
                filepath = os.path.join(current_root, filename)
                # Skip legacy test scripts at root if any
                if filename.startswith("test_") or "test" in current_root.split(os.sep):
                    continue
                found_keys = extract_static_keys_from_file(filepath)
                for key_name, lineno in found_keys:
                    results.setdefault(key_name, []).append((filepath, lineno))

    return results


def validate_catalog_parity(
    cat_a: TranslationCatalog,
    cat_b: TranslationCatalog,
) -> Tuple[bool, Set[str], Set[str]]:
    """
    Check key parity between two catalogs.
    Returns (is_equal, missing_in_b, missing_in_a).
    """
    keys_a = cat_a.keys()
    keys_b = cat_b.keys()
    missing_in_b = keys_a - keys_b
    missing_in_a = keys_b - keys_a
    is_equal = (len(missing_in_b) == 0 and len(missing_in_a) == 0)
    return is_equal, missing_in_b, missing_in_a


def validate_codebase_key_coverage(
    codebase_keys: Set[str],
    catalog: TranslationCatalog,
) -> Tuple[bool, Set[str]]:
    """
    Verify that every statically referenced translation key in the codebase exists in the catalog.
    Returns (is_complete, missing_keys).
    """
    cat_keys = catalog.keys()
    missing = codebase_keys - cat_keys
    return len(missing) == 0, missing
